#!/usr/bin/env bash
# Hourly watchdog: ensure ANIMUS + Hermes gateway are up.
set -euo pipefail

ANIMUS_UNIT="${ANIMUS_SYSTEMD_UNIT:-animus.service}"
GATEWAY_UNIT="${HERMES_GATEWAY_SYSTEMD_UNIT:-hermes-gateway.service}"
ANIMUS_URL="${ANIMUS_HEALTHCHECK_URL:-http://127.0.0.1:3001/api/version}"
GATEWAY_URL="${HERMES_HEALTHCHECK_URL:-http://127.0.0.1:8642/v1/models}"

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ANIMUS_ENV="${ROOT}/animus.env"
HERMES_ENV="${ROOT}/.hermes/.env"

log() {
  echo "[watchdog] $*"
}

_env_get() {
  local key="$1"
  local file="$2"
  [[ -f "$file" ]] || return 1
  local line
  line="$(rg -n "^${key}=" "$file" | head -n 1 || true)"
  [[ -n "$line" ]] || return 1
  line="${line#*:}"
  line="${line#${key}=}"
  printf "%s" "$line"
}

gateway_auth_header() {
  local tok=""
  tok="$(_env_get "HERMES_API_KEY" "$ANIMUS_ENV" || true)"
  if [[ -z "$tok" ]]; then
    tok="$(_env_get "API_SERVER_KEY" "$HERMES_ENV" || true)"
  fi
  if [[ -n "$tok" ]]; then
    printf "Authorization: Bearer %s" "$tok"
    return 0
  fi
  return 1
}

check_or_restart_service() {
  local unit="$1"
  local label="$2"
  if systemctl --user is-active --quiet "$unit"; then
    log "${label}: active"
    return 0
  fi

  log "${label}: inactive; restarting ${unit}"
  systemctl --user restart "$unit"
  sleep 2

  if systemctl --user is-active --quiet "$unit"; then
    log "${label}: restart succeeded"
    return 0
  fi

  log "${label}: restart failed"
  systemctl --user status "$unit" --no-pager || true
  return 1
}

wait_http_ok() {
  local label="$1"
  local url="$2"
  local header="${3:-}"
  local i
  for i in {1..8}; do
    if [[ -n "$header" ]]; then
      if curl -fsS -H "$header" "$url" >/dev/null; then
        log "${label}: HTTP check OK (${url})"
        return 0
      fi
    else
      if curl -fsS "$url" >/dev/null; then
        log "${label}: HTTP check OK (${url})"
        return 0
      fi
    fi
    sleep 2
  done
  log "${label}: HTTP check FAILED (${url})"
  return 1
}

main() {
  check_or_restart_service "$GATEWAY_UNIT" "gateway"
  check_or_restart_service "$ANIMUS_UNIT" "animus"

  local gw_header=""
  gw_header="$(gateway_auth_header || true)"

  wait_http_ok "gateway" "$GATEWAY_URL" "$gw_header"
  wait_http_ok "animus" "$ANIMUS_URL"
  log "all checks passed"
}

main "$@"
