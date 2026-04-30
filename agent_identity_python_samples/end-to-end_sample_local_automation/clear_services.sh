#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="${ROOT_DIR}/.venv-bootstrap/bin/python"

print_section() {
  echo
  echo "================================================================"
  echo "[CLEAR] $1"
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

if [[ ! -x "${PYTHON_BIN}" ]]; then
  echo "[ERROR] Required runtime not found: ${PYTHON_BIN}"
  echo "Please run bootstrap.sh first to create the customer runtime environment."
  exit 1
fi

if ! command -v aliyun >/dev/null 2>&1; then
  echo "[ERROR] aliyun CLI not found in PATH."
  echo "Please run bootstrap.sh first, or install Alibaba Cloud CLI and ensure the aliyun command is available."
  exit 1
fi

if [[ ! -f "${ROOT_DIR}/.config.json" ]]; then
  echo "[ERROR] .config.json not found. Nothing to clear."
  exit 1
fi

echo "[OK] Input validation passed."
echo "[OK] Using Python runtime: ${PYTHON_BIN}"
echo "[OK] Using Aliyun CLI: $(command -v aliyun)"
echo "[OK] Region: ${AGENT_IDENTITY_REGION_ID:-cn-beijing}"
if [[ "${CLEAR_DRY_RUN:-}" =~ ^(1|true|TRUE|yes|YES|on|ON)$ ]]; then
  echo "[OK] CLEAR_DRY_RUN is enabled. No cloud resources will be deleted."
fi

print_section "Resource cleanup plan"
"${PYTHON_BIN}" - <<'PY'
import json
from pathlib import Path

cfg = json.loads(Path(".config.json").read_text(encoding="utf-8"))
keys = [
    "apig_mcp_server_id",
    "apig_plugin_attachment_id",
    "apig_policy_attachment_id",
    "apig_policy_id",
    "apig_plugin_id",
    "apig_service_id",
    "agentidentity_gateway_arn",
    "agentidentity_policy_name",
    "agentidentity_policy_set_name",
    "apig_gateway_id",
    "identity_provider_name",
    "workload_identity_name",
    "inbound_app_id",
    "mcp_app_id",
    "provisioned_ram_user_name",
]
for key in keys:
    value = cfg.get(key)
    if value:
        print(f"  - {key}: {value}")
PY

print_section "Running cleanup"
cd "${ROOT_DIR}"
"${PYTHON_BIN}" -m clear

print_section "Done"
echo "[OK] Cleanup completed."
