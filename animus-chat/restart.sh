#!/usr/bin/env bash
# Reload ANIMUS after editing server.py (user systemd unit animus.service).
set -euo pipefail
CHAT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${CHAT_DIR}/animus.env"
if [[ ! -f "${ENV_FILE}" ]]; then
  ENV_FILE="${CHAT_DIR}/hermes-chat.env"
fi
PORT=3001
if [[ -f "${ENV_FILE}" ]]; then
  line="$(grep -E '^[[:space:]]*CHAT_PORT=' "${ENV_FILE}" | head -1 || true)"
  if [[ -n "${line}" ]]; then
    PORT="${line#*=}"
    PORT="${PORT//[$'\r']}"
  fi
fi

if systemctl --user cat animus.service &>/dev/null; then
  systemctl --user daemon-reload 2>/dev/null || true
  systemctl --user restart animus.service
  systemctl --user is-active animus.service
elif sudo -n systemctl cat animus.service &>/dev/null 2>&1; then
  sudo systemctl daemon-reload
  sudo systemctl restart animus.service
  sudo systemctl is-active animus.service
else
  echo "No animus.service found. Restart manually (e.g. pkill -f server.py; python server.py)." >&2
  exit 1
fi

echo "Probe: curl -fsS http://127.0.0.1:${PORT}/api/health"
