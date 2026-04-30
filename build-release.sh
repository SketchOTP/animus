#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${ROOT}"

echo "== Sanitisation grep (known bad tokens; ship tree only) =="
SCAN=(animus-chat hermes-agent installer docker systemd)
for needle in '\b5206\b' "tail1a5964" "/home/sketch/hermes/hermes-chat" "/home/sketch/hermes/hermes-agent"; do
  for d in "${SCAN[@]}"; do
    [[ -d "${ROOT}/${d}" ]] || continue
    if rg -l --hidden -g'!.git' -g'!.venv' -g'!venv' -g'!node_modules' "${needle}" "${ROOT}/${d}" >/dev/null 2>&1; then
      echo "FAIL: found ${needle} under ${d}" >&2
      rg -n --hidden "${needle}" "${ROOT}/${d}" >&2 || true
      exit 1
    fi
  done
done

echo "== User-facing product name check =="
if rg -n "Hermes Chat" animus-chat/app/static animus-chat/app 2>/dev/null; then
  echo "WARN: Hermes Chat still in app/ paths above" >&2
fi

UI_HTML="animus-chat/app/index.html"
echo "[check] No 'Hermes Chat' in primary UI (${UI_HTML})..."
if [[ -f "${ROOT}/${UI_HTML}" ]] && grep -q "Hermes Chat" "${ROOT}/${UI_HTML}"; then
  echo "FAIL: 'Hermes Chat' found in ${UI_HTML}" >&2
  exit 1
fi

echo "[check] No legacy /api/chat-models in UI..."
if [[ -f "${ROOT}/${UI_HTML}" ]] && grep -q "chat-models" "${ROOT}/${UI_HTML}"; then
  echo "FAIL: legacy chat-models still in ${UI_HTML}" >&2
  exit 1
fi

echo "[check] No legacy /api/cron/jobs in UI..."
if [[ -f "${ROOT}/${UI_HTML}" ]] && grep -q "cron/jobs" "${ROOT}/${UI_HTML}"; then
  echo "FAIL: legacy cron/jobs still in ${UI_HTML}" >&2
  exit 1
fi

echo "[check] No bare Hermes product name in Plan tab..."
if [[ -f "${ROOT}/${UI_HTML}" ]] && grep -qE "Each Hermes step|Hermes step is|Hermes chat" "${ROOT}/${UI_HTML}"; then
  echo "FAIL: bare Hermes product name in ${UI_HTML}" >&2
  exit 1
fi

echo "[check] /api/animus/check-updates endpoint exists..."
if ! grep -q "check-updates" "${ROOT}/animus-chat/server.py"; then
  echo "FAIL: check-updates endpoint not found in server.py" >&2
  exit 1
fi

echo "[check] ANIMUS_UPDATE_URL in animus.env.example..."
if ! grep -q "ANIMUS_UPDATE_URL" "${ROOT}/animus.env.example"; then
  echo "FAIL: ANIMUS_UPDATE_URL missing from animus.env.example" >&2
  exit 1
fi

echo "[check] No git fetch/pull/rev-parse/rev-list in server.py..."
if grep -qE "git fetch|git pull|git rev-parse|git rev-list" "${ROOT}/animus-chat/server.py"; then
  echo "FAIL: git commands still in server.py" >&2
  exit 1
fi

echo "[check] httpx in animus-chat/requirements.txt..."
if ! grep -q "httpx" "${ROOT}/animus-chat/requirements.txt"; then
  echo "FAIL: httpx not in animus-chat/requirements.txt" >&2
  exit 1
fi

echo "[check] No ANIMUS_GIT_ORIGIN_URL or ANIMUS_UPDATE_REPO in animus.env.example..."
if grep -qE "ANIMUS_GIT_ORIGIN_URL|ANIMUS_UPDATE_REPO" "${ROOT}/animus.env.example"; then
  echo "FAIL: old git env vars still in animus.env.example" >&2
  exit 1
fi

echo "[check] projects_dir in wizard save-config..."
if ! grep -q "projects_dir" "${ROOT}/animus-chat/setup_wizard/wizard_routes.py"; then
  echo "FAIL: projects_dir not saved by wizard" >&2
  exit 1
fi

echo "[check] subprocess exemptions in server.py..."
_bad_sub="$(grep -n "subprocess" "${ROOT}/animus-chat/server.py" 2>/dev/null | grep -v "# exempt:" || true)"
if [[ -n "${_bad_sub}" ]]; then
  echo "FAIL: raw subprocess in server.py without # exempt: comment" >&2
  echo "${_bad_sub}" >&2
  exit 1
fi

echo "[check] docs/hermes-agent-patches.md non-empty..."
if [[ ! -s "${ROOT}/docs/hermes-agent-patches.md" ]]; then
  echo "FAIL: docs/hermes-agent-patches.md missing or empty" >&2
  exit 1
fi

echo "[check] hermes-agent-patches.md has Patch sections..."
PATCH_COUNT="$(grep -c '^## Patch' "${ROOT}/docs/hermes-agent-patches.md" 2>/dev/null || echo 0)"
if [[ "${PATCH_COUNT}" -lt 1 ]]; then
  echo "FAIL: no '## Patch' sections in docs/hermes-agent-patches.md" >&2
  exit 1
fi
echo "  Found ${PATCH_COUNT} patch section(s) — OK"

echo "[check] Cursor auto model present in server..."
if ! grep -qF "cursor-agent + auto" "${ROOT}/animus-chat/server.py"; then
  echo "FAIL: Cursor catalog comment (cursor-agent + auto) missing in server.py" >&2
  exit 1
fi

echo "[check] No 'Hermes should do' in cron UI..."
if [[ -f "${ROOT}/${UI_HTML}" ]] && grep -q "Hermes should do" "${ROOT}/${UI_HTML}"; then
  echo "FAIL: 'Hermes should do' still in cron form (${UI_HTML})" >&2
  exit 1
fi

echo "[check] project_goal.md referenced in add-project flow..."
if [[ -f "${ROOT}/${UI_HTML}" ]] && ! grep -q "project_goal" "${ROOT}/${UI_HTML}"; then
  echo "FAIL: project_goal not referenced in ${UI_HTML}" >&2
  exit 1
fi

echo "[check] Slack webhook env var in animus.env.example..."
if ! grep -q "SLACK_WEBHOOK_URL" "${ROOT}/animus.env.example"; then
  echo "FAIL: SLACK_WEBHOOK_URL missing from animus.env.example" >&2
  exit 1
fi

echo "[check] SSH hosts endpoint in server.py..."
if ! grep -q "api/ssh/hosts" "${ROOT}/animus-chat/server.py"; then
  echo "FAIL: SSH hosts API not found in server.py" >&2
  exit 1
fi

echo "[check] Token usage source field..."
if ! grep -q '"source"' "${ROOT}/animus-chat/server.py"; then
  echo "FAIL: token usage source field not in server.py" >&2
  exit 1
fi

echo "[check] No Browse button in path fields..."
if grep -qE ">Browse<|>Browse </|Browse is not available" "${ROOT}/${UI_HTML}"; then
  echo "FAIL: Browse button or PWA message still present" >&2
  exit 1
fi

V="$(tr -d '[:space:]' < VERSION)"
ZIP="${ROOT}/animus-v${V}.zip"
rm -f "${ZIP}"

# Ship tree trims (v1.0 ≤55MB zip cap, no ANIMUS / core hermes runtime impact):
# - Ghost3D: optional GLB assets; PWA does not load them yet.
# - hermes-agent/tests: pytest only; not imported at runtime.
# - hermes-agent/website: docs site source; not used by `hermes` CLI or ANIMUS chat.
# - hermes-agent/.env: provider template only; buyers should use checked-in examples / wizard, not raw .env paths.
# - *.flock / hermes-agent/.envrc: local lock/dev-shell files, not buyer runtime.
# - hermes-agent/scripts/whatsapp-bridge/node_modules: WhatsApp gateway bridge; reinstall with npm when needed.
# - animus-update-server/: seller-only update manifest app; never ship to buyers.
# - ./scripts/: repo-root dev/smoke checklists only (not hermes-agent/.../scripts/).
# - seller-private/: seller-local tokens/notes; gitignored except README; never ship to buyers.
# Internal monorepo continuity (not for buyers — clone the repo to develop ANIMUS):
# - project_*.md, repo_map.md, AGENTS.md, CLAUDE.md, .cursorrules, .cursor/, setup_repo.md,
#   animus-chat copies of repo_map / project_history / setup_repo; hermes-agent/AGENTS.md (upstream dev doc).
zip -qr "${ZIP}" . \
  -x"*.git/*" \
  -x"*__pycache__/*" \
  -x"*.pyc" \
  -x"*.flock" \
  -x"./animus.env" \
  -x"./animus-chat/animus.env" \
  -x"./animus-chat/hermes-chat.env" \
  -x"./hermes-agent/.env" \
  -x"./hermes-agent/.envrc" \
  -x"./data/*" \
  -x"./animus-chat/data/*" \
  -x"./animus-chat/.venv/*" \
  -x"./hermes-agent/venv/*" \
  -x"./hermes-agent/node_modules/*" \
  -x"./hermes-agent/web/node_modules/*" \
  -x"./hermes-agent/.git/*" \
  -x"./Ghost3D/*" \
  -x"./hermes-agent/tests/*" \
  -x"./hermes-agent/website/*" \
  -x"./hermes-agent/scripts/whatsapp-bridge/node_modules/*" \
  -x"./project_goal.md" \
  -x"./project_status.md" \
  -x"./project_history.md" \
  -x"./project_knowledge.md" \
  -x"./repo_map.md" \
  -x"./AGENTS.md" \
  -x"./CLAUDE.md" \
  -x"./.cursorrules" \
  -x"./.cursor/*" \
  -x"./setup_repo.md" \
  -x"./animus-chat/repo_map.md" \
  -x"./animus-chat/project_history.md" \
  -x"./animus-chat/setup_repo.md" \
  -x"./hermes-agent/.cursor/*" \
  -x"./hermes-agent/AGENTS.md" \
  -x"./animus-update-server/*" \
  -x"./scripts/*" \
  -x"./seller-private/*" \
  -x"./animus-v*.zip"

SZ="$(du -sm "${ZIP}" | awk '{print $1}')"
echo "Created ${ZIP} (${SZ} MB)"
if [[ "${SZ}" -gt 55 ]]; then
  echo "FAIL: zip is over 55MB (v1.0 acceptance cap in project_goal.md). Add more -x excludes or split the ship tree." >&2
  exit 1
fi
echo "  Zip size OK (≤55MB v1.0 cap)"

echo "== Zip leak check (env + local data) =="
if unzip -l "${ZIP}" | grep -E '[[:space:]]animus\.env$' | grep -Fv example | grep -q .; then
  echo "FAIL: raw animus.env path in zip (use animus.env.example only)" >&2
  unzip -l "${ZIP}" | grep -E '[[:space:]]animus\.env$' | grep -Fv example >&2
  exit 1
fi
if unzip -l "${ZIP}" | grep -E '[[:space:]]hermes-chat\.env$' | grep -Fv example | grep -q .; then
  echo "FAIL: raw hermes-chat.env path in zip" >&2
  exit 1
fi
if unzip -l "${ZIP}" | grep -E '[[:space:]]hermes-agent/\.env$' | grep -q .; then
  echo "FAIL: raw hermes-agent/.env path in zip" >&2
  exit 1
fi
if unzip -l "${ZIP}" | grep -q 'animus-chat/data/'; then
  echo "FAIL: animus-chat/data/ present in zip" >&2
  exit 1
fi
if unzip -l "${ZIP}" | grep -q 'animus-update-server/'; then
  echo "FAIL: animus-update-server/ present in zip — remove it" >&2
  exit 1
fi
if unzip -l "${ZIP}" | grep -q '\.flock$'; then
  echo "FAIL: local .flock lock file present in zip" >&2
  exit 1
fi
if unzip -l "${ZIP}" | grep -q 'seller-private/'; then
  echo "FAIL: seller-private/ present in zip — remove it" >&2
  exit 1
fi
echo "  animus-update-server/ not in zip — OK"
echo "  No raw env or animus-chat/data/ in zip — OK"

cat <<EOF
ANIMUS release checklist:
[ ] seller-private/ is NOT in the zip (local tokens stay on your machine only)
[ ] animus.env is NOT in the zip
[ ] data/ directory is NOT in the zip
[ ] START_HERE.txt and docs/GUMROAD.md are in the repo (included in zip for buyers/sellers)
[ ] No personal API keys in any file
[ ] No personal hostnames or IPs in any file
[ ] No Hermes Chat in user-facing strings under animus-chat/app/
[ ] installer/install.sh is executable (chmod +x)
[ ] README.md references correct version
[ ] VERSION file updated
[ ] Docker build passes on a clean host
EOF
