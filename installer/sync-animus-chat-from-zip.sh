#!/usr/bin/env bash
# Thin wrapper — canonical logic lives in animus-chat/sync-from-release-zip.sh
# so installs that only contain animus-chat/ can still run the same script.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
exec "${ROOT}/animus-chat/sync-from-release-zip.sh" "$@"
