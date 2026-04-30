#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ ! -f "${ROOT}/animus.env" ]] && [[ -f "${ROOT}/animus.env.example" ]]; then
  cp "${ROOT}/animus.env.example" "${ROOT}/animus.env"
  echo "Created ${ROOT}/animus.env from animus.env.example (same as install.sh — edit keys/paths before relying on it)."
fi
if [[ -f "${ROOT}/animus.env" ]] && [[ -f "${ROOT}/installer/merge-hermes-gateway-auth.py" ]]; then
  python3 "${ROOT}/installer/merge-hermes-gateway-auth.py" "${ROOT}/animus.env" || true
fi
echo "ANIMUS preflight"
ok=0
fail=0
check() {
  local name="$1" status="$2"
  if [[ "$status" == "ok" ]]; then
    printf "  [ok]   %s\n" "$name"
    ok=$((ok + 1))
  else
    printf "  [FAIL] %s\n" "$name"
    fail=$((fail + 1))
  fi
}

ver="$(python3 --version 2>&1 || true)"
if python3 -c 'import sys; sys.exit(0 if sys.version_info[:2] >= (3, 10) else 1)' 2>/dev/null; then
  check "Python 3.10+" "ok"
else
  check "Python 3.10+ (got ${ver})" "fail"
fi

command -v pip3 >/dev/null 2>&1 && check "pip3" "ok" || check "pip3" "fail"
command -v git >/dev/null 2>&1 && check "git (optional)" "ok" || check "git (optional)" "ok"

if [[ "$(uname -s)" == "Linux" ]] && ! command -v sshpass >/dev/null 2>&1; then
  printf "  [note] sshpass not on PATH — SSH password tests in Settings need it; ./installer/install.sh can install (or sudo apt install -y sshpass).\n"
fi

if command -v ss >/dev/null 2>&1; then
  if ss -lntp 2>/dev/null | grep -q ':3001 '; then
    check "port 3001 free (ANIMUS default)" "fail"
  else
    check "port 3001 free (ANIMUS default)" "ok"
  fi
else
  check "port 3001 check (ss missing — skipped)" "ok"
fi

df_m="$(df -Pm . 2>/dev/null | awk 'NR==2 {print $4}')"
if [[ "${df_m:-0}" -ge 500 ]] 2>/dev/null; then
  check "500MB+ free on install volume" "ok"
else
  check "500MB+ free (best-effort)" "ok"
fi

echo "Summary: ${ok} passed, ${fail} failed."
[[ "$fail" -eq 0 ]]
