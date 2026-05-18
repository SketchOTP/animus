#!/usr/bin/env bash
# Re-apply ANIMUS Hermes customizations onto an upstream v0.14 tree.
# Run from repo root after `hermes-agent/` contains v2026.5.16 (git archive).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"
UPSTREAM_TAG="${UPSTREAM_TAG:-v2026.5.16}"
ANIMUS_REF="${ANIMUS_REF:-main}"

merge_file() {
  local rel="$1"
  local up_path="${2:-$rel}"
  git show "${UPSTREAM_TAG}:${up_path}" > /tmp/hermes-up.py
  git show "${ANIMUS_REF}:hermes-agent/${rel}" > /tmp/hermes-an.py
  cp "hermes-agent/${rel}" /tmp/hermes-base.py
  git merge-file /tmp/hermes-base.py /tmp/hermes-up.py /tmp/hermes-an.py
  cp /tmp/hermes-base.py "hermes-agent/${rel}"
  echo "[ok] merged ${rel}"
}

git checkout "${ANIMUS_REF}" -- hermes-agent/animus hermes-agent/tests/animus
git checkout "${ANIMUS_REF}" -- \
  hermes-agent/hermes_cli/codex_device_oauth.py \
  hermes-agent/hermes_cli/project_workspace_cmd.py \
  hermes-agent/tests/hermes_cli/test_provider_registry_external_shims.py

merge_file gateway/platforms/api_server.py gateway/platforms/api_server.py
merge_file hermes_cli/providers.py hermes_cli/providers.py
merge_file tools/transcription_tools.py tools/transcription_tools.py
merge_file hermes_cli/web_server.py hermes_cli/web_server.py
merge_file hermes_cli/main.py hermes_cli/main.py

echo "Done. Run: cd hermes-agent && ./scripts/run_tests.sh tests/hermes_cli/test_provider_registry_external_shims.py tests/animus/test_context_protocol.py -q"
