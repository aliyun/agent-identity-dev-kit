#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="${ROOT_DIR}/.venv-bootstrap/bin/python"
REGION_IDENTITY="${AGENT_IDENTITY_REGION_ID:-cn-beijing}"
REGION_OPENAPI="cn-hangzhou"
OPENAPI_ENDPOINT="openapiexplorer.aliyuncs.com"
AGENT_LOG="${DEPLOY_AGENT_LOG:-/tmp/deploy_starter.log}"
BACKEND_LOG="${DEPLOY_BACKEND_LOG:-/tmp/backend_app.log}"
AGENT_PID_FILE="${DEPLOY_AGENT_PID_FILE:-/tmp/deploy_starter.pid}"
BACKEND_PID_FILE="${DEPLOY_BACKEND_PID_FILE:-/tmp/backend_app.pid}"
HEALTH_TIMEOUT_SECONDS="${DEPLOY_HEALTH_TIMEOUT_SECONDS:-60}"

print_section() {
  echo
  echo "================================================================"
  echo "[DEPLOY] $1"
  echo "================================================================"
}

require_env() {
  local key="$1"
  if [[ -z "${!key:-}" ]]; then
    echo "[ERROR] Missing required environment variable: ${key}"
    exit 1
  fi
}

print_section "Checking required inputs"
require_env "ALIBABA_CLOUD_ACCESS_KEY_ID"
require_env "ALIBABA_CLOUD_ACCESS_KEY_SECRET"
require_env "DASHSCOPE_API_KEY"
if [[ ! -x "${PYTHON_BIN}" ]]; then
  echo "[ERROR] Required runtime not found: ${PYTHON_BIN}"
  echo "Please run bootstrap.sh first to create the customer runtime environment."
  exit 1
fi
if [[ ! -f "${ROOT_DIR}/.config.json" ]]; then
  echo "[ERROR] .config.json not found. Run bootstrap.sh/prepare.py first."
  exit 1
fi
echo "[OK] Input validation passed."
echo "[OK] Using Python runtime: ${PYTHON_BIN}"

check_http_health() {
  local url="$1"
  "${PYTHON_BIN}" - "${url}" <<'PY'
import sys
import urllib.request

url = sys.argv[1]
try:
    with urllib.request.urlopen(url, timeout=2) as response:
        body = response.read(1024).decode("utf-8", errors="replace")
        if 200 <= response.status < 300:
            print(body)
            raise SystemExit(0)
        print(f"unexpected status={response.status} body={body}", file=sys.stderr)
except Exception as exc:
    print(str(exc), file=sys.stderr)
raise SystemExit(1)
PY
}

wait_for_health() {
  local name="$1"
  local url="$2"
  local log_file="$3"
  local deadline=$((SECONDS + HEALTH_TIMEOUT_SECONDS))
  local last_error=""

  while (( SECONDS < deadline )); do
    if last_error="$(check_http_health "${url}" 2>&1)"; then
      echo "[OK] ${name} healthy: ${url}"
      echo "${last_error}"
      return 0
    fi
    sleep 2
  done

  echo "[ERROR] ${name} did not become healthy within ${HEALTH_TIMEOUT_SECONDS}s: ${url}"
  echo "[ERROR] Last health error: ${last_error}"
  echo "[ERROR] Last 120 log lines from ${log_file}:"
  if [[ -f "${log_file}" ]]; then
    tail -120 "${log_file}"
  else
    echo "(log file not found)"
  fi
  return 1
}

print_section "Reading local resource IDs from .config.json"
CONFIG_OUTPUT="$("${PYTHON_BIN}" - <<'PY'
import json
from pathlib import Path
cfg = json.loads(Path(".config.json").read_text(encoding="utf-8"))
print(cfg.get("apig_mcp_server_id", ""))
print(cfg.get("workload_identity_name", ""))
PY
)"
APIG_MCP_SERVER_ID="$(printf '%s\n' "${CONFIG_OUTPUT}" | sed -n '1p')"
WORKLOAD_IDENTITY_NAME="$(printf '%s\n' "${CONFIG_OUTPUT}" | sed -n '2p')"
if [[ -z "${APIG_MCP_SERVER_ID}" ]]; then
  echo "[ERROR] apig_mcp_server_id is missing in .config.json"
  exit 1
fi
if [[ -z "${WORKLOAD_IDENTITY_NAME}" ]]; then
  echo "[ERROR] workload_identity_name is missing in .config.json"
  exit 1
fi
echo "[OK] apig_mcp_server_id=${APIG_MCP_SERVER_ID}"
echo "[OK] workload_identity_name=${WORKLOAD_IDENTITY_NAME}"

print_section "Resolving MCP_SERVER from OpenAPIExplorer ListApiMcpServers"
OPENAPI_JSON="$(
  aliyun openapiexplorer ListApiMcpServers \
    --region "${REGION_OPENAPI}" \
    --endpoint "${OPENAPI_ENDPOINT}" \
    --access-key-id "${ALIBABA_CLOUD_ACCESS_KEY_ID}" \
    --access-key-secret "${ALIBABA_CLOUD_ACCESS_KEY_SECRET}"
)"

MCP_SERVER="$(
  OPENAPI_JSON="${OPENAPI_JSON}" "${PYTHON_BIN}" - <<'PY'
import json
import os

payload = json.loads(os.environ["OPENAPI_JSON"])
servers = payload.get("apiMcpServers") or payload.get("ApiMcpServers") or []
target = None
for item in servers:
    if not isinstance(item, dict):
        continue
    name = str(item.get("name", "")).lower()
    sys_name = str((item.get("systemMcpServerInfo") or {}).get("name", "")).lower()
    product = str((item.get("systemMcpServerInfo") or {}).get("product", "")).lower()
    if name == "resourcecenter" or sys_name == "resourcecenter" or product == "resourcecenter":
        target = item
        break
if not target:
    raise SystemExit("resourcecenter MCP server not found in ListApiMcpServers response")
urls = target.get("urls") or {}
mcp_url = urls.get("mcp")
if not mcp_url:
    raise SystemExit("resourcecenter MCP server found but urls.mcp is missing")
print(mcp_url)
PY
)"
echo "[OK] MCP_SERVER=${MCP_SERVER}"

print_section "Resolving DEMO_MCP_SERVER from APIG GetMcpServer"
APIG_MCP_JSON="$(
  aliyun apig GetMcpServer \
    --mcpServerId "${APIG_MCP_SERVER_ID}" \
    --region "${REGION_IDENTITY}" \
    --access-key-id "${ALIBABA_CLOUD_ACCESS_KEY_ID}" \
    --access-key-secret "${ALIBABA_CLOUD_ACCESS_KEY_SECRET}"
)"

DEMO_OUTPUT="$(
  APIG_MCP_JSON="${APIG_MCP_JSON}" "${PYTHON_BIN}" - <<'PY'
import json
import os

payload = json.loads(os.environ["APIG_MCP_JSON"])
data = payload.get("data") or payload.get("Data") or {}
environment_id = data.get("environmentId")
name = data.get("name")
if not environment_id or not name:
    raise SystemExit("GetMcpServer response missing environmentId or name")
print(environment_id)
print(name)
PY
)"
ENVIRONMENT_ID="$(printf '%s\n' "${DEMO_OUTPUT}" | sed -n '1p')"
MCP_NAME="$(printf '%s\n' "${DEMO_OUTPUT}" | sed -n '2p')"
if [[ -z "${ENVIRONMENT_ID}" || -z "${MCP_NAME}" ]]; then
  echo "[ERROR] Failed to parse environmentId/name from GetMcpServer response"
  exit 1
fi
DEMO_MCP_SERVER="http://${ENVIRONMENT_ID}-cn-beijing.alicloudapi.com/mcp-servers/${MCP_NAME}"
echo "[OK] DEMO_MCP_SERVER=${DEMO_MCP_SERVER}"

print_section "Restarting local services"
pkill -f "deploy_starter.main" >/dev/null 2>&1 || true
pkill -f "application.backend.app" >/dev/null 2>&1 || true
rm -f "${AGENT_PID_FILE}" "${BACKEND_PID_FILE}"

ALIBABA_CLOUD_ACCESS_KEY_ID="${ALIBABA_CLOUD_ACCESS_KEY_ID}" \
ALIBABA_CLOUD_ACCESS_KEY_SECRET="${ALIBABA_CLOUD_ACCESS_KEY_SECRET}" \
DASHSCOPE_API_KEY="${DASHSCOPE_API_KEY}" \
AGENT_IDENTITY_WORKLOAD_IDENTITY_NAME="${WORKLOAD_IDENTITY_NAME}" \
MCP_SERVER="${MCP_SERVER}" \
DEMO_MCP_SERVER="${DEMO_MCP_SERVER}" \
nohup "${PYTHON_BIN}" -m deploy_starter.main >"${AGENT_LOG}" 2>&1 &
AGENT_PID="$!"
echo "${AGENT_PID}" > "${AGENT_PID_FILE}"

ALIBABA_CLOUD_ACCESS_KEY_ID="${ALIBABA_CLOUD_ACCESS_KEY_ID}" \
ALIBABA_CLOUD_ACCESS_KEY_SECRET="${ALIBABA_CLOUD_ACCESS_KEY_SECRET}" \
DASHSCOPE_API_KEY="${DASHSCOPE_API_KEY}" \
AGENT_IDENTITY_WORKLOAD_IDENTITY_NAME="${WORKLOAD_IDENTITY_NAME}" \
MCP_SERVER="${MCP_SERVER}" \
DEMO_MCP_SERVER="${DEMO_MCP_SERVER}" \
nohup "${PYTHON_BIN}" -m application.backend.app >"${BACKEND_LOG}" 2>&1 &
BACKEND_PID="$!"
echo "${BACKEND_PID}" > "${BACKEND_PID_FILE}"

echo "[OK] Services launched."
echo "  - deploy_starter pid: ${AGENT_PID}"
echo "  - backend pid: ${BACKEND_PID}"
echo "  - deploy_starter log: ${AGENT_LOG}"
echo "  - backend log: ${BACKEND_LOG}"

print_section "Checking service health"
wait_for_health "deploy_starter" "http://127.0.0.1:8080/health" "${AGENT_LOG}"
wait_for_health "backend" "http://127.0.0.1:8090/health" "${BACKEND_LOG}"

print_section "Summary"
echo "AGENT_IDENTITY_WORKLOAD_IDENTITY_NAME=${WORKLOAD_IDENTITY_NAME}"
echo "MCP_SERVER=${MCP_SERVER}"
echo "DEMO_MCP_SERVER=${DEMO_MCP_SERVER}"
echo
echo "Next step: open http://localhost:8090"
