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

export COMMAND_CENTER_HOST="${COMMAND_CENTER_HOST:-0.0.0.0}"
export COMMAND_CENTER_PORT="${COMMAND_CENTER_PORT:-3010}"
export GOVERNANCE_API_URL="${GOVERNANCE_API_URL:-http://127.0.0.1:8120}"

PYTHON="${ROOT}/.venv/bin/python3"
if [[ ! -x "${PYTHON}" ]]; then
  PYTHON="$(command -v python3)"
fi

LAN_IP="$(hostname -I 2>/dev/null | awk '{print $1}')"
URL="http://${COMMAND_CENTER_HOST}:${COMMAND_CENTER_PORT}/"
echo "Starting Animus Command Center on ${URL}"
if [[ "${COMMAND_CENTER_HOST}" == "0.0.0.0" || "${COMMAND_CENTER_HOST}" == "::" ]]; then
  echo "Local browser: http://127.0.0.1:${COMMAND_CENTER_PORT}/"
  if [[ -n "${LAN_IP}" ]]; then
    echo "LAN access:    http://${LAN_IP}:${COMMAND_CENTER_PORT}/"
  fi
fi
echo "Governance API: ${GOVERNANCE_API_URL}"

exec "${PYTHON}" animus-command-center/server.py
