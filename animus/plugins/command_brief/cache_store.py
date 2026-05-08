from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def cache_path(data_dir: Path) -> Path:
    return data_dir / "command_brief_cache.json"


def load_cache(data_dir: Path) -> dict[str, Any]:
    p = cache_path(data_dir)
    if not p.is_file():
        return {"version": 1, "summaries": {}}
    try:
        raw = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, TypeError):
        return {"version": 1, "summaries": {}}
    if not isinstance(raw, dict):
        return {"version": 1, "summaries": {}}
    summaries = raw.get("summaries")
    if not isinstance(summaries, dict):
        summaries = {}
    return {"version": int(raw.get("version") or 1), "summaries": summaries}


def save_cache(data_dir: Path, summaries: dict[str, Any]) -> None:
    p = cache_path(data_dir)
    p.parent.mkdir(parents=True, exist_ok=True)
    body = {"version": 1, "summaries": summaries}
    p.write_text(json.dumps(body, indent=2, ensure_ascii=False), encoding="utf-8")


def get_summary(summaries: dict[str, Any], project_id: str) -> dict[str, Any] | None:
    row = summaries.get(project_id)
    return row if isinstance(row, dict) else None


def put_summary(summaries: dict[str, Any], project_id: str, row: dict[str, Any]) -> None:
    summaries[project_id] = row
