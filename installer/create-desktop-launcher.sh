#!/usr/bin/env bash
# Create a desktop / menu launcher that opens ANIMUS in the default browser.
# Same origin + same browser profile = same post-setup data (localStorage + server config).
#
# Skips: Docker, CI, SKIP_ANIMUS_DESKTOP_LAUNCHER=1, non Linux/macOS, Linux without DISPLAY/WAYLAND.
#
# Usage: bash installer/create-desktop-launcher.sh
# Optional env: REPO_ROOT=/path/to/animus (defaults to parent of this script's directory)

set -euo pipefail

if [[ "${SKIP_ANIMUS_DESKTOP_LAUNCHER:-}" == "1" ]]; then
  echo "[ANIMUS] Desktop launcher skipped (SKIP_ANIMUS_DESKTOP_LAUNCHER=1)."
  exit 0
fi
if [[ -f /.dockerenv ]]; then
  echo "[ANIMUS] Desktop launcher skipped (running inside Docker)."
  exit 0
fi
if [[ "${CI:-}" == "true" ]] || [[ "${GITHUB_ACTIONS:-}" == "true" ]]; then
  echo "[ANIMUS] Desktop launcher skipped (CI)."
  exit 0
fi

ROOT="${REPO_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
ENV_F="${ROOT}/animus.env"

OS="$(uname -s)"
if [[ "$OS" == "Linux" ]]; then
  if [[ -z "${DISPLAY:-}" && -z "${WAYLAND_DISPLAY:-}" ]]; then
    echo "[ANIMUS] Desktop launcher skipped (no DISPLAY or WAYLAND_DISPLAY — headless)."
    exit 0
  fi
elif [[ "$OS" == "Darwin" ]]; then
  :
else
  echo "[ANIMUS] Desktop launcher skipped (OS=${OS}; only Linux and macOS)."
  exit 0
fi

CHAT_HOST="127.0.0.1"
CHAT_PORT="3001"
PUB=""
if [[ -f "$ENV_F" ]]; then
  while IFS= read -r line || [[ -n "$line" ]]; do
    [[ "$line" =~ ^[[:space:]]*# ]] && continue
    [[ "$line" =~ ^[[:space:]]*$ ]] && continue
    if [[ "$line" =~ ^[[:space:]]*HERMES_CHAT_PUBLIC_URL= ]]; then
      val="${line#*=}"
      val="${val%\"}"; val="${val#\"}"; val="${val%\'}"; val="${val#\'}"
      PUB="$(echo "$val" | xargs)"
    elif [[ "$line" =~ ^[[:space:]]*CHAT_HOST= ]]; then
      val="${line#*=}"
      CHAT_HOST="$(echo "$val" | xargs)"
    elif [[ "$line" =~ ^[[:space:]]*CHAT_PORT= ]]; then
      val="${line#*=}"
      CHAT_PORT="$(echo "$val" | xargs)"
    fi
  done <"$ENV_F"
fi

if [[ -n "$PUB" ]]; then
  LAUNCH_URL="${PUB%/}"
else
  # :: and 0.0.0.0 are bind addresses, not valid in a browser URL host field
  LAUNCH_HOST="$CHAT_HOST"
  if [[ "$CHAT_HOST" == "::" || "$CHAT_HOST" == "0.0.0.0" ]]; then
    LAUNCH_HOST="127.0.0.1"
  fi
  LAUNCH_URL="http://${LAUNCH_HOST}:${CHAT_PORT}"
fi
LAUNCH_URL="${LAUNCH_URL%/}/"

ICON_PATH=""
for c in "${ROOT}/animus-chat/app/ghostonlyicon.png" "${ROOT}/animus-chat/app/icon-192.png" "${ROOT}/ANIMUSLOGOICON.png"; do
  if [[ -f "$c" ]]; then
    ICON_PATH="$c"
    break
  fi
done

xml_escape_url() {
  # Minimal XML/plist escaping for URL string
  local s="$1"
  s="${s//&/&amp;}"
  s="${s//</&lt;}"
  s="${s//>/&gt;}"
  printf '%s' "$s"
}

write_webloc() {
  local out="$1"
  local u
  u="$(xml_escape_url "$LAUNCH_URL")"
  cat >"$out" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>URL</key>
  <string>${u}</string>
</dict>
</plist>
EOF
  chmod 644 "$out"
}

write_linux_desktop() {
  local out="$1"
  local q
  q="$(printf '%q' "$LAUNCH_URL")"
  local icon_line="Icon=applications-internet"
  if [[ -n "$ICON_PATH" ]]; then
    icon_line="Icon=${ICON_PATH}"
  fi
  umask 022
  {
    echo "[Desktop Entry]"
    echo "Version=1.0"
    echo "Type=Application"
    echo "Name=ANIMUS"
    echo "Comment=Open ANIMUS in your default browser (same session as visiting this URL)"
    echo "Exec=xdg-open ${q}"
    echo "$icon_line"
    echo "Terminal=false"
    echo "Categories=Network;InstantMessaging;"
    echo "StartupNotify=true"
  } >"$out"
  chmod 644 "$out"
}

DESKTOP_DIR=""
if [[ "$OS" == "Linux" ]] && command -v xdg-user-dir >/dev/null 2>&1; then
  DESKTOP_DIR="$(xdg-user-dir DESKTOP 2>/dev/null || true)"
fi
if [[ -z "${DESKTOP_DIR:-}" || ! -d "$DESKTOP_DIR" ]]; then
  DESKTOP_DIR="${HOME}/Desktop"
fi

APP_DIR="${HOME}/.local/share/applications"
mkdir -p "$APP_DIR"

if [[ "$OS" == "Linux" ]]; then
  write_linux_desktop "${APP_DIR}/animus.desktop"
  echo "[ANIMUS] Application menu launcher: ${APP_DIR}/animus.desktop"
  if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "${HOME}/.local/share/applications" 2>/dev/null || true
  fi
  if [[ -d "$DESKTOP_DIR" ]]; then
    write_linux_desktop "${DESKTOP_DIR}/animus.desktop"
    echo "[ANIMUS] Desktop shortcut: ${DESKTOP_DIR}/animus.desktop"
  else
    echo "[ANIMUS] No Desktop folder found; menu launcher only."
  fi
elif [[ "$OS" == "Darwin" ]]; then
  if [[ -d "$DESKTOP_DIR" ]]; then
    write_webloc "${DESKTOP_DIR}/ANIMUS.webloc"
    echo "[ANIMUS] Desktop shortcut: ${DESKTOP_DIR}/ANIMUS.webloc"
  else
    echo "[ANIMUS] No Desktop folder; skipping."
  fi
fi

echo "[ANIMUS] Opens: ${LAUNCH_URL}"
