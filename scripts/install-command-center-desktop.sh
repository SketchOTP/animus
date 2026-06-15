#!/usr/bin/env bash
# Install Animus Command Center desktop shortcut + application menu entry.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LAUNCHER="${ROOT}/scripts/command-center-launch.sh"
ICON="${ROOT}/animus-command-center/app/ghostonlyicon.png"
APP_DIR="${HOME}/.local/share/applications"
DESKTOP_DIR="${HOME}/Desktop"

if [[ ! -x "${LAUNCHER}" ]]; then
  chmod +x "${LAUNCHER}"
fi

if [[ ! -f "${ICON}" ]]; then
  echo "Missing icon: ${ICON}" >&2
  exit 1
fi

DESKTOP_FILE="${APP_DIR}/animus-command-center.desktop"
mkdir -p "${APP_DIR}"

cat >"${DESKTOP_FILE}" <<EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Animus Command Center
GenericName=Governance dashboard
Comment=Start Animus Command Center and open it in your browser
Path=${ROOT}
TryExec=${LAUNCHER}
Exec=${LAUNCHER}
Icon=${ICON}
Terminal=false
Categories=Development;Network;
StartupNotify=true
Keywords=animus;governance;command;center;goal;runner;
EOF
chmod 644 "${DESKTOP_FILE}"

if [[ -d "${DESKTOP_DIR}" ]]; then
  cp "${DESKTOP_FILE}" "${DESKTOP_DIR}/Animus Command Center.desktop"
  chmod 644 "${DESKTOP_DIR}/Animus Command Center.desktop"
  if command -v gio >/dev/null 2>&1; then
    gio set "${DESKTOP_DIR}/Animus Command Center.desktop" metadata::trusted true 2>/dev/null || true
  fi
  echo "Desktop shortcut: ${DESKTOP_DIR}/Animus Command Center.desktop"
fi

if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database "${APP_DIR}" 2>/dev/null || true
fi

echo "Application menu entry: ${DESKTOP_FILE}"
echo "Icon: ${ICON}"
