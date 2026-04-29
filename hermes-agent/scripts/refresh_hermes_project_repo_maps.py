#!/usr/bin/env python3
"""Refresh repo_map.md for Hermes Chat projects (paths in projects.json).

Run periodically (cron or systemd timer) so agents read an up-to-date index
instead of re-listing the tree in chat.

Requires the same CHAT_DATA_DIR / ~/.hermes/.env as Hermes Chat.

Examples:
  python scripts/refresh_hermes_project_repo_maps.py
  python scripts/refresh_hermes_project_repo_maps.py --missing-only
  hermes project repo-maps-refresh-all
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def main() -> int:
    from agent.project_workspace import refresh_all_hermes_chat_repo_maps

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--missing-only",
        action="store_true",
        help="Ensure project_history.md and repo_map.md in each project root; never overwrite existing repo_map.md",
    )
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="List targets without writing",
    )
    args = ap.parse_args()
    rows = refresh_all_hermes_chat_repo_maps(
        missing_only=args.missing_only,
        dry_run=args.dry_run,
    )
    for row in rows:
        print(row)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
