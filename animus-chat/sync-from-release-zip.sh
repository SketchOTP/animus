#!/usr/bin/env bash
# Patch THIS animus-chat/ directory from animus-vX.Y.Z.zip (official release layout).
# Use when you only have animus-chat/ (no installer/ next to it), e.g. a partial tree.
#
# Usage (from inside animus-chat/, or pass DEST as 2nd arg):
#   chmod +x sync-from-release-zip.sh
#   ./sync-from-release-zip.sh /path/to/animus-v1.0.4.zip
#
# With no args, searches for a zip next to VERSION on the parent dir, then common locations.
#
set -euo pipefail
CHAT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_ROOT="$(cd "${CHAT_DIR}/.." && pwd)"
ZIP_INPUT="${1:-}"
DEST="${2:-${CHAT_DIR}}"

pick_zip() {
  local base v z
  for base in "${INSTALL_ROOT}" "${INSTALL_ROOT}/../animus" "${HOME}/animus"; do
    [[ -d "${base}" ]] || continue
    base="$(cd "${base}" && pwd)"
    v="$(tr -d '[:space:]' < "${base}/VERSION" 2>/dev/null || true)"
    if [[ -n "${v}" && -f "${base}/animus-v${v}.zip" ]]; then
      echo "${base}/animus-v${v}.zip"
      return
    fi
    z="$(ls -t "${base}"/animus-v*.zip 2>/dev/null | head -1 || true)"
    if [[ -n "${z}" ]]; then
      echo "${z}"
      return
    fi
  done
  echo ""
}

if [[ -n "${ZIP_INPUT}" ]]; then
  ZIP="$(realpath "${ZIP_INPUT}")"
else
  ZIP="$(pick_zip)"
fi

if [[ ! -f "${ZIP}" ]]; then
  echo "sync-from-release-zip: no release zip found." >&2
  echo "  Pass the zip as the first argument, e.g.:" >&2
  echo "    $0 /home/you/animus/animus-v1.0.4.zip" >&2
  echo "  Searched: ${INSTALL_ROOT} , ${INSTALL_ROOT}/../animus , ${HOME}/animus (for VERSION + animus-v*.zip)" >&2
  exit 1
fi

if [[ ! -d "${DEST}" ]]; then
  echo "sync-from-release-zip: destination is not a directory: ${DEST}" >&2
  exit 1
fi

TMP="$(mktemp -d)"
cleanup() { rm -rf "${TMP}"; }
trap cleanup EXIT

unzip -oq "${ZIP}" animus-chat/server.py animus-chat/hermes_runner.py animus-chat/help_routes.py -d "${TMP}"
cp -v "${TMP}/animus-chat/server.py" "${TMP}/animus-chat/hermes_runner.py" "${TMP}/animus-chat/help_routes.py" "${DEST}/"

echo ""
echo "Patched: ${DEST}"
echo "From zip: ${ZIP}"
echo "Restart the chat server, then verify (default port 3001; change if CHAT_PORT differs):"
echo "  curl -sS \"http://127.0.0.1:3001/api/version\" | jq .app,.chat_server_rev,.chat_proxy_blocks_on_missing_hermes_api_key"
echo "  curl -sS \"http://127.0.0.1:3001/api/hermes-chat-meta\" | jq .rev,.chat_proxy_blocks_on_missing_hermes_api_key"
