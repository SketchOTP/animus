#!/usr/bin/env bash
# After editing server.py (or anything under this directory), run this so systemd
# loads the new code. Optional: pull the monorepo first.
set -euo pipefail
CHAT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MONO="$(cd "${CHAT_DIR}/.." && pwd)"
ENV_FILE="${CHAT_DIR}/hermes-chat.env"
PORT=3000
if [[ -f "${ENV_FILE}" ]]; then
  line="$(grep -E '^[[:space:]]*CHAT_PORT=' "${ENV_FILE}" | head -1 || true)"
  if [[ -n "${line}" ]]; then
    PORT="${line#*=}"
    PORT="${PORT//[$'\r']}"
  fi
fi

if [[ "${1:-}" == "--pull" ]]; then
  if [[ -d "${MONO}/.git" ]]; then
    if ! git -C "${MONO}" pull --ff-only; then
      echo "Warning: git pull failed (no upstream or merge conflicts); continuing with restart." >&2
    fi
  else
    echo "No git repo at ${MONO}; skipping pull." >&2
  fi
fi

restart() {
  systemctl --user daemon-reload 2>/dev/null || true
  systemctl --user restart hermes-chat.service
  systemctl --user is-active hermes-chat.service
}

if systemctl --user cat hermes-chat.service &>/dev/null; then
  restart
elif sudo -n systemctl cat hermes-chat.service &>/dev/null 2>&1; then
  sudo systemctl daemon-reload
  sudo systemctl restart hermes-chat.service
  sudo systemctl is-active hermes-chat.service
else
  echo "No hermes-chat.service (user or passwordless sudo system). Restart manually." >&2
  exit 1
fi

echo "GET https://127.0.0.1:${PORT}/api/hermes-chat-meta (use -k if TLS):"
curl -kfsS "https://127.0.0.1:${PORT}/api/hermes-chat-meta" | jq '{rev, tls_enabled, public_url}'
