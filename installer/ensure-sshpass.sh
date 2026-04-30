#!/usr/bin/env bash
# Optional: install sshpass so Settings → SSH Hosts → password "Test" works (see animus-chat/ssh_routes.py).
set -euo pipefail

if [[ "${SKIP_ANIMUS_SSHPASS:-}" == "1" ]]; then
  exit 0
fi

if command -v sshpass >/dev/null 2>&1; then
  exit 0
fi

os="$(uname -s)"
if [[ "$os" != "Linux" ]] && [[ "$os" != "Darwin" ]]; then
  echo "[ANIMUS] sshpass not found — install it from your OS for SSH password tests in Settings (see INSTALL.md)."
  exit 0
fi

if [[ ! -t 0 ]]; then
  echo "[ANIMUS] sshpass missing (needed for SSH password \"Test\"). Install: Debian/Ubuntu: sudo apt install -y sshpass | Fedora: sudo dnf install -y sshpass | Arch: sudo pacman -S --noconfirm sshpass | macOS: brew install sshpass"
  echo "[ANIMUS] Re-run ./installer/install.sh in an interactive terminal to be prompted, or set SKIP_ANIMUS_SSHPASS=1 to silence."
  exit 0
fi

read -r -p "Install sshpass (SSH password tests in Settings)? [Y/n] " ans || true
if [[ "${ans:-}" =~ ^[Nn] ]]; then
  echo "[ANIMUS] Skipped sshpass — SSH key auth still works; password tests need sshpass (see INSTALL.md)."
  exit 0
fi

run_sudo() {
  if [[ "$(id -u)" -eq 0 ]]; then
    "$@"
  else
    sudo "$@"
  fi
}

install_linux() {
  if command -v apt-get >/dev/null 2>&1; then
    run_sudo apt-get update -qq
    run_sudo apt-get install -y --no-install-recommends sshpass
    return 0
  fi
  if command -v dnf >/dev/null 2>&1; then
    run_sudo dnf install -y sshpass
    return 0
  fi
  if command -v pacman >/dev/null 2>&1; then
    run_sudo pacman -S --noconfirm sshpass
    return 0
  fi
  if command -v zypper >/dev/null 2>&1; then
    run_sudo zypper install -y sshpass
    return 0
  fi
  echo "[ANIMUS] No supported package manager found — install sshpass manually."
  return 1
}

install_macos() {
  if ! command -v brew >/dev/null 2>&1; then
    echo "[ANIMUS] Homebrew not found — install sshpass manually, e.g. brew install sshpass"
    return 1
  fi
  brew install sshpass
}

if [[ "$os" == "Linux" ]]; then
  install_linux || exit 1
elif [[ "$os" == "Darwin" ]]; then
  install_macos || exit 1
fi

if command -v sshpass >/dev/null 2>&1; then
  echo "[ANIMUS] sshpass is available."
else
  echo "[ANIMUS] sshpass still not on PATH after install step — check errors above."
  exit 1
fi
