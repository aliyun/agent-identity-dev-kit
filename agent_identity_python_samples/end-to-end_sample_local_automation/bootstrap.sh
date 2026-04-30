#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${ROOT_DIR}/.venv-bootstrap"
PYTHON_BIN="${PYTHON_BIN:-python3}"

# Two dependency source profiles are supported:
# - internal: use internal mirrors (current default before public package release)
# - public: use default PyPI (for customer release)
PIP_PROFILE="${BOOTSTRAP_PIP_PROFILE:-public}"
INTERNAL_PIP_INDEX_URL_DEFAULT="http://yum.tbsite.net/aliyun-pypi/simple/"
INTERNAL_PIP_EXTRA_INDEX_URL_DEFAULT="http://yum.tbsite.net/pypi/simple/"
INTERNAL_PIP_TRUSTED_HOST_DEFAULT="yum.tbsite.net"

print_section() {
  echo
  echo "================================================================"
  echo "[BOOTSTRAP] $1"
  echo "================================================================"
}

check_required_env() {
  local missing=0
  if [[ -z "${ALIBABA_CLOUD_ACCESS_KEY_ID:-}" ]]; then
    echo "[ERROR] Missing environment variable: ALIBABA_CLOUD_ACCESS_KEY_ID"
    missing=1
  fi
  if [[ -z "${ALIBABA_CLOUD_ACCESS_KEY_SECRET:-}" ]]; then
    echo "[ERROR] Missing environment variable: ALIBABA_CLOUD_ACCESS_KEY_SECRET"
    missing=1
  fi
  if [[ -z "${DASHSCOPE_API_KEY:-}" ]]; then
    echo "[ERROR] Missing environment variable: DASHSCOPE_API_KEY"
    missing=1
  fi
  if [[ "$missing" -eq 1 ]]; then
    echo
    echo "Please export the required variables, then rerun:"
    echo "  export ALIBABA_CLOUD_ACCESS_KEY_ID=<your-admin-ak>"
    echo "  export ALIBABA_CLOUD_ACCESS_KEY_SECRET=<your-admin-sk>"
    echo "  export DASHSCOPE_API_KEY=<your-dashscope-api-key>"
    exit 1
  fi
}

print_section "Checking Python runtime"
if ! command -v "${PYTHON_BIN}" >/dev/null 2>&1; then
  echo "[ERROR] ${PYTHON_BIN} not found. Please install Python 3.10+."
  exit 1
fi
"${PYTHON_BIN}" --version

print_section "Checking required environment variables"
check_required_env
echo "[OK] Required credentials are present."

print_section "Creating virtual environment"
if [[ ! -d "${VENV_DIR}" ]]; then
  "${PYTHON_BIN}" -m venv "${VENV_DIR}"
  echo "[OK] Created ${VENV_DIR}"
else
  echo "[OK] Reusing existing ${VENV_DIR}"
fi

print_section "Installing dependencies"
"${VENV_DIR}/bin/python" -m pip install --upgrade pip

if [[ "${PIP_PROFILE}" == "internal" ]]; then
  PIP_INDEX_URL="${BOOTSTRAP_PIP_INDEX_URL:-${INTERNAL_PIP_INDEX_URL_DEFAULT}}"
  PIP_EXTRA_INDEX_URL="${BOOTSTRAP_PIP_EXTRA_INDEX_URL:-${INTERNAL_PIP_EXTRA_INDEX_URL_DEFAULT}}"
  PIP_TRUSTED_HOST="${BOOTSTRAP_PIP_TRUSTED_HOST:-${INTERNAL_PIP_TRUSTED_HOST_DEFAULT}}"
  echo "[BOOTSTRAP] Dependency source profile: internal"
  echo "[BOOTSTRAP] index-url=${PIP_INDEX_URL}"
  echo "[BOOTSTRAP] extra-index-url=${PIP_EXTRA_INDEX_URL}"
elif [[ "${PIP_PROFILE}" == "public" ]]; then
  echo "[BOOTSTRAP] Dependency source profile: public (default PyPI)"
else
  echo "[ERROR] Unsupported BOOTSTRAP_PIP_PROFILE: ${PIP_PROFILE}"
  echo "Supported values: internal | public"
  exit 1
fi

set +e
if [[ "${PIP_PROFILE}" == "internal" ]]; then
  "${VENV_DIR}/bin/pip" install \
    -i "${PIP_INDEX_URL}" \
    --extra-index-url "${PIP_EXTRA_INDEX_URL}" \
    --trusted-host "${PIP_TRUSTED_HOST}" \
    -r "${ROOT_DIR}/requirements.txt"
else
  "${VENV_DIR}/bin/pip" install -r "${ROOT_DIR}/requirements.txt"
fi
install_exit_code=$?
set -e
if [[ "${install_exit_code}" -ne 0 ]]; then
  echo "[ERROR] Dependency installation failed."
  if [[ "${PIP_PROFILE}" == "internal" ]]; then
    echo "Please ensure the following package indexes are reachable from your environment:"
    echo "  - ${PIP_INDEX_URL}"
    echo "  - ${PIP_EXTRA_INDEX_URL}"
    echo
    echo "You can override indexes if needed:"
    echo "  export BOOTSTRAP_PIP_INDEX_URL=<index-url>"
    echo "  export BOOTSTRAP_PIP_EXTRA_INDEX_URL=<extra-index-url>"
    echo "  export BOOTSTRAP_PIP_TRUSTED_HOST=<trusted-host>"
  else
    echo "Public profile failed. This may happen before internal SDK packages are published to PyPI."
    echo "Try internal profile:"
    echo "  export BOOTSTRAP_PIP_PROFILE=internal"
    echo "  bash bootstrap.sh"
  fi
  exit "${install_exit_code}"
fi
echo "[OK] Dependencies installed."

print_section "Installing local inner SDK package"
"${VENV_DIR}/bin/pip" install -e "${ROOT_DIR}/alibabacloud_agentidentity20250901_inner"
# Ensure the public SDK package files are intact (guards against stale venv state).
"${VENV_DIR}/bin/pip" install --force-reinstall --no-deps alibabacloud-agentidentity20250901 >/dev/null 2>&1 || true
"${VENV_DIR}/bin/python" - <<'PY'
from alibabacloud_agentidentity20250901_inner.client import Client as InnerClient
from alibabacloud_agentidentity20250901_inner import models as inner_models
methods = dir(InnerClient)
required = ["create_policy_set", "attach_policy_set_to_gateway"]
missing = [m for m in required if m not in methods]
if missing:
    raise SystemExit(f"[ERROR] inner SDK methods missing: {missing}")
if not hasattr(inner_models, "CreatePolicySetRequest"):
    raise SystemExit("[ERROR] inner SDK models mismatch: CreatePolicySetRequest is missing.")
print("[OK] inner SDK package verified: PolicySet methods are available.")
PY

print_section "Running resource preparation"
cd "${ROOT_DIR}"
echo "[BOOTSTRAP] Default prepare scope: Section 1 + Section 3 (AI Gateway related resources)."
echo "[BOOTSTRAP] To run Section 1 only, set:"
echo "[BOOTSTRAP]   ENABLE_AI_GATEWAY_SETUP=false ENABLE_AGENTIDENTITY_POLICYSET_SETUP=false"
"${VENV_DIR}/bin/python" "${ROOT_DIR}/prepare.py"

print_section "Done"
echo "[OK] prepare.py completed."
echo "Next step: start local services and open http://localhost:8090"
