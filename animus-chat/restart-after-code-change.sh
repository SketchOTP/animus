#!/usr/bin/env bash
# After editing server.py (or anything under animus-chat/), restart user systemd
# so the running process loads new code. Prefers animus.service (ANIMUS); falls
# back to legacy hermes-chat.service if present.
set -euo pipefail
CHAT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MONO="$(cd "${CHAT_DIR}/.." && pwd)"
PORT=3001
for envf in "${MONO}/animus.env" "${CHAT_DIR}/animus.env" "${CHAT_DIR}/hermes-chat.env"; do
  if [[ -f "${envf}" ]]; then
    line="$(grep -E '^[[:space:]]*CHAT_PORT=' "${envf}" | head -1 || true)"
    if [[ -n "${line}" ]]; then
      PORT="${line#*=}"
      PORT="${PORT//[$'\r']}"
      PORT="${PORT// /}"
      break
    fi
  fi
done

if [[ "${1:-}" == "--pull" ]]; then
  if [[ -d "${MONO}/.git" ]]; then
    if ! git -C "${MONO}" pull --ff-only; then
      echo "Warning: git pull failed (no upstream or merge conflicts); continuing with restart." >&2
    fi
  else
    echo "No git repo at ${MONO}; skipping pull." >&2
  fi
fi

restart_unit() {
  local u="$1"
  systemctl --user daemon-reload 2>/dev/null || true
  systemctl --user restart "${u}"
  systemctl --user is-active "${u}"
}

if systemctl --user cat animus.service &>/dev/null; then
  restart_unit animus.service
elif systemctl --user cat hermes-chat.service &>/dev/null; then
  restart_unit hermes-chat.service
elif sudo -n systemctl cat animus.service &>/dev/null 2>&1; then
  sudo systemctl daemon-reload
  sudo systemctl restart animus.service
  sudo systemctl is-active animus.service
elif sudo -n systemctl cat hermes-chat.service &>/dev/null 2>&1; then
  sudo systemctl daemon-reload
  sudo systemctl restart hermes-chat.service
  sudo systemctl is-active hermes-chat.service
else
  echo "No animus.service or hermes-chat.service (user or passwordless sudo). Restart manually." >&2
  echo "Hint: user units use  systemctl --user restart animus.service  (not  systemctl restart animus )." >&2
  exit 1
fi

echo "GET http://127.0.0.1:${PORT}/api/version (app semver + chat_server_rev fingerprint):"
curl -fsS "http://127.0.0.1:${PORT}/api/version" | jq '{app, chat_server_rev, chat_proxy_blocks_on_missing_hermes_api_key}' || true
echo "GET http://127.0.0.1:${PORT}/api/hermes-chat-meta (use https -k if TLS on loopback):"
curl -fsS "http://127.0.0.1:${PORT}/api/hermes-chat-meta" | jq '{rev, chat_proxy_blocks_on_missing_hermes_api_key, server_py, tls_enabled, public_url}' || true
