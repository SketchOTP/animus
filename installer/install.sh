#!/usr/bin/env bash
set -euo pipefail
echo "========================================="
echo " ANIMUS Installer"
echo "========================================="
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
bash "${ROOT}/installer/preflight.sh"

if command -v git >/dev/null 2>&1; then
  if ! git -C "${ROOT}" remote get-url origin &>/dev/null; then
    git -C "${ROOT}" remote add origin https://github.com/SketchOTP/animus.git || true
  fi
fi

mkdir -p "${ROOT}/animus-chat/data"
if [[ ! -f "${ROOT}/animus.env" ]]; then
  cp "${ROOT}/animus.env.example" "${ROOT}/animus.env"
  echo "Created ${ROOT}/animus.env — edit HERMES_API_KEY and paths, or use the in-app wizard."
fi

echo "[ANIMUS] Installing Python deps for animus-chat (venv)…"
python3 -m venv "${ROOT}/animus-chat/.venv"
"${ROOT}/animus-chat/.venv/bin/pip" install -U pip
"${ROOT}/animus-chat/.venv/bin/pip" install -r "${ROOT}/animus-chat/requirements.txt"

echo "[ANIMUS] Installing Hermes Agent from bundle…"
if [[ -f "${ROOT}/hermes-agent/pyproject.toml" ]]; then
  "${ROOT}/animus-chat/.venv/bin/pip" install -e "${ROOT}/hermes-agent" || {
    echo "[ANIMUS] Warning: editable install failed; try manual: cd hermes-agent && pip install -e ." >&2
  }
fi

if command -v hermes >/dev/null 2>&1; then
  hermes --version || true
  mkdir -p "${ROOT}/animus-chat/data"
  hermes model --help >/dev/null 2>&1 || true
else
  echo "[ANIMUS] Note: hermes CLI not on PATH yet; open a new shell or use ${ROOT}/animus-chat/.venv/bin/hermes if installed there."
fi

if command -v cursor >/dev/null 2>&1; then
  echo "[ANIMUS] Optional: Cursor CLI detected."
else
  echo "[optional] Cursor CLI not found. If you want Cursor as a model provider, install Cursor and run: cursor login"
fi

read -r -p "Install user systemd unit animus.service? [y/N] " ans || true
if [[ "${ans:-}" =~ ^[Yy]$ ]]; then
  mkdir -p "${HOME}/.config/systemd/user"
  sed "s|%h|${HOME}|g" "${ROOT}/systemd/animus.service" >"${HOME}/.config/systemd/user/animus.service"
  systemctl --user daemon-reload || true
  echo "Enabled template at ~/.config/systemd/user/animus.service — edit paths, then: systemctl --user enable --now animus.service"
fi

echo "[ANIMUS] Starting server in background on http://127.0.0.1:3001"
export HERMES_AGENT_DIR="${ROOT}/hermes-agent"
(
  cd "${ROOT}/animus-chat"
  nohup "${ROOT}/animus-chat/.venv/bin/python" server.py >>"${ROOT}/animus-chat/data/animus-server.log" 2>&1 &
)
sleep 1
echo "Open http://localhost:3001 — the first-run wizard runs when data/config.json marks first_run."
