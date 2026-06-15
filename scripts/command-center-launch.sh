#!/usr/bin/env bash
# Start Animus Command Center (if needed) and open it in the default browser.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_F="${ROOT}/animus.env"
LOG_DIR="${HOME}/.animus/logs"
LOG_FILE="${LOG_DIR}/command_center_launch.log"
ICON="${ROOT}/animus-command-center/app/ghostonlyicon.png"

mkdir -p "${LOG_DIR}"
exec >>"${LOG_FILE}" 2>&1
echo "=== command-center-launch $(date -Is) ==="

HOST="127.0.0.1"
PORT="3010"
if [[ -f "${ENV_F}" ]]; then
  while IFS= read -r line || [[ -n "${line}" ]]; do
    [[ "${line}" =~ ^[[:space:]]*# ]] && continue
    [[ "${line}" =~ ^[[:space:]]*$ ]] && continue
    if [[ "${line}" =~ ^[[:space:]]*COMMAND_CENTER_HOST= ]]; then
      HOST="$(echo "${line#*=}" | xargs)"
    elif [[ "${line}" =~ ^[[:space:]]*COMMAND_CENTER_PORT= ]]; then
      PORT="$(echo "${line#*=}" | xargs)"
    fi
  done <"${ENV_F}"
fi

if [[ "${HOST}" == "::" || "${HOST}" == "0.0.0.0" ]]; then
  HOST="127.0.0.1"
fi

URL="http://${HOST}:${PORT}/"
HEALTH_URL="${URL}healthz"

is_healthy() {
  curl -fsS "${HEALTH_URL}" >/dev/null 2>&1
}

wait_http() {
  local url="$1"
  local tries="${2:-30}"
  for _ in $(seq 1 "${tries}"); do
    if curl -fsS "${url}" >/dev/null 2>&1; then
      return 0
    fi
    sleep 1
  done
  return 1
}

if ! is_healthy; then
  if systemctl --user cat animus-command-center.service &>/dev/null; then
    systemctl --user start animus-command-center.service || true
  else
    echo "Starting Command Center dev server on ${URL}"
    nohup "${ROOT}/scripts/run-command-center.sh" >>"${LOG_FILE}" 2>&1 &
  fi
  if ! wait_http "${HEALTH_URL}"; then
    echo "Command Center not healthy at ${URL}; opening browser anyway"
  fi
else
  echo "Command Center already running at ${URL}"
  LAN_IP="$(hostname -I 2>/dev/null | awk '{print $1}')"
  if [[ -n "${LAN_IP}" ]]; then
    echo "LAN access: http://${LAN_IP}:${PORT}/"
  fi
fi

if command -v xdg-open >/dev/null 2>&1; then
  xdg-open "${URL}"
else
  echo "Open ${URL} manually (xdg-open unavailable)"
fi
