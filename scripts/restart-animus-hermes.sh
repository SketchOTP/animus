#!/usr/bin/env bash
# Hardened restart for both Hermes gateway + ANIMUS chat.
# Usage: scripts/restart-animus-hermes.sh [--no-daemon-reload]
set -euo pipefail

ANIMUS_UNIT="${ANIMUS_SYSTEMD_UNIT:-animus.service}"
GATEWAY_UNIT="${HERMES_GATEWAY_SYSTEMD_UNIT:-hermes-gateway.service}"
ANIMUS_URL="${ANIMUS_HEALTHCHECK_URL:-http://127.0.0.1:3001/api/version}"
GATEWAY_URL="${HERMES_HEALTHCHECK_URL:-http://127.0.0.1:8642/health}"
DO_DAEMON_RELOAD=1

if [[ "${1:-}" == "--no-daemon-reload" ]]; then
  DO_DAEMON_RELOAD=0
fi

log() {
  echo "[restart-stack] $*"
}

fail_with_status() {
  local unit="$1"
  log "FAILED: ${unit} is not active after restart"
  systemctl --user status "${unit}" --no-pager -n 40 || true
  exit 1
}

restart_and_wait_active() {
  local unit="$1"
  log "restarting ${unit}"
  systemctl --user restart "${unit}"
  for _ in {1..15}; do
    if systemctl --user is-active --quiet "${unit}"; then
      log "${unit}: active"
      return 0
    fi
    sleep 1
  done
  fail_with_status "${unit}"
}

wait_http_ok() {
  local name="$1"
  local url="$2"
  for _ in {1..15}; do
    if curl -fsS "${url}" >/dev/null 2>&1; then
      log "${name}: health OK (${url})"
      return 0
    fi
    sleep 1
  done
  log "FAILED: ${name} health check did not recover (${url})"
  exit 1
}

main() {
  if [[ "${DO_DAEMON_RELOAD}" -eq 1 ]]; then
    log "running systemctl --user daemon-reload"
    systemctl --user daemon-reload
  fi

  # Restart backend first, then chat proxy.
  restart_and_wait_active "${GATEWAY_UNIT}"
  restart_and_wait_active "${ANIMUS_UNIT}"

  wait_http_ok "gateway" "${GATEWAY_URL}"
  wait_http_ok "animus" "${ANIMUS_URL}"

  log "stack restart complete"
  log "quick checks:"
  echo "  - systemctl --user status ${GATEWAY_UNIT} --no-pager"
  echo "  - systemctl --user status ${ANIMUS_UNIT} --no-pager"
  echo "  - curl -fsS ${GATEWAY_URL}"
  echo "  - curl -fsS ${ANIMUS_URL}"
}

main "$@"
