#!/usr/bin/env bash
# Install the Architect diff-gate pre-commit hook for this repository.
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
hook_src="$repo_root/scripts/git-hooks/pre-commit-architect-gate"
hook_dst="$repo_root/.git/hooks/pre-commit"

if [[ ! -f "$hook_src" ]]; then
  echo "Missing hook script: $hook_src" >&2
  exit 1
fi

install -m 755 "$hook_src" "$hook_dst"
echo "Installed architect gate hook -> $hook_dst"
