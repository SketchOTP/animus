"""Handlers for ``hermes project …``."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def project_command(args: argparse.Namespace) -> None:
    from agent.project_workspace import (
        append_project_history_line,
        ensure_workspace_files,
        normalize_project_root,
        refresh_all_hermes_chat_repo_maps,
        refresh_repo_map,
        read_workspace_file,
        write_workspace_file,
    )

    action = getattr(args, "project_action", None) or ""
    if action == "init":
        root = Path(getattr(args, "path", ""))
        skip_map = bool(getattr(args, "skip_repo_map", False))
        info = ensure_workspace_files(
            root,
            generate_repo_map_if_missing=not skip_map,
        )
        print(info)
        return
    if action == "history-append":
        root = Path(getattr(args, "path", ""))
        summary = getattr(args, "summary", "") or ""
        source = getattr(args, "source", "") or ""
        line = append_project_history_line(root, summary, source=source)
        print(line)
        return
    if action == "repo-map-refresh":
        root = Path(getattr(args, "path", ""))
        info = refresh_repo_map(root)
        print(info)
        return
    if action == "repo-maps-refresh-all":
        rows = refresh_all_hermes_chat_repo_maps(
            missing_only=bool(getattr(args, "missing_only", False)),
            dry_run=bool(getattr(args, "dry_run", False)),
        )
        for row in rows:
            print(row)
        return
    if action == "show":
        root = normalize_project_root(getattr(args, "path", ""))
        which = getattr(args, "file", "project_history")
        text = read_workspace_file(root, which)
        sys.stdout.write(text)
        if text and not text.endswith("\n"):
            sys.stdout.write("\n")
        return
    if action == "write":
        root = normalize_project_root(getattr(args, "path", ""))
        which = getattr(args, "file", "")
        content = getattr(args, "content", None)
        if content is None:
            content = sys.stdin.read()
        write_workspace_file(root, which, content)
        print(f"Wrote {which} under {root}")
        return

    raise SystemExit(f"unknown project action: {action!r}")
