#!/usr/bin/env bash
# Point user systemd at THIS monorepo (~/…/animus) so ANIMUS is not started from
# an old unzip path (e.g. animus-fresh-install). Safe to re-run.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
UNIT_SRC="${ROOT}/systemd/animus.service"
UNIT_DST="${HOME}/.config/systemd/user/animus.service"
ENV_DST="${ROOT}/animus.env"
ENV_EX="${ROOT}/animus.env.example"
AGENT="${ROOT}/hermes-agent"

if [[ ! -f "${UNIT_SRC}" ]]; then
  echo "Missing ${UNIT_SRC}" >&2
  exit 1
fi
if [[ ! -d "${AGENT}" ]]; then
  echo "Missing hermes-agent at ${AGENT}" >&2
  exit 1
fi

mkdir -p "${HOME}/.config/systemd/user"
cp -f "${UNIT_SRC}" "${UNIT_DST}"
echo "Installed ${UNIT_DST}"

# systemd EnvironmentFile does not expand ${HOME} the way a login shell does;
# use an absolute path so Hermes profile/cron paths resolve correctly.
HERMES_HOME_ABS="${HOME}/.hermes/profiles/default"

if [[ ! -f "${ENV_DST}" ]]; then
  if [[ ! -f "${ENV_EX}" ]]; then
    echo "Missing ${ENV_EX}; cannot create animus.env" >&2
    exit 1
  fi
  cp "${ENV_EX}" "${ENV_DST}"
  sed -i "s|^HERMES_AGENT_DIR=.*|HERMES_AGENT_DIR=${AGENT}|" "${ENV_DST}"
  sed -i "s|^HERMES_HOME=.*|HERMES_HOME=${HERMES_HOME_ABS}|" "${ENV_DST}"
  # INSTALL_DIR is referenced in the example; set explicitly for dotenv/skills.
  if ! grep -qE '^[[:space:]]*INSTALL_DIR=' "${ENV_DST}"; then
    printf '\n# Monorepo root (set by scripts/sync-dev-systemd.sh)\nINSTALL_DIR=%s\n' "${ROOT}" >>"${ENV_DST}"
  fi
  if ! grep -qE '^[[:space:]]*HERMES_CHAT_SYSTEMD_UNIT=' "${ENV_DST}"; then
    printf 'HERMES_CHAT_SYSTEMD_UNIT=animus.service\n' >>"${ENV_DST}"
  fi
  echo "Created ${ENV_DST} from example (edit HERMES_API_KEY and providers)."
else
  if ! grep -qF "HERMES_AGENT_DIR=${AGENT}" "${ENV_DST}" 2>/dev/null; then
    if grep -qE '^[[:space:]]*HERMES_AGENT_DIR=' "${ENV_DST}"; then
      sed -i "s|^HERMES_AGENT_DIR=.*|HERMES_AGENT_DIR=${AGENT}|" "${ENV_DST}"
      echo "Updated HERMES_AGENT_DIR in ${ENV_DST} -> ${AGENT}"
    else
      printf '\nHERMES_AGENT_DIR=%s\n' "${AGENT}" >>"${ENV_DST}"
      echo "Appended HERMES_AGENT_DIR to ${ENV_DST}"
    fi
  fi
  if ! grep -qE '^[[:space:]]*INSTALL_DIR=' "${ENV_DST}"; then
    printf '\nINSTALL_DIR=%s\n' "${ROOT}" >>"${ENV_DST}"
    echo "Appended INSTALL_DIR to ${ENV_DST}"
  fi
  # Fix broken HERMES_HOME if env still uses ${HOME} (not expanded under systemd).
  if grep -qE '^HERMES_HOME=.*\$\{HOME\}' "${ENV_DST}"; then
    sed -i "s|^HERMES_HOME=.*|HERMES_HOME=${HERMES_HOME_ABS}|" "${ENV_DST}"
    echo "Normalized HERMES_HOME to ${HERMES_HOME_ABS} (systemd-safe path)."
  fi
fi

# User-level gateway: always use THIS repo's hermes-agent (no second checkout).
GATE_DST="${HOME}/.config/systemd/user/hermes-gateway.service"
PYTHON_GATE="${AGENT}/venv/bin/python"
if [[ -x "${PYTHON_GATE}" ]]; then
  NODE_PART=""
  if command -v node >/dev/null 2>&1; then
    NODE_PART="$(dirname "$(command -v node)"):"
  fi
  PATH_GATE="${AGENT}/venv/bin:${AGENT}/node_modules/.bin:${NODE_PART}${HOME}/.local/bin:${HOME}/.cargo/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
  CHAT_DATA_ABS="${ROOT}/animus-chat/data"
  cat >"${GATE_DST}" <<EOF
[Unit]
Description=Hermes Agent Gateway (ANIMUS monorepo hermes-agent)
After=network.target
StartLimitIntervalSec=0

[Service]
Type=simple
ExecStart=${PYTHON_GATE} -m hermes_cli.main gateway run --replace
WorkingDirectory=${AGENT}
Environment="PATH=${PATH_GATE}"
Environment="VIRTUAL_ENV=${AGENT}/venv"
Environment="HERMES_HOME=${HERMES_HOME_ABS}"
Environment="CHAT_DATA_DIR=${CHAT_DATA_ABS}"
Restart=on-failure
RestartSec=30
RestartForceExitStatus=75
KillMode=mixed
KillSignal=SIGTERM
ExecReload=/bin/kill -USR1 \$MAINPID
TimeoutStopSec=60
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=default.target
EOF
  echo "Installed ${GATE_DST} (hermes-agent + CHAT_DATA_DIR under this monorepo)."
else
  echo "Skipping ${GATE_DST}: no executable at ${PYTHON_GATE} (cd hermes-agent && uv sync or pip install -e . per INSTALL)."
fi

systemctl --user daemon-reload

# CLI on PATH: animus start | stop | restart | status
ANIMUS_CLI_SRC="${ROOT}/scripts/animus"
LOCAL_BIN="${HOME}/.local/bin"
if [[ -f "${ANIMUS_CLI_SRC}" ]]; then
  chmod +x "${ANIMUS_CLI_SRC}" 2>/dev/null || true
  mkdir -p "${LOCAL_BIN}"
  ln -sf "${ANIMUS_CLI_SRC}" "${LOCAL_BIN}/animus"
  echo "CLI: ${LOCAL_BIN}/animus → start | stop | restart | status"
  case ":${PATH}:" in
    *":${LOCAL_BIN}:"*) ;;
    *) echo "Tip: add ${LOCAL_BIN} to PATH if \`animus\` is not found (e.g. export PATH=\"\${HOME}/.local/bin:\${PATH}\")." >&2 ;;
  esac
fi

if command -v ss >/dev/null 2>&1; then
  if ss -tlnp 2>/dev/null | grep -qE ':3001\s'; then
    echo "" >&2
    echo "WARNING: port 3001 is already in use. animus.service will fail until you stop the other process." >&2
    ss -tlnp 2>/dev/null | grep -E ':3001\s' || true
    echo "Example: stop a manual \`python server.py\` from another directory, or: systemctl --user stop animus.service" >&2
    echo "" >&2
  fi
fi

echo "Run:  animus restart   (or: systemctl --user restart animus.service)"
echo "Then: curl -fsS http://127.0.0.1:3001/api/hermes-chat-meta | jq '.rev,.server_py'"
if [[ -x "${PYTHON_GATE}" ]]; then
  echo "Gateway: systemctl --user restart hermes-gateway.service"
  echo "Then:    curl -fsS -H \"Authorization: Bearer \$(grep -m1 '^HERMES_API_KEY=' ${ENV_DST} | cut -d= -f2-)\" http://127.0.0.1:8642/v1/models | head -c 200"
fi
