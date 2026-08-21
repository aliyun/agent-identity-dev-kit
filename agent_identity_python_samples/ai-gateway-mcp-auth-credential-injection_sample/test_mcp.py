#!/usr/bin/env python3
"""
MCP 连接测试脚本

功能：
1. OIDC 登录获取 ID Token
2. 用 ID Token 换取 Workload Access Token (WAT)
3. 连接 MCP Server，列出工具
4. 显示工具列表或授权提示（-32042 elicitation）

用法：
    # 使用 .env 文件（同目录或上层目录）
    python3 test_mcp.py

    # 直接传参
    python3 test_mcp.py --mcp-url "http://..." --region cn-beijing

    # 跳过 OIDC 登录，直接传 ID Token
    python3 test_mcp.py --bearer-token "eyJ..."

环境变量（通过 .env 或 export）：
    OIDC_DISCOVERY_URL, OIDC_CLIENT_ID, OIDC_CLIENT_SECRET
    MCP_SERVER_URL, AGENT_IDENTITY_REGION_ID
"""

import argparse
import asyncio
import json
import os
import subprocess
import sys
from datetime import timedelta

# ─── 加载 .env ─────────────────────────────────────────────
def load_env(env_path=None):
    """加载 .env 文件"""
    if env_path and os.path.exists(env_path):
        pass
    elif os.path.exists(".env"):
        env_path = ".env"
    elif os.path.exists("../.env"):
        env_path = "../.env"
    else:
        return

    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip()
                if value and key not in os.environ:
                    os.environ[key] = value

# ─── 获取 WAT ──────────────────────────────────────────────
def get_wat(id_token: str | None, region: str) -> str | None:
    """用 ID Token 换取 Workload Access Token"""
    try:
        from agent_identity_python_sdk import IdentityClient
    except ImportError:
        print("✘ 缺少依赖: pip install agent-identity-python-sdk")
        sys.exit(1)

    workload_identity = os.environ.get("AGENT_IDENTITY_WORKLOAD_IDENTITY_NAME", "")
    if not workload_identity:
        print("✘ 未设置 AGENT_IDENTITY_WORKLOAD_IDENTITY_NAME，请先设置该环境变量"
              "（Agent Identity 控制台创建的 Workload Identity 名称）")
        return None

    client = IdentityClient(region_id=region)
    print(f"[WAT] 使用 ID Token 换取 Workload Access Token...")
    try:
        token = client.get_workload_access_token(workload_identity, user_token=id_token)
        print(f"[WAT] ✓ 获取成功")
        print(f"[WAT] Token 前缀: {token[:30]}...")
        return token
    except Exception as e:
        print(f"✘ WAT 获取失败: {e}")
        return None

# ─── OIDC 登录 ─────────────────────────────────────────────
def oidc_login() -> str | None:
    """调用 oidc_login.py 进行 OIDC 登录"""
    discovery_url = os.environ.get("OIDC_DISCOVERY_URL", "")
    client_id = os.environ.get("OIDC_CLIENT_ID", "")
    client_secret = os.environ.get("OIDC_CLIENT_SECRET", "")

    if not all([discovery_url, client_id, client_secret]):
        print("✘ 缺少 OIDC 配置 (OIDC_DISCOVERY_URL, OIDC_CLIENT_ID, OIDC_CLIENT_SECRET)")
        return None

    # 查找 oidc_login.py
    script_paths = [
        os.path.join(os.path.dirname(__file__), "oidc_login.py"),
        os.path.join(os.path.dirname(__file__), "..", "oidc_login.py"),
    ]
    oidc_script = None
    for p in script_paths:
        if os.path.exists(p):
            oidc_script = p
            break

    if not oidc_script:
        print("✘ 找不到 oidc_login.py，请放在同目录下")
        return None

    print("[OIDC] 启动登录...")
    result = subprocess.run(
        [sys.executable, oidc_script,
         "--discovery-url", discovery_url,
         "--client-id", client_id,
         "--client-secret", client_secret],
        capture_output=True, text=True
    )

    # stderr 显示给用户
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)

    if result.returncode != 0 or not result.stdout.strip():
        print("✘ OIDC 登录失败")
        return None

    token = result.stdout.strip()
    print(f"[OIDC] ✓ 获取 ID Token: {token[:20]}...")
    return token

# ─── MCP 连接测试 ──────────────────────────────────────────
async def test_mcp(mcp_url: str, bearer_token: str):
    """连接 MCP Server 并列出工具"""
    try:
        from mcp import ClientSession
        from mcp.client.streamable_http import streamablehttp_client
    except ImportError:
        print("✘ 缺少依赖: pip install mcp")
        sys.exit(1)

    print(f"\n{'═' * 60}")
    print(f"  MCP 连接测试")
    print(f"{'═' * 60}")
    print(f"  URL: {mcp_url}")
    print(f"  Auth: Bearer Token (WAT)")
    print(f"{'─' * 60}")

    headers = {"Authorization": f"Bearer {bearer_token}"}

    try:
        async with streamablehttp_client(
            mcp_url,
            headers=headers,
            timeout=30,
            sse_read_timeout=120,
        ) as (read_stream, write_stream, _):

            async with ClientSession(
                read_stream, write_stream,
                read_timeout_seconds=timedelta(seconds=60),
            ) as session:

                # 初始化
                try:
                    init_result = await session.initialize()
                    print(f"\n[初始化] ✓ 协议版本: {init_result.protocolVersion}")
                    if init_result.serverInfo:
                        print(f"[初始化] Server: {init_result.serverInfo.name} v{init_result.serverInfo.version}")
                except Exception as e:
                    err_str = str(e)
                    if "elicitation" in err_str.lower() or "-32042" in err_str:
                        print(f"\n[初始化] ⚠ 收到 URL Elicitation（授权请求）")
                        # 从 McpError.error.data 中提取授权 URL
                        auth_url = None
                        message = ""
                        try:
                            if hasattr(e, 'error') and hasattr(e.error, 'data'):
                                data = e.error.data
                                elicitations = data.get('elicitations', [])
                                if elicitations:
                                    auth_url = elicitations[0].get('url', '')
                                    message = elicitations[0].get('message', '')
                                    print(f"  消息: {message}")
                        except Exception:
                            pass

                        if auth_url:
                            print(f"\n  🔗 请在浏览器中打开以下链接完成授权：")
                            print(f"  {auth_url}")
                            print(f"\n  授权完成后，请重新运行测试脚本。")
                        else:
                            print(f"  详细信息: {err_str[:800]}")
                            print(f"\n  授权完成后，请重新运行测试脚本。")
                        return
                    else:
                        print(f"\n[初始化] ✗ 失败: {e}")
                        return

                # 列出工具
                try:
                    tools = await session.list_tools()
                    if tools and tools.tools:
                        print(f"\n[工具] 共 {len(tools.tools)} 个工具:")
                        for t in tools.tools:
                            desc = t.description or "(无描述)"
                            params = []
                            if t.inputSchema and t.inputSchema.get("properties"):
                                params = list(t.inputSchema["properties"].keys())
                            param_str = f"  参数: {', '.join(params)}" if params else ""
                            print(f"  • {t.name}: {desc}")
                            if param_str:
                                print(f"    {param_str}")
                    else:
                        print(f"\n[工具] 未返回任何工具")
                except Exception as e:
                    err_str = str(e)
                    print(f"\n[工具] ✗ 列出工具失败: {err_str[:500]}")
                    if "-32042" in err_str or "elicitation" in err_str.lower():
                        print(f"\n  → 工具列表请求触发授权提示")

                # 列出资源（如果支持）
                try:
                    resources = await session.list_resources()
                    if resources and resources.resources:
                        print(f"\n[资源] 共 {len(resources.resources)} 个资源:")
                        for r in resources.resources[:5]:
                            print(f"  • {r.uri}: {r.name or '(无名)'}")
                except Exception:
                    pass

                # 列出提示模板（如果支持）
                try:
                    prompts = await session.list_prompts()
                    if prompts and prompts.prompts:
                        print(f"\n[提示模板] 共 {len(prompts.prompts)} 个:")
                        for p in prompts.prompts[:5]:
                            print(f"  • {p.name}: {p.description or '(无描述)'}")
                except Exception:
                    pass

    except Exception as e:
        err_str = str(e)
        # 解包 ExceptionGroup
        actual_err = e
        if hasattr(e, 'exceptions') and e.exceptions:
            actual_err = e.exceptions[0]
            err_str = str(actual_err)
            # 再解包一层
            if hasattr(actual_err, 'exceptions') and actual_err.exceptions:
                actual_err = actual_err.exceptions[0]
                err_str = str(actual_err)

        print(f"\n[连接] ✗ 连接失败:")
        print(f"  错误类型: {type(actual_err).__name__}")

        if hasattr(actual_err, 'response'):
            status = actual_err.response.status_code
            print(f"  HTTP {status}")
            print(f"  URL: {actual_err.request.url if hasattr(actual_err, 'request') else 'unknown'}")
            try:
                body = actual_err.response.text[:300]
                if body:
                    print(f"  Body: {body}")
            except Exception:
                pass  # streaming response, can't read body
        elif "401" in err_str:
            print(f"  HTTP 401 Unauthorized - WAT 无效或已过期")
        elif "403" in err_str:
            print(f"  HTTP 403 Forbidden - 权限被拒绝")
        elif "Connection refused" in err_str or "connect" in err_str.lower():
            print(f"  无法连接到 MCP 服务器，请检查 URL 和网络")
        else:
            print(f"  {err_str[:500]}")

# ─── 主入口 ──────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="MCP 连接测试")
    parser.add_argument("--mcp-url", default=os.environ.get("MCP_SERVER_URL", ""),
                        help="MCP Server URL")
    parser.add_argument("--bearer-token", default="",
                        help="直接传入 ID Token（跳过 OIDC 登录）")
    parser.add_argument("--region", default=os.environ.get("AGENT_IDENTITY_REGION_ID", "cn-beijing"),
                        help="Region ID (默认 cn-beijing)")
    parser.add_argument("--env", default="",
                        help=".env 文件路径")
    args = parser.parse_args()

    # 加载 .env
    load_env(args.env or None)

    # MCP URL
    mcp_url = args.mcp_url or os.environ.get("MCP_SERVER_URL", "")
    if not mcp_url:
        print("✘ 请指定 --mcp-url 或设置 MCP_SERVER_URL 环境变量")
        sys.exit(1)

    # 获取 ID Token
    if args.bearer_token:
        id_token = args.bearer_token
        print(f"[认证] 使用传入的 Token: {id_token[:20]}...")
    else:
        id_token = oidc_login()
        if not id_token:
            sys.exit(1)

    # 换取 WAT
    region = args.region
    bearer_token = get_wat(id_token, region)
    if not bearer_token:
        print("✘ 无法获取 WAT")
        sys.exit(1)

    # 测试 MCP
    asyncio.run(test_mcp(mcp_url, bearer_token))


if __name__ == "__main__":
    main()
