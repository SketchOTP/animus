#!/usr/bin/env bash
# Dev launcher for the dedicated Animus Command Center dashboard (D-140).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"

if [[ -f "${ROOT}/animus.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "${ROOT}/animus.env"
  set +a
fi

export COMMAND_CENTER_HOST="${COMMAND_CENTER_HOST:-127.0.0.1}"
export COMMAND_CENTER_PORT="${COMMAND_CENTER_PORT:-3010}"
export GOVERNANCE_API_URL="${GOVERNANCE_API_URL:-http://127.0.0.1:8120}"

PYTHON="${ROOT}/.venv/bin/python3"
if [[ ! -x "${PYTHON}" ]]; then
  PYTHON="$(command -v python3)"
fi

URL="http://${COMMAND_CENTER_HOST}:${COMMAND_CENTER_PORT}/"
echo "Starting Animus Command Center on ${URL}"
echo "Governance API: ${GOVERNANCE_API_URL}"

exec "${PYTHON}" animus-command-center/server.py
