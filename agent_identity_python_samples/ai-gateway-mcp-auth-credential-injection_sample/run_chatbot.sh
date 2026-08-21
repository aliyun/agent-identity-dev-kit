#!/bin/bash
# 串联脚本：OIDC 登录 → 获取 ID Token → 启动 MCP Chatbot
#
# 用法：
#   方式一：通过环境变量配置
#     export OIDC_DISCOVERY_URL="https://..."
#     export OIDC_CLIENT_ID="client_xxx"
#     export OIDC_CLIENT_SECRET="xxx"
#     export LLM_API_KEY="sk-xxx"
#     export LLM_BASE_URL="https://..."
#     export MCP_SERVER_URL="http://..."
#     ./run_chatbot.sh
#
#   方式二：通过 .env 文件加载（脚本会自动读取同目录下的 .env）
#
# 必需环境变量（无默认值，缺失则退出）：
#   OIDC_DISCOVERY_URL    - OIDC Discovery 地址
#   OIDC_CLIENT_ID        - OAuth2 Client ID
#   OIDC_CLIENT_SECRET    - OAuth2 Client Secret
#   AGENT_IDENTITY_WORKLOAD_IDENTITY_NAME - Workload Identity 名称（ID Token 换 WAT 用）
#   LLM_API_KEY           - LLM API Key
#   LLM_BASE_URL          - LLM API Base URL
#   MCP_SERVER_URL        - MCP 服务端点地址
#
# 可选环境变量（有默认值）：
#   AGENT_IDENTITY_REGION_ID  - Region ID（默认 cn-beijing）
#   LLM_MODEL                 - LLM 模型名称（默认 qwen-max）

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# ─── 自动加载 .env 文件（如存在） ───────────────────────────
if [ -f "$SCRIPT_DIR/.env" ]; then
    set -a
    source "$SCRIPT_DIR/.env"
    set +a
fi

# ─── 校验必需环境变量 ─────────────────────────────────────
missing=()
[ -z "$OIDC_DISCOVERY_URL" ]  && missing+=("OIDC_DISCOVERY_URL")
[ -z "$OIDC_CLIENT_ID" ]      && missing+=("OIDC_CLIENT_ID")
[ -z "$OIDC_CLIENT_SECRET" ]              && missing+=("OIDC_CLIENT_SECRET")
[ -z "$AGENT_IDENTITY_WORKLOAD_IDENTITY_NAME" ] && missing+=("AGENT_IDENTITY_WORKLOAD_IDENTITY_NAME")
[ -z "$LLM_API_KEY" ]         && missing+=("LLM_API_KEY")
[ -z "$LLM_BASE_URL" ]        && missing+=("LLM_BASE_URL")
[ -z "$MCP_SERVER_URL" ]      && missing+=("MCP_SERVER_URL")

if [ ${#missing[@]} -gt 0 ]; then
    echo "✘ 缺少必需的环境变量：" >&2
    for var in "${missing[@]}"; do
        echo "  - $var" >&2
    done
    echo "" >&2
    echo "请通过 export 设置或在同目录下创建 .env 文件，示例：" >&2
    echo '  OIDC_DISCOVERY_URL=https://signin-cn-beijing.aliyunagentid.com/up_xxx/.well-known/openid-configuration' >&2
    echo '  OIDC_CLIENT_ID=client_xxx' >&2
    echo '  OIDC_CLIENT_SECRET=xxx' >&2
    echo '  LLM_API_KEY=sk-xxx' >&2
    echo '  LLM_BASE_URL=https://llm-xxx.cn-beijing.maas.aliyuncs.com/compatible-mode/v1' >&2
    echo '  MCP_SERVER_URL=http://env-xxx-cn-beijing.alicloudapi.com/mcp-servers/xxx' >&2
    exit 1
fi

# ─── 可选变量默认值 ──────────────────────────────────────
REGION="${AGENT_IDENTITY_REGION_ID:-cn-beijing}"
MODEL="${LLM_MODEL:-qwen-max}"

echo "═══ Step 1: OIDC 登录获取 ID Token ═══"
echo ""

# oidc_login.py 已将纯 JWT token 输出到 stdout，其他信息输出到 stderr
# $() 只捕获 stdout（纯 token），stderr 自然显示在终端让用户看到登录进度
ID_TOKEN=$(python3 "$SCRIPT_DIR/oidc_login.py" \
    --discovery-url "$OIDC_DISCOVERY_URL" \
    --client-id "$OIDC_CLIENT_ID" \
    --client-secret "$OIDC_CLIENT_SECRET")

if [ -z "$ID_TOKEN" ]; then
    echo "✘ 未能获取 ID Token" >&2
    exit 1
fi

echo "" >&2
echo "✓ ID Token 获取成功: ${ID_TOKEN:0:20}..." >&2
echo "" >&2
echo "═══ Step 2: 启动 MCP Chatbot ═══" >&2

# 用 exec 替换当前进程，确保 Ctrl+C 能正常终止 chatbot
exec python3 "$SCRIPT_DIR/mcp_chatbot.py" \
    --bearer-token "$ID_TOKEN" \
    --region "$REGION" \
    --api-key "$LLM_API_KEY" \
    --base-url "$LLM_BASE_URL" \
    --mcp-url "$MCP_SERVER_URL" \
    --model "$MODEL"
