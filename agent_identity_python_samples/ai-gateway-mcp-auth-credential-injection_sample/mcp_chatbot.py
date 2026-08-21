#!/usr/bin/env python3
"""
对话式 MCP Chatbot — LangChain + DashScope/Qwen + MCP (-32042 Elicitation)

功能：
1. 启动时连接 MCP Server，加载工具列表
2. 如果 list_tools 触发 -32042，展示授权链接，等待用户完成后回车继续
3. 对话过程中工具调用触发 -32042，自动展示授权链接
4. 使用 LangChain + create_react_agent 做对话
5. 交互式命令行聊天
6. 自动获取 Workload Access Token (WAT)，无需手动传入 bearer-token

用法：
    # 方式1：自动获取 WAT（推荐）
    export ALIBABA_CLOUD_ACCESS_KEY_ID=xxx
    export ALIBABA_CLOUD_ACCESS_KEY_SECRET=xxx
    export AGENT_IDENTITY_WORKLOAD_IDENTITY_NAME=workload-xxx
    python mcp_chatbot.py --api-key sk-xxx

    # 方式2：手动传入 bearer-token
    python mcp_chatbot.py \
        --mcp-url http://env-xxx.alicloudapi.com/mcp-servers/test-order-agent-identity \
        --bearer-token YOUR_TOKEN \
        --api-key sk-xxx

依赖安装：
    pip install "mcp>=1.2.0" langchain-core langchain-openai langgraph httpx
    pip install agent-identity-python-sdk  # 用于自动获取 WAT
"""

import argparse
import asyncio
import json
import logging
import os
import re
import sys
import uuid
import webbrowser
from dataclasses import dataclass, field
from typing import Any, Optional

import httpx

# MCP SDK imports
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from mcp.shared.exceptions import McpError

# LangChain imports
from langchain_core.tools import StructuredTool
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.outputs import ChatGeneration, ChatResult
from pydantic import ConfigDict, create_model

def _is_anyio_cancelled(exc: BaseException) -> bool:
    """检查异常是否为 anyio 的 CancelledError。"""
    try:
        import anyio
        return isinstance(exc, anyio.get_cancelled_exc_class())
    except Exception:
        return False


logger = logging.getLogger(__name__)

# ════════════════════════════════════════════════════════════
# 兼容非标准 OpenAI API 响应的 ChatModel
# ════════════════════════════════════════════════════════════


def _extract_json_objects(text: str) -> list[dict]:
    """从文本中提取所有包含 "name" 和 "arguments" 的 JSON 对象。

    使用 json.JSONDecoder.raw_decode() 正确处理嵌套花括号，
    而非正则表达式。
    """
    decoder = json.JSONDecoder()
    results = []
    i = 0
    while i < len(text):
        idx = text.find('{', i)
        if idx == -1:
            break
        try:
            obj, end = decoder.raw_decode(text, idx)
            if isinstance(obj, dict) and "name" in obj and "arguments" in obj:
                results.append(obj)
            i = end
        except json.JSONDecodeError:
            i = idx + 1
    return results


_TOOL_SYSTEM_SUFFIX = """

你可以使用以下工具来帮助用户完成任务。当你需要调用工具时，必须严格按照以下 JSON 格式输出（不要输出其他任何内容）：
{{"name": "工具名称", "arguments": {{"参数名": "参数值"}}}}
每次只调用一个工具。输出工具调用后，系统会执行工具并返回结果给你，你再基于结果回答用户。
可用工具列表：
{tool_descriptions}"""


class CompatibleChatOpenAI(BaseChatModel):
    """
    兼容非标准 OpenAI API 响应的 ChatModel。

    某些阿里云 MAAS 端点返回的响应格式与标准 OpenAI API 不同：
    - 标准格式: {{"choices": [{{"message": {{"content": "..."}}, ...}}]}}
    - 非标准格式: {{"text": "...", "finish_reason": "stop"}}

    本类通过 httpx 直接调用 API，自动检测并适配两种格式。
    对于不支持原生 function calling 的端点，使用文本解析方式实现工具调用。
    """

    model_name: str = "qwen-max"
    base_url: str = ""
    api_key: str = ""
    temperature: float = 0
    max_tokens: int = 4096
    request_timeout: float = 60.0

    # 内部状态
    _bound_tools: list[dict] = []
    _tool_schemas: list[dict] = []

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @property
    def _llm_type(self) -> str:
        return "compatible-chat-openai"

    @property
    def _identifying_params(self) -> dict:
        return {"model": self.model_name, "base_url": self.base_url}

    def bind_tools(self, tools: list, **kwargs) -> "CompatibleChatOpenAI":
        """绑定工具列表，返回新的模型实例。"""
        import copy
        new_model = copy.copy(self)
        new_model._tool_schemas = []
        new_model._bound_tools = []
        for t in tools:
            if hasattr(t, "get_input_schema") and callable(t.get_input_schema):
                # LangChain Tool → OpenAI tool schema
                schema = {
                    "type": "function",
                    "function": {
                        "name": t.name,
                        "description": t.description or "",
                        "parameters": t.args_schema.model_json_schema()
                        if hasattr(t, "args_schema") and t.args_schema
                        else {"type": "object", "properties": {}},
                    },
                }
            elif isinstance(t, dict):
                schema = t
            else:
                continue
            new_model._tool_schemas.append(schema)
            new_model._bound_tools.append(t)
        return new_model

    def _build_messages(
        self, messages: list[BaseMessage]
    ) -> list[dict]:
        """将 LangChain messages 转为 API 请求格式，必要时注入工具描述。"""
        api_msgs = []
        for m in messages:
            if isinstance(m, SystemMessage):
                content = m.content
                # 如果有绑定的工具，追加工具描述到 system prompt
                if self._tool_schemas:
                    descs = []
                    for s in self._tool_schemas:
                        fn = s.get("function", s)
                        descs.append(
                            f"- {fn['name']}: {fn.get('description', '')}"
                            f"  参数: {json.dumps(fn.get('parameters', {}), ensure_ascii=False)}"
                        )
                    content += _TOOL_SYSTEM_SUFFIX.format(
                        tool_descriptions="\n".join(descs)
                    )
                api_msgs.append({"role": "system", "content": content})
            elif isinstance(m, HumanMessage):
                api_msgs.append({"role": "user", "content": m.content})
            elif isinstance(m, AIMessage):
                # 如果有 tool_calls，将调用信息包含在 content 中以便 LLM 理解上下文
                if hasattr(m, "tool_calls") and m.tool_calls:
                    tc = m.tool_calls[0]
                    content = json.dumps(
                        {"name": tc["name"], "arguments": tc.get("args", {})},
                        ensure_ascii=False,
                    )
                    api_msgs.append({"role": "assistant", "content": f"```json\n{content}\n```"})
                else:
                    api_msgs.append({"role": "assistant", "content": m.content or ""})
            elif isinstance(m, ToolMessage):
                api_msgs.append({
                    "role": "user",
                    "content": f"[工具 {m.name} 返回结果]: {m.content}",
                })
            else:
                api_msgs.append({"role": "user", "content": str(m.content)})
        return api_msgs

    def _do_request(self, api_messages: list[dict]) -> dict:
        """发送 HTTP 请求并返回原始 JSON 响应。"""
        url = self.base_url.rstrip("/") + "/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        body: dict[str, Any] = {
            "model": self.model_name,
            "messages": api_messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        # 注意: 不发送 tools 参数，因为该 MAAS 端点不支持原生 function calling。
        # 工具调用通过 system prompt 中的文本指令 + 文本解析实现。

        response = httpx.post(
            url, headers=headers, json=body, timeout=self.request_timeout
        )
        if response.status_code != 200:
            # 调试信息仅在 MCP_DEBUG/--debug 开启时输出，且不包含任何凭据内容
            if DEBUG_ENABLED:
                print(f"{C_DIM}[DEBUG] LLM request URL: {url}{C_RESET}")
                print(f"{C_DIM}[DEBUG] LLM body keys: {list(body.keys())}, msg count: {len(api_messages)}{C_RESET}")
                print(f"{C_DIM}[DEBUG] LLM response status={response.status_code}, body={response.text[:300]}{C_RESET}")
        response.raise_for_status()
        return response.json()

    def _parse_tool_calls_from_text(self, text: str) -> list[dict] | None:
        """尝试从文本中解析工具调用（用于不支持原生 function calling 的端点）。

        使用 json.JSONDecoder.raw_decode() 提取 JSON 对象，
        正确处理嵌套花括号，不依赖正则。
        """
        logging.debug("[TOOL_PARSE] 尝试从文本解析工具调用, text=%r", text[:500])
        objs = _extract_json_objects(text)
        for obj in objs:
            name = obj.get("name")
            arguments = obj.get("arguments")
            if isinstance(name, str) and name and isinstance(arguments, dict):
                logging.debug("[TOOL_PARSE] 成功解析: name=%s, args=%s", name, arguments)
                return [{
                    "name": name,
                    "args": arguments,
                    "id": f"call_{uuid.uuid4().hex[:12]}",
                }]
        logging.debug("[TOOL_PARSE] 未找到工具调用")
        return None

    def _normalize_response(self, raw: dict) -> dict:
        """
        将非标准响应归一化为标准 OpenAI 格式。

        标准格式直接返回；非标准格式（顶层 text/finish_reason）
        转换为 {{"choices": [{{"message": {{"content": ..., "role": "assistant"}}}}]}}。
        """
        # 已经是标准格式
        if raw.get("choices") and isinstance(raw["choices"], list) and len(raw["choices"]) > 0:
            return raw

        # 非标准格式: 构造标准格式
        text = raw.get("text", "")
        finish_reason = raw.get("finish_reason", "stop")

        # 检查是否有 tool_calls（某些非标准端点可能在顶层返回）
        tool_calls_raw = raw.get("tool_calls")
        message: dict[str, Any] = {"role": "assistant", "content": text}
        if tool_calls_raw:
            message["tool_calls"] = tool_calls_raw
            message["content"] = None

        return {
            "id": raw.get("id", f"chatcmpl-{uuid.uuid4().hex[:12]}"),
            "choices": [{
                "message": message,
                "finish_reason": finish_reason,
                "index": 0,
            }],
            "model": raw.get("model", self.model_name),
            "object": "chat.completion",
            "usage": raw.get("usage", {}),
        }

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: Optional[list[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any,
    ) -> ChatResult:
        api_messages = self._build_messages(messages)
        logging.debug("[LLM] >>> API messages: %s", json.dumps(api_messages, ensure_ascii=False, indent=2))
        raw = self._do_request(api_messages)
        logging.debug("[LLM] <<< Raw response: %s", json.dumps(raw, ensure_ascii=False, indent=2))
        normalized = self._normalize_response(raw)

        choice = normalized["choices"][0]
        msg = choice["message"]
        content = msg.get("content") or ""
        finish_reason = choice.get("finish_reason", "stop")
        logging.debug("[LLM] content=%r, finish_reason=%s, has_tool_calls=%s",
                      content[:300] if content else "", finish_reason, bool(msg.get("tool_calls")))

        # 构建 AIMessage
        ai_kwargs: dict[str, Any] = {"finish_reason": finish_reason}

        # 优先检查原生 tool_calls（如果端点未来支持了 function calling）
        if msg.get("tool_calls"):
            tool_calls = []
            for tc in msg["tool_calls"]:
                fn = tc.get("function", tc)
                args = fn.get("arguments", "{}")
                if isinstance(args, str):
                    try:
                        args = json.loads(args)
                    except json.JSONDecodeError:
                        args = {}
                tool_calls.append({
                    "name": fn.get("name", ""),
                    "args": args,
                    "id": tc.get("id", f"call_{uuid.uuid4().hex[:12]}"),
                })
            ai_msg = AIMessage(
                content=content, tool_calls=tool_calls, additional_kwargs=ai_kwargs
            )
        elif self._tool_schemas and content:
            # 从文本中解析工具调用（文本模式 tool calling）
            parsed = self._parse_tool_calls_from_text(content)
            if parsed:
                logging.debug("[LLM] 解析到文本工具调用: %s", parsed)
                ai_msg = AIMessage(
                    content="", tool_calls=parsed, additional_kwargs=ai_kwargs
                )
            else:
                ai_msg = AIMessage(
                    content=content, additional_kwargs=ai_kwargs
                )
        else:
            ai_msg = AIMessage(content=content, additional_kwargs=ai_kwargs)

        return ChatResult(generations=[ChatGeneration(message=ai_msg)])

    def _stream(self, messages, stop=None, run_manager=None, **kwargs):
        # 简化实现：不支持流式，直接返回完整结果
        result = self._generate(messages, stop=stop, run_manager=run_manager, **kwargs)
        yield result.generations[0]


# ════════════════════════════════════════════════════════════
# 常量
# ════════════════════════════════════════════════════════════

URL_ELICITATION_REQUIRED = -32042

DEFAULT_MCP_URL = os.environ.get(
    "MCP_SERVER_URL", ""
)
DEFAULT_LLM_BASE_URL = os.environ.get(
    "LLM_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"
)
DEFAULT_LLM_MODEL = os.environ.get("LLM_MODEL", "qwen-max")

# ANSI 颜色
C_RESET = "\033[0m"
C_BOLD = "\033[1m"
C_RED = "\033[91m"
C_GREEN = "\033[92m"
C_YELLOW = "\033[93m"
C_BLUE = "\033[94m"
C_CYAN = "\033[96m"
C_DIM = "\033[2m"

# 调试开关：默认关闭。可通过 MCP_DEBUG 环境变量或 --debug 命令行参数开启。
# 注意：调试输出中绝不包含 key/secret/token 等凭据内容。
DEBUG_ENABLED = os.environ.get("MCP_DEBUG", "").strip().lower() in (
    "1", "true", "yes", "on",
)


def set_debug(enabled: bool) -> None:
    """启用/关闭调试输出（由 --debug 命令行参数调用）。"""
    global DEBUG_ENABLED
    DEBUG_ENABLED = bool(enabled)


# ════════════════════════════════════════════════════════════
# Workload Access Token (WAT) 自动获取
# ════════════════════════════════════════════════════════════

def get_workload_access_token(id_token: str | None = None, region: str | None = None) -> str | None:
    """
    获取 Workload Access Token (WAT)。

    三种模式：
    1. 提供 id_token → 用 id_token 换取 WAT
    2. 不提供 id_token，有 AK/SK → 用 AK/SK 获取 WAT
    3. 都不满足 → 返回 None

    读取以下环境变量：
    - AGENT_IDENTITY_WORKLOAD_IDENTITY_NAME: Workload Identity 名称
    - AGENT_IDENTITY_REGION_ID: 区域 ID（可选，默认根据模式决定）
    - ALIBABA_CLOUD_ACCESS_KEY_ID: 阿里云 AccessKey ID（模式2需要）
    - ALIBABA_CLOUD_ACCESS_KEY_SECRET: 阿里云 AccessKey Secret（模式2需要）

    Args:
        id_token: ID Token，用于换取 WAT
        region: 区域 ID，如不指定则从环境变量读取或使用默认值

    Returns:
        WAT token 字符串，获取失败时返回 None
    """
    workload_identity_name = os.environ.get("AGENT_IDENTITY_WORKLOAD_IDENTITY_NAME")
    if not workload_identity_name:
        print(f"{C_YELLOW}[WAT]{C_RESET} 未设置 AGENT_IDENTITY_WORKLOAD_IDENTITY_NAME，跳过自动获取")
        return None

    # 确定 region：优先使用参数，其次环境变量，最后根据模式使用默认值
    if not region:
        region = os.environ.get("AGENT_IDENTITY_REGION_ID")
    if not region:
        region = "cn-beijing"  # 统一默认 cn-beijing

    try:
        from agent_identity_python_sdk.core.identity import IdentityClient

        client = IdentityClient(region_id=region)

        if id_token:
            # 模式1：用 ID Token 换取 WAT
            print(f"{C_BLUE}[WAT]{C_RESET} 使用 ID Token 换取 Workload Access Token...")
            token = client.get_workload_access_token(
                workload_identity_name,
                user_token=id_token
            )
        else:
            # 模式2：用 AK/SK 获取 WAT
            ak = os.environ.get("ALIBABA_CLOUD_ACCESS_KEY_ID")
            sk = os.environ.get("ALIBABA_CLOUD_ACCESS_KEY_SECRET")
            if not ak or not sk:
                print(f"{C_YELLOW}[WAT]{C_RESET} 未设置 AK/SK，跳过自动获取")
                return None
            print(f"{C_BLUE}[WAT]{C_RESET} 使用 AK/SK 获取 Workload Access Token...")
            token = client.get_workload_access_token(workload_identity_name)

        if token:
            print(f"{C_GREEN}[WAT]{C_RESET} 成功获取 Workload Access Token")
            if DEBUG_ENABLED:
                print(f"  {C_DIM}Token 前缀: {token[:8]}...{C_RESET}")
            return token
        return None

    except ImportError as e:
        print(f"{C_YELLOW}[WAT]{C_RESET} SDK 未安装: {e}")
        return None
    except Exception as e:
        print(f"{C_RED}[WAT]{C_RESET} 获取 WAT 失败: {type(e).__name__}: {e}")
        if "EntityNotExists.WorkloadIdentity" in str(e):
            print(
                f"{C_YELLOW}[WAT]{C_RESET} 提示: SDK 默认凭据链可能解析到了其他阿里云账号，"
                "请确认 ALIBABA_CLOUD_ACCESS_KEY_ID/SECRET（或凭据 profile）与 Workload Identity 属于同一账号"
            )
        return None


# ════════════════════════════════════════════════════════════
# -32042 Elicitation 解析
# ════════════════════════════════════════════════════════════

@dataclass
class ElicitationInfo:
    """从 -32042 错误中提取的授权信息"""
    url: str
    message: str
    elicitation_id: str
    mode: str = "url"


def _extract_http_status_error(exc: BaseException) -> httpx.HTTPStatusError | None:
    """从异常（可能是 ExceptionGroup）中递归提取 HTTPStatusError。"""
    if isinstance(exc, httpx.HTTPStatusError):
        return exc
    if hasattr(exc, 'exceptions'):
        for sub_exc in exc.exceptions:
            found = _extract_http_status_error(sub_exc)
            if found is not None:
                return found
    return None


def _http_error_message(status_code: int) -> str:
    """根据 HTTP 状态码返回友好的错误消息。"""
    if status_code == 403:
        return "权限不足（403 Forbidden）：Cedar 策略拒绝了该操作，请联系管理员配置访问权限。"
    elif status_code == 401:
        return "认证失败（401 Unauthorized）：请检查 bearer token 是否有效。"
    elif 400 <= status_code < 500:
        return f"客户端错误（{status_code}）：请求被服务器拒绝，请检查请求参数。"
    else:
        return f"服务器错误（{status_code}）：MCP 服务器暂时不可用，请稍后重试。"


def parse_elicitation_error(error: McpError) -> list[ElicitationInfo]:
    """从 McpError 中解析 -32042 URL elicitation 数据。"""
    if not hasattr(error, "error") or error.error is None:
        return []

    error_data = error.error
    if not hasattr(error_data, "code") or error_data.code != URL_ELICITATION_REQUIRED:
        return []

    data = getattr(error_data, "data", None)
    if not isinstance(data, dict):
        return []

    elicitations_raw = data.get("elicitations", [])
    results = []
    for item in elicitations_raw:
        if isinstance(item, dict):
            results.append(ElicitationInfo(
                url=item.get("url", ""),
                message=item.get("message", ""),
                elicitation_id=item.get("elicitationId", ""),
                mode=item.get("mode", "url"),
            ))
    return results


def parse_elicitation_from_text(text: str) -> list[ElicitationInfo]:
    """尝试从错误文本中解析 -32042 JSON。"""
    try:
        data = json.loads(text)
        if isinstance(data, dict) and data.get("code") == URL_ELICITATION_REQUIRED:
            elicitations_raw = data.get("data", {}).get("elicitations", [])
            return [
                ElicitationInfo(
                    url=item.get("url", ""),
                    message=item.get("message", ""),
                    elicitation_id=item.get("elicitationId", ""),
                    mode=item.get("mode", "url"),
                )
                for item in elicitations_raw if isinstance(item, dict)
            ]
    except (json.JSONDecodeError, AttributeError, TypeError):
        pass
    return []


def display_elicitation(elic: ElicitationInfo):
    """友好展示授权信息，并尝试打开浏览器。"""
    print(f"\n{C_YELLOW}{'━' * 60}{C_RESET}")
    print(f"{C_YELLOW}  ⚠  需要 OAuth2 授权{C_RESET}")
    print(f"{C_YELLOW}{'━' * 60}{C_RESET}")
    print(f"  {C_BOLD}消息:{C_RESET} {elic.message}")
    print(f"  {C_BOLD}URL: {C_RESET} {C_CYAN}{elic.url}{C_RESET}")
    if elic.elicitation_id:
        print(f"  {C_DIM}ID:  {elic.elicitation_id}{C_RESET}")
    print(f"{C_YELLOW}{'━' * 60}{C_RESET}")

    try:
        webbrowser.open(elic.url)
        print(f"  {C_GREEN}已在浏览器中打开授权页面{C_RESET}")
    except Exception:
        print(f"  {C_RED}无法自动打开浏览器，请手动复制上方 URL 访问{C_RESET}")


# ════════════════════════════════════════════════════════════
# MCP Chatbot
# ════════════════════════════════════════════════════════════

class MCPChatbot:
    def __init__(
        self,
        mcp_url: str,
        bearer_token: str,
        llm_api_key: str,
        llm_base_url: str = DEFAULT_LLM_BASE_URL,
        llm_model: str = DEFAULT_LLM_MODEL,
    ):
        self.mcp_url = mcp_url
        self.bearer_token = bearer_token
        self.llm_api_key = llm_api_key
        self.llm_base_url = llm_base_url
        self.llm_model = llm_model

        self.headers: dict[str, str] = {}
        if bearer_token:
            self.headers["Authorization"] = f"Bearer {bearer_token}"

        self.mcp_tools: list[Any] = []   # MCP Tool 定义
        self.lc_tools: list[Any] = []    # LangChain StructuredTool
        self.agent: Any = None
        self.agent_config: dict[str, Any] = {}

        # 在 run() 中设置
        self.session: ClientSession | None = None

        # 连续 403 计数器：防止 LLM 无限重试被 Cedar 拒绝的操作
        self._consecutive_403_count = 0
        self._connection_broken = False  # 标记 MCP 连接是否已断裂
        self.session_broken = False      # 标记 MCP session 是否因 CancelledError 而不可用

    # ────────────────────────────────────────────────────────
    # 初始化
    # ────────────────────────────────────────────────────────

    async def initialize(self):
        """连接 MCP server，加载工具列表，处理 -32042。"""
        print(f"\n{C_BLUE}[连接]{C_RESET} {self.mcp_url}")
        print(f"{C_BLUE}[认证]{C_RESET} Bearer token: {'已配置' if self.headers.get('Authorization') else '未配置'}")

        result = await self._load_tools_with_elicitation()
        if result is None:
            # 用户取消了授权，直接退出
            return
        if not result:
            # 授权链接已展示但工具未加载，抛出异常让 _connect_and_run 重连
            raise ConnectionError("工具未加载，需要重新建立连接")
        self._build_agent()

    async def _load_tools_with_elicitation(self) -> bool | None:
        """尝试 list_tools，如果遇到 -32042 则展示授权链接并等待。

        Returns:
            True: 工具加载成功
            False: 需要重新连接（elicitation 已展示）
            None: 用户取消了授权
        """
        max_retries = 3
        for attempt in range(1, max_retries + 1):
            try:
                tools_result = await self.session.list_tools()
                self.mcp_tools = tools_result.tools
                print(f"\n{C_GREEN}[工具]{C_RESET} 已加载 {len(self.mcp_tools)} 个 MCP 工具：")
                for t in self.mcp_tools:
                    print(f"  {C_BOLD}•{C_RESET} {t.name}: {t.description or '(无描述)'}")
                self._wrap_tools()
                return True
            except McpError as e:
                elicitations = parse_elicitation_error(e)
                if elicitations:
                    print(f"\n{C_YELLOW}[授权]{C_RESET} MCP Server 需要 OAuth2 授权 (尝试 {attempt}/{max_retries})")
                    for elic in elicitations:
                        display_elicitation(elic)
                    try:
                        input(f"\n{C_CYAN}请在浏览器中完成授权后按回车继续...{C_RESET}")
                    except (EOFError, KeyboardInterrupt):
                        print(f"\n{C_DIM}再见！{C_RESET}")
                        return None
                    # session 可能因错误而不可用，break 让 _connect_and_run 重连
                    break
                else:
                    print(f"{C_RED}[错误]{C_RESET} MCP 错误: {e}")
                    raise
            except BaseException as e:
                # 处理 ExceptionGroup 包装的 McpError（如 -32042）
                mcp_err_found = False
                if hasattr(e, 'exceptions'):
                    for sub_exc in e.exceptions:
                        if isinstance(sub_exc, McpError):
                            elicitations = parse_elicitation_error(sub_exc)
                            if elicitations:
                                print(f"\n{C_YELLOW}[授权]{C_RESET} MCP Server 需要 OAuth2 授权 (尝试 {attempt}/{max_retries})")
                                for elic in elicitations:
                                    display_elicitation(elic)
                                try:
                                    input(f"\n{C_CYAN}请在浏览器中完成授权后按回车继续...{C_RESET}")
                                except (EOFError, KeyboardInterrupt):
                                    print(f"\n{C_DIM}再见！{C_RESET}")
                                    return None
                                mcp_err_found = True
                                break
                if mcp_err_found:
                    # session 已损坏，break 让 _connect_and_run 重新建立连接
                    break
                # 非 -32042 的 BaseException，冒泡给外层
                print(f"{C_RED}[错误]{C_RESET} {type(e).__name__}: {e}")
                raise

        # 重试耗尽或 elicitation 后 break，交还给 _connect_and_run 重连
        return False

    # ────────────────────────────────────────────────────────
    # MCP → LangChain 工具转换
    # ────────────────────────────────────────────────────────

    def _wrap_tools(self):
        """将 MCP 工具列表转换为 LangChain StructuredTool 列表。"""
        self.lc_tools = []
        for mcp_tool in self.mcp_tools:
            lc_tool = self._make_lc_tool(mcp_tool)
            self.lc_tools.append(lc_tool)

    def _make_lc_tool(self, mcp_tool):
        """为单个 MCP 工具创建 LangChain StructuredTool。

        从 MCP tool 的 inputSchema 动态创建 Pydantic model 作为 args_schema，
        避免 **kwargs 导致 schema 中出现 kwargs 参数误导 LLM。
        """
        tool_name = mcp_tool.name
        tool_desc = mcp_tool.description or f"MCP tool: {tool_name}"
        input_schema = getattr(mcp_tool, "inputSchema", None) or {}

        # 从 MCP tool 的 inputSchema 动态创建 Pydantic model
        args_schema = None
        properties = input_schema.get("properties", {})
        if properties:
            type_map = {
                "string": str, "integer": int, "number": float,
                "boolean": bool, "array": list, "object": dict,
            }
            required_set = set(input_schema.get("required", []))
            fields = {}
            for prop_name, prop_info in properties.items():
                prop_type = prop_info.get("type", "string")
                py_type = type_map.get(prop_type, str)
                if prop_name in required_set:
                    fields[prop_name] = (py_type, ...)
                else:
                    fields[prop_name] = (Optional[py_type], None)
            args_schema = create_model(f"{tool_name}_Schema", **fields)

        async def _call_tool(**kwargs):
            return await self._call_mcp_tool(tool_name, kwargs)

        tool_kwargs = {
            "coroutine": _call_tool,
            "name": tool_name,
            "description": tool_desc,
        }
        if args_schema:
            tool_kwargs["args_schema"] = args_schema

        return StructuredTool.from_function(**tool_kwargs)

    async def _call_mcp_tool(self, tool_name: str, tool_args: dict) -> str:
        """调用 MCP 工具，处理 -32042 elicitation。返回字符串结果给 LLM。"""
        # 过滤掉 None 值参数，避免 MCP server 校验失败
        tool_args = {k: v for k, v in tool_args.items() if v is not None}
        print(f"\n{C_DIM}[MCP] 调用 {tool_name}({json.dumps(tool_args, ensure_ascii=False)}){C_RESET}")
        try:
            from datetime import timedelta
            result = await self.session.call_tool(
                tool_name, tool_args, read_timeout_seconds=timedelta(seconds=120)
            )

            # 检查 isError
            if result.isError:
                error_text = result.content[0].text if result.content else "Unknown error"
                elicitations = parse_elicitation_from_text(error_text)
                if elicitations:
                    return await self._handle_elicitation_in_chat(elicitations, tool_name, tool_args)
                return f"工具 {tool_name} 返回错误（请根据错误信息调整参数后重试，不要使用相同的参数重复调用）: {error_text}"

            # 正常结果
            texts = []
            for content in result.content:
                if hasattr(content, "text"):
                    texts.append(content.text)
            output = "\n".join(texts) if texts else "(空结果)"
            print(f"{C_GREEN}[MCP] 成功{C_RESET}")
            return output

        except McpError as e:
            elicitations = parse_elicitation_error(e)
            if elicitations:
                return await self._handle_elicitation_in_chat(elicitations, tool_name, tool_args)
            return f"工具 {tool_name} 调用失败（不可重试的错误）: {e}。请直接告诉用户操作失败，不要重试调用该工具。"
        except Exception as e:
            # 检查是否是 ExceptionGroup 中包含 HTTPStatusError（如 403 Forbidden）
            http_err = _extract_http_status_error(e)
            if http_err is not None:
                status = http_err.response.status_code
                if DEBUG_ENABLED:
                    print(f"{C_DIM}[DEBUG] _call_mcp_tool caught HTTP {status} for {tool_name}{C_RESET}")
                if status == 403:
                    self._consecutive_403_count += 1
                    msg = f"工具 {tool_name} 调用被拒绝（403 Forbidden）：当前策略不允许执行该操作。请告知用户没有权限执行此操作，不要重试。"
                else:
                    msg = f"工具 {tool_name} 调用失败（HTTP {status}）：{_http_error_message(status)}。请告知用户操作失败，不要重试。"
                print(f"{C_RED}[MCP] {msg}{C_RESET}")
                return msg
            return f"工具 {tool_name} 发生异常（不可重试）: {type(e).__name__}: {e}。请直接告诉用户操作失败，不要重试调用该工具。"
        except BaseException as e:
            # CancelledError 静默处理：不打印堆栈，直接返回友好消息
            if isinstance(e, asyncio.CancelledError) or _is_anyio_cancelled(e):
                logger.debug("MCP tool %s cancelled", tool_name)
                # 标记 session 损坏，通知 while 循环触发重连（而非仅 reset agent 状态）
                self.session_broken = True
                return f"工具 {tool_name} 调用被取消（连接超时或中断），请告知用户操作未完成，不要重试。"
            # ExceptionGroup（Python 3.11+ 中不继承 Exception）：提取 HTTP 错误
            http_err = _extract_http_status_error(e)
            if http_err is not None:
                status = http_err.response.status_code
                if status == 403:
                    self._consecutive_403_count += 1
                    msg = f"工具 {tool_name} 调用被拒绝（403 Forbidden）：当前策略不允许执行该操作。请告知用户没有权限执行此操作，不要重试。"
                else:
                    msg = f"工具 {tool_name} 调用失败（HTTP {status}）：{_http_error_message(status)}。请告知用户操作失败，不要重试。"
                print(f"{C_RED}[MCP] {msg}{C_RESET}")
                return msg
            # _call_mcp_tool 必须始终返回字符串，绝不抛出异常
            logger.warning('_call_mcp_tool unhandled BaseException: %s: %s', type(e).__name__, e)
            self.session_broken = True
            print(f"{C_RED}[MCP] 工具 {tool_name} 发生严重异常: {type(e).__name__}: {e}{C_RESET}")
            return f"工具 {tool_name} 发生严重异常（{type(e).__name__}）：请直接告诉用户操作失败，不要重试调用该工具。"

    def _reset_agent_state(self):
        """重置 Agent 状态，用于从 CancelledError / session 异常中恢复。"""
        self.agent_config = {
            "configurable": {
                "thread_id": f"chat-session-{uuid.uuid4().hex[:8]}"
            },
            "recursion_limit": 10,
        }
        self.session_broken = False
        logger.debug("Agent state reset (new thread_id)")

    def _is_session_alive(self) -> bool:
        """检查 MCP session 和底层传输是否仍然可用。"""
        session = self.session
        if session is None:
            return False
        try:
            # 检查 anyio MemoryObjectReceiveStream 是否已关闭
            recv_stream = getattr(session, '_receive_stream', None)
            if recv_stream is not None and getattr(recv_stream, '_closed', False):
                return False
            # 检查 httpx client 是否已关闭
            http_client = getattr(session, '_http_client', None)
            if http_client is not None and getattr(http_client, 'is_closed', False):
                return False
            return True
        except Exception:
            return False

    async def _handle_elicitation_in_chat(
        self, elicitations: list[ElicitationInfo], tool_name: str, tool_args: dict
    ) -> str:
        """对话中的 -32042 处理：展示授权链接给用户，返回提示信息给 LLM。"""
        for elic in elicitations:
            display_elicitation(elic)

        urls = [e.url for e in elicitations]
        msg = (
            f"工具 {tool_name} 需要 OAuth2 授权。"
            f"授权链接已展示给用户，请等待用户在浏览器中完成授权。"
            f"授权 URL: {', '.join(urls)}"
        )
        print(f"{C_YELLOW}[提示]{C_RESET} 授权链接已展示给用户")
        return msg

    # ────────────────────────────────────────────────────────
    # LangChain Agent 构建
    # ────────────────────────────────────────────────────────

    def _build_agent(self):
        """构建 LangChain ReAct Agent。"""
        import warnings
        from langgraph.prebuilt import create_react_agent

        # 使用 CompatibleChatOpenAI 以兼容非标准 MAAS 响应格式
        llm = CompatibleChatOpenAI(
            model_name=self.llm_model,
            base_url=self.llm_base_url,
            api_key=self.llm_api_key,
            temperature=0,
        )

        system_prompt = (
            "你是一个智能助手，可以通过 MCP 工具帮助用户完成各种任务。\n"
            "当工具返回需要 OAuth2 授权的消息时，请告诉用户需要在浏览器中完成授权，"
            "然后等待用户确认后再重试。\n"
            "请用中文回答。"
        )

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            self.agent = create_react_agent(
                llm,
                self.lc_tools,
                prompt=system_prompt,
            )
        self.agent_config = {"configurable": {"thread_id": "chat-session"}, "recursion_limit": 10}

        print(f"\n{C_GREEN}[Agent]{C_RESET} LangChain ReAct Agent 已就绪")
        print(f"  LLM: {C_BOLD}{self.llm_model}{C_RESET} @ {self.llm_base_url}")
        print(f"  工具: {len(self.lc_tools)} 个")

    # ────────────────────────────────────────────────────────
    # 对话
    # ────────────────────────────────────────────────────────

    _MAX_CONSECUTIVE_403 = 3  # 连续 403 次数阈值，超过则强制中断对话

    async def chat(self, user_input: str) -> str:
        """处理用户消息，通过 Agent 返回回复。"""
        try:
            result = await self.agent.ainvoke(
                {"messages": [HumanMessage(content=user_input)]},
                config=self.agent_config,
            )

            # 提取最后一条 AI 消息
            messages = result.get("messages", [])
            for msg in reversed(messages):
                if hasattr(msg, "content") and msg.content and msg.type == "ai":
                    response = msg.content
                    print(f"\n{C_GREEN}{C_BOLD}助手:{C_RESET} {response}")
                    return response

            print(f"\n{C_DIM}(无回复){C_RESET}")
            return ""

        except Exception as e:
            # 检查是否是 ExceptionGroup 中包含 HTTPStatusError
            http_err = _extract_http_status_error(e)
            if http_err is not None:
                status = http_err.response.status_code
                if status == 403:
                    self._consecutive_403_count += 1
                    if self._consecutive_403_count >= self._MAX_CONSECUTIVE_403:
                        print(f"\n{C_RED}[错误]{C_RESET} 连续 {self._consecutive_403_count} 次工具调用被 Cedar 策略拒绝（403 Forbidden），强制中断当前对话。")
                        print(f"  请联系管理员调整访问权限后重试。")
                        self._consecutive_403_count = 0
                        self._reset_agent_state()
                        return "由于权限不足，当前对话已被中断。请联系管理员配置 Cedar 策略后再试。"
                    print(f"{C_RED}[错误]{C_RESET} 工具调用被拒绝（403 Forbidden），连续第 {self._consecutive_403_count} 次")
                    return f"操作被拒绝（403 Forbidden）：Cedar 策略不允许执行。请告知用户没有权限，不要重试该操作。"
                else:
                    print(f"{C_RED}[错误]{C_RESET} HTTP 错误（{status}）：{_http_error_message(status)}")
                    if DEBUG_ENABLED:
                        # 调试：显示请求 URL，确认错误来源（不含任何凭据）
                        if hasattr(http_err, 'request') and http_err.request is not None:
                            print(f"{C_DIM}[DEBUG] 请求 URL: {http_err.request.url}{C_RESET}")
                        print(f"{C_DIM}[DEBUG] chat() caught HTTP {status}, exception type: {type(e).__name__}{C_RESET}")
                    self._reset_agent_state()
                    return f"操作失败（HTTP {status}）：{_http_error_message(status)}"
            error_msg = f"{C_RED}[错误]{C_RESET} {type(e).__name__}: {e}"
            logger.warning('chat() unhandled Exception: %s: %s', type(e).__name__, e)
            print(error_msg)
            self._reset_agent_state()
            return f"Error: {e}"
        except BaseException as e:
            # CancelledError 静默处理
            if isinstance(e, asyncio.CancelledError) or _is_anyio_cancelled(e):
                logger.debug("chat() cancelled")
                self._reset_agent_state()
                return "操作被取消（连接超时或中断），Agent 状态已重置。请重新输入您的问题。"
            # 兜底：捕获 ExceptionGroup（Python 3.11+ 不继承 Exception）等
            http_err = _extract_http_status_error(e)
            if http_err is not None:
                status = http_err.response.status_code
                if status == 403:
                    self._consecutive_403_count += 1
                    if self._consecutive_403_count >= self._MAX_CONSECUTIVE_403:
                        print(f"\n{C_RED}[错误]{C_RESET} 连续 {self._consecutive_403_count} 次工具调用被 Cedar 策略拒绝（403 Forbidden），强制中断当前对话。")
                        print(f"  请联系管理员调整访问权限后重试。")
                        self._consecutive_403_count = 0
                        return "由于权限不足，当前对话已被中断。请联系管理员配置 Cedar 策略后再试。"
                    print(f"{C_RED}[错误]{C_RESET} 工具调用被拒绝（403 Forbidden），连续第 {self._consecutive_403_count} 次")
                    return f"操作被拒绝（403 Forbidden）：Cedar 策略不允许执行。请告知用户没有权限，不要重试该操作。"
                else:
                    print(f"{C_RED}[错误]{C_RESET} HTTP 错误（{status}）：{_http_error_message(status)}")
                    return f"操作失败（HTTP {status}）：{_http_error_message(status)}"
            # chat() 必须始终返回字符串，绝不向 while 循环抛出异常
            logger.warning('chat() unhandled BaseException: %s: %s', type(e).__name__, e)
            print(f"{C_RED}[错误]{C_RESET} {type(e).__name__}: {e}")
            self._reset_agent_state()
            return f"操作失败（{type(e).__name__}）：Agent 状态已重置。请重新输入您的问题。"

    # ────────────────────────────────────────────────────────
    # 主循环
    # ────────────────────────────────────────────────────────

    async def run(self):
        """主循环：保持 MCP session，初始化 + 交互式对话。"""
        print(f"\n{C_BOLD}{'═' * 60}{C_RESET}")
        print(f"{C_BOLD}  MCP Chatbot — LangChain + DashScope/Qwen{C_RESET}")
        print(f"{C_BOLD}{'═' * 60}{C_RESET}")

        await self._connect_and_run()

    async def _connect_and_run(self):
        """建立 MCP 连接、初始化 session（含 -32042 elicitation 重试），然后进入主循环。"""
        max_retries = 3
        for attempt in range(1, max_retries + 1):
            try:
                async with streamablehttp_client(
                    self.mcp_url,
                    headers=self.headers,
                    timeout=120,
                    sse_read_timeout=600,
                ) as (read, write, _):
                    async with ClientSession(read, write) as session:
                        # 在 async with 内部捕获，避免 anyio ExceptionGroup 包装
                        try:
                            await session.initialize()
                        except McpError as e:
                            elicitations = parse_elicitation_error(e)
                            if elicitations:
                                print(f"\n{C_YELLOW}[授权]{C_RESET} MCP Server 在初始化阶段需要 OAuth2 授权 (尝试 {attempt}/{max_retries})")
                                for elic in elicitations:
                                    display_elicitation(elic)
                                try:
                                    input(f"\n{C_CYAN}请在浏览器中完成授权后按回车继续...{C_RESET}")
                                except (EOFError, KeyboardInterrupt):
                                    print(f"\n{C_DIM}再见！{C_RESET}")
                                    return
                                continue  # 重试循环，重新建立连接
                            raise

                        self.session = session
                        print(f"{C_GREEN}[连接]{C_RESET} MCP 连接已建立")

                        await self.initialize()

                        print(f"\n{C_CYAN}{'─' * 60}{C_RESET}")
                        print(f"  {C_BOLD}开始对话{C_RESET}  输入 {C_CYAN}quit{C_RESET}/{C_CYAN}exit{C_RESET}/{C_CYAN}q{C_RESET} 退出")
                        print(f"{C_CYAN}{'─' * 60}{C_RESET}")

                        while True:
                            try:
                                user_input = input(f"\n{C_BOLD}{C_BLUE}你:{C_RESET} ").strip()
                            except (EOFError, KeyboardInterrupt):
                                print(f"\n{C_DIM}再见！{C_RESET}")
                                break

                            if not user_input:
                                continue
                            if user_input.lower() in ("quit", "exit", "q"):
                                print(f"{C_DIM}再见！{C_RESET}")
                                break

                            if self.session_broken:
                                if not self._is_session_alive():
                                    print(f"{C_YELLOW}[连接]{C_RESET} MCP session 已损坏，正在重新连接...")
                                    self._reset_agent_state()
                                    break
                                # session 仍存活但标记为 broken（可能是临时 cancel），仅 reset 状态
                                print(f"{C_YELLOW}[提示]{C_RESET} 上次操作导致 session 异常，正在重置 Agent 状态...")
                                self._reset_agent_state()

                            try:
                                # 用独立 task + wait_for，确保超时能真正中断卡死的 agent
                                chat_task = asyncio.ensure_future(self.chat(user_input))
                                try:
                                    await asyncio.wait_for(
                                        asyncio.shield(chat_task), timeout=180
                                    )
                                except asyncio.TimeoutError:
                                    chat_task.cancel()
                                    try:
                                        await chat_task
                                    except BaseException:
                                        pass
                                    print(f"{C_RED}[超时]{C_RESET} 响应超时（180秒），请重试")
                                    if self.session_broken or not self._is_session_alive():
                                        print(f"{C_YELLOW}[连接]{C_RESET} MCP session 已损坏，正在重新连接...")
                                        break
                                    self._reset_agent_state()
                                except asyncio.CancelledError:
                                    # 外部取消（如 Ctrl+C），不吞掉，向上冒泡
                                    chat_task.cancel()
                                    try:
                                        await chat_task
                                    except BaseException:
                                        pass
                                    raise
                            except asyncio.CancelledError:
                                # 外部取消，重新抛出，让 _connect_and_run 退出
                                raise
                            except BaseException as e:
                                # CancelledError 静默处理，不打印堆栈
                                if isinstance(e, asyncio.CancelledError) or _is_anyio_cancelled(e):
                                    logger.debug("chat loop cancelled")
                                    print(f"{C_YELLOW}[提示]{C_RESET} 操作被取消，Agent 状态已重置，请重试。")
                                    self._reset_agent_state()
                                    if self.session_broken or not self._is_session_alive():
                                        print(f"{C_YELLOW}[连接]{C_RESET} MCP session 已损坏，正在重新连接...")
                                        break
                                    continue
                                # 安全网：防止 ExceptionGroup 从 chat() 逃逸出 while 循环
                                http_err = _extract_http_status_error(e)
                                if http_err is not None:
                                    status = http_err.response.status_code
                                    if status == 403:
                                        self._consecutive_403_count += 1
                                        if self._consecutive_403_count >= self._MAX_CONSECUTIVE_403:
                                            print(f"\n{C_RED}[错误]{C_RESET} 连续 {self._consecutive_403_count} 次被 Cedar 策略拒绝（403），强制中断对话。")
                                            self._consecutive_403_count = 0
                                            break
                                        print(f"{C_YELLOW}[警告]{C_RESET} 工具调用被拒绝（403），连接可能不稳定")
                                    else:
                                        print(f"{C_YELLOW}[警告]{C_RESET} HTTP 错误（{status}），连接可能不稳定")
                                else:
                                    print(f"{C_YELLOW}[警告]{C_RESET} {type(e).__name__}: {e}")

                                # 检查连接是否还存活，不存活则 break 触发重连
                                if not self._is_session_alive():
                                    print(f"{C_YELLOW}[连接]{C_RESET} MCP 连接已断开，正在尝试重新连接...")
                                    break
                return  # 正常退出
            except McpError as e:
                # 兜底：捕获未被内部处理的 McpError
                elicitations = parse_elicitation_error(e)
                if elicitations:
                    print(f"\n{C_YELLOW}[授权]{C_RESET} MCP Server 需要 OAuth2 授权 (尝试 {attempt}/{max_retries})")
                    for elic in elicitations:
                        display_elicitation(elic)
                    input(f"\n{C_CYAN}请在浏览器中完成授权后按回车继续...{C_RESET}")
                else:
                    print(f"{C_RED}[错误]{C_RESET} MCP 错误: {e}")
                    raise
            except ConnectionError:
                # initialize() 抛出 ConnectionError 表示 elicitation 已展示，需要重连
                print(f"{C_YELLOW}[重连]{C_RESET} 授权已完成，正在重新建立连接 (尝试 {attempt}/{max_retries})")
                continue
            except BaseException as e:
                # 兆底：处理 anyio ExceptionGroup 包装的情况
                if hasattr(e, 'exceptions'):
                    handled = False
                    for sub_exc in e.exceptions:
                        if isinstance(sub_exc, McpError):
                            elicitations = parse_elicitation_error(sub_exc)
                            if elicitations:
                                print(f"\n{C_YELLOW}[授权]{C_RESET} MCP Server 需要 OAuth2 授权 (尝试 {attempt}/{max_retries})")
                                for elic in elicitations:
                                    display_elicitation(elic)
                                try:
                                    input(f"\n{C_CYAN}请在浏览器中完成授权后按回车继续...{C_RESET}")
                                except (EOFError, KeyboardInterrupt):
                                    print(f"\n{C_DIM}再见！{C_RESET}")
                                    return
                                handled = True
                                break
                        elif isinstance(sub_exc, httpx.HTTPStatusError) and sub_exc.response.status_code == 401:
                            print(f"\n{C_YELLOW}[认证]{C_RESET} MCP Server 返回 401 Unauthorized，需要认证")
                            print(f"  请通过以下方式之一提供 bearer token：")
                            print(f"  1. --bearer-token 参数")
                            print(f"  2. MCP_BEARER_TOKEN 环境变量")
                            print(f"  3. 配置 AK/SK/Workload 环境变量以自动获取 WAT")
                            return
                    if not handled:
                        # 检查是否包含 HTTPStatusError（如 403 Cedar 策略拒绝）
                        http_err = _extract_http_status_error(e)
                        if http_err is not None:
                            status = http_err.response.status_code
                            if status == 403:
                                self._consecutive_403_count += 1
                                if self._consecutive_403_count >= self._MAX_CONSECUTIVE_403:
                                    print(f"\n{C_RED}[错误]{C_RESET} 连续 {self._consecutive_403_count} 次被 Cedar 策略拒绝（403），停止重试。")
                                    print(f"  请联系管理员配置访问权限。")
                                    return
                                print(f"\n{C_YELLOW}[重连]{C_RESET} Cedar 策略拒绝（403），尝试重新建立连接 (尝试 {attempt}/{max_retries})")
                            else:
                                print(f"\n{C_YELLOW}[重连]{C_RESET} HTTP 错误（{status}），尝试重新建立连接 (尝试 {attempt}/{max_retries})")
                            # continue → 重试循环，重新建立连接
                        else:
                            # 没有找到可处理的异常
                            print(f"{C_RED}[错误]{C_RESET} {type(e).__name__}: {e}")
                            raise
                    continue  # 重试循环
                print(f"{C_RED}[错误]{C_RESET} {type(e).__name__}: {e}")
                raise

        print(f"{C_RED}[失败]{C_RESET} 多次尝试后仍无法建立 MCP 连接，请检查授权状态。")
        sys.exit(1)


# ════════════════════════════════════════════════════════════
# 命令行入口
# ════════════════════════════════════════════════════════════

def parse_args():
    parser = argparse.ArgumentParser(
        description="对话式 MCP Chatbot — LangChain + DashScope/Qwen + MCP",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python %(prog)s \\
      --bearer-token YOUR_TOKEN \\
      --api-key sk-xxx

  # 使用环境变量:
  export MCP_BEARER_TOKEN=YOUR_TOKEN
  export LLM_API_KEY=sk-xxx
  python %(prog)s
        """,
    )
    parser.add_argument(
        "--mcp-url",
        default=DEFAULT_MCP_URL,
        help=f"MCP 服务器 URL（默认: {DEFAULT_MCP_URL}）",
    )
    parser.add_argument(
        "--bearer-token",
        default=os.environ.get("MCP_BEARER_TOKEN", ""),
        help="Bearer token（或 MCP_BEARER_TOKEN 环境变量）。如不指定，将自动尝试获取 WAT",
    )
    parser.add_argument(
        "--api-key",
        default=os.environ.get("LLM_API_KEY", ""),
        help="LLM API Key（或 LLM_API_KEY 环境变量）",
    )
    parser.add_argument(
        "--base-url",
        default=DEFAULT_LLM_BASE_URL,
        help=f"LLM Base URL（默认: {DEFAULT_LLM_BASE_URL}）",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_LLM_MODEL,
        help=f"LLM 模型名（默认: {DEFAULT_LLM_MODEL}）",
    )
    parser.add_argument(
        "--region",
        default=None,
        help="Region ID（可选，默认 cn-beijing，可用 AGENT_IDENTITY_REGION_ID 环境变量覆盖）",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="开启调试输出（也可通过 MCP_DEBUG=1 环境变量开启，默认关闭）",
    )
    return parser.parse_args()


async def async_main():
    args = parse_args()
    if args.debug:
        set_debug(True)

    bearer_token = None

    if args.bearer_token:
        # 有 ID Token → 用它换取 WAT
        print(f"{C_BLUE}[认证]{C_RESET} 检测到 ID Token，尝试换取 Workload Access Token...")
        bearer_token = get_workload_access_token(id_token=args.bearer_token, region=args.region)
    else:
        # 没有 ID Token → 尝试用 AK/SK 获取 WAT
        print(f"{C_BLUE}[认证]{C_RESET} 未提供 --bearer-token，尝试自动获取 WAT...")
        bearer_token = get_workload_access_token(region=args.region)

    if not bearer_token:
        # 无法获取 token，但仍可启动（MCP 可能会触发 -32042 授权流程）
        print(f"{C_YELLOW}[认证]{C_RESET} 无法获取 WAT，将尝试无认证连接...")

    if not args.api_key:
        print(f"{C_RED}[错误]{C_RESET} 请提供 --api-key 或设置 LLM_API_KEY 环境变量")
        sys.exit(1)

    if bearer_token and DEBUG_ENABLED:
        # 仅在调试模式下显示 token 类型与收窄前缀（前 8 字符），帮助确认是 WAT 而非 ID Token
        token_type = "WAT" if bearer_token.startswith("eyJjdHkiOiJKV1QiLCJ") else "JWT/ID Token"
        print(f"{C_DIM}[认证] Token 类型: {token_type}, 前缀: {bearer_token[:8]}...{C_RESET}")

    chatbot = MCPChatbot(
        mcp_url=args.mcp_url,
        bearer_token=bearer_token,
        llm_api_key=args.api_key,
        llm_base_url=args.base_url,
        llm_model=args.model,
    )

    try:
        await chatbot.run()
    except BaseException as e:
        # 顶层兜底：防止未捕获的 ExceptionGroup 中包含 HTTPStatusError 时打印丑陋堆栈
        http_err = _extract_http_status_error(e)
        if http_err is not None:
            status = http_err.response.status_code
            if status == 403:
                print(f"\n{C_RED}[错误]{C_RESET} Cedar 策略拒绝（403 Forbidden）：程序已安全退出。")
            else:
                print(f"\n{C_RED}[错误]{C_RESET} HTTP 错误（{status}）：{_http_error_message(status)}")
            sys.exit(1)
        raise


if __name__ == "__main__":
    asyncio.run(async_main())
