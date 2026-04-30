#!/usr/bin/env bash
# Publish a release manifest to animus-site (Vercel Redis).
#
# Prerequisites:
#   1. ./build-release.sh already produced animus-v$(cat VERSION | tr -d '[:space:]').zip
#   2. Upload that zip to a public HTTPS URL (same host/path pattern you used before).
#
# Usage:
#   export ADMIN_TOKEN='…'   # Vercel project → Settings → ADMIN_TOKEN
#   optional: export DOWNLOAD_URL (defaults to Vercel static URL below)
#   optional: export ANIMUS_RELEASE_NOTES='Bugfix: skills list seeds on first launch'
#   optional: export ANIMUS_PUBLISH_URL='https://animusai.vercel.app/api/admin/publish'
#   ./scripts/publish-animus-manifest.sh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
V="$(tr -d '[:space:]' < "$ROOT/VERSION")"
# Defaults: customer-facing hostname (must be a Vercel alias for this project’s Production).
PUBLISH_URL="${ANIMUS_PUBLISH_URL:-https://animusai.vercel.app/api/admin/publish}"
BASE="${ANIMUS_SITE_BASE:-https://animusai.vercel.app}"
DOWNLOAD_URL="${DOWNLOAD_URL:-${BASE}/releases/animus-v${V}.zip}"
NOTES="${ANIMUS_RELEASE_NOTES:-ANIMUS v${V}}"
if [[ -z "${ADMIN_TOKEN:-}" ]]; then
  echo "error: set ADMIN_TOKEN (Vercel → animus-site → Settings → Environment variables → Production)" >&2
  echo "  Or pull Production secrets: cd sibling animus-site/ && vercel env pull .env.production.local --environment production --yes" >&2
  echo "    then: set -a && source .env.production.local && set +a && re-run this script from animus/" >&2
  exit 1
fi
BODY="$(python3 -c "import json,sys; print(json.dumps({'version':sys.argv[1],'download_url':sys.argv[2],'notes':sys.argv[3]}))" "$V" "$DOWNLOAD_URL" "$NOTES")"
curl -sS -X POST "$PUBLISH_URL" \
  -H "x-admin-token: $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d "$BODY" | python3 -m json.tool
