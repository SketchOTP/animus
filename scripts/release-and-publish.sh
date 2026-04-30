#!/usr/bin/env bash
# Copy the release zip into sibling animus-site/releases/ and deploy Production on Vercel.
# After this finishes, buyers can use the static URL under /releases/ OR run publish-animus-manifest.sh
# if you only needed deploy without changing the manifest download_url.
#
# Usage (from animus repo root, after ./build-release.sh):
#   ./scripts/release-and-publish.sh
#
# Override site directory:
#   ANIMUS_SITE_DIR=/path/to/animus-site ./scripts/release-and-publish.sh
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VER="$(tr -d '[:space:]' < "${ROOT}/VERSION")"
ZIP="animus-v${VER}.zip"
DEFAULT_SITE="$(cd "${ROOT}/.." && pwd)/animus-site"
SITE="${ANIMUS_SITE_DIR:-$DEFAULT_SITE}"

if [[ ! -f "${ROOT}/${ZIP}" ]]; then
  echo "Missing ${ROOT}/${ZIP} — run ./build-release.sh first." >&2
  exit 1
fi
if [[ ! -d "${SITE}" ]]; then
  echo "animus-site not found at ${SITE}. Clone it or set ANIMUS_SITE_DIR." >&2
  exit 1
fi

mkdir -p "${SITE}/releases"
cp -f "${ROOT}/${ZIP}" "${SITE}/releases/${ZIP}"
echo "[release-and-publish] Copied ${ZIP} → ${SITE}/releases/"

(
  cd "${SITE}"
  vercel --prod ${VERCEL_ARGS:-}
)

echo "[release-and-publish] Vercel deploy finished."
echo "Publish / refresh manifest (if needed):"
echo "  cd ${ROOT} && ./scripts/publish-animus-manifest.sh"
