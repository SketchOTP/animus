from __future__ import annotations

from typing import Any

from model_tools import get_tool_definitions
from tools.skills_tool import _find_all_skills


def _summarize_text(raw: str, max_len: int = 180) -> str:
    txt = " ".join(str(raw or "").split())
    if len(txt) <= max_len:
        return txt
    return txt[: max_len - 3].rstrip() + "..."


def _tags_from_text(*parts: str, max_tags: int = 8) -> list[str]:
    joined = " ".join(parts).lower()
    tokens: list[str] = []
    for chunk in joined.replace("/", " ").replace("_", " ").replace("-", " ").split():
        tok = "".join(ch for ch in chunk if ch.isalnum())
        if len(tok) < 3:
            continue
        if tok in tokens:
            continue
        tokens.append(tok)
        if len(tokens) >= max_tags:
            break
    return tokens


def build_registry_snapshot(
    *,
    enabled_toolsets: list[str],
    disabled_tools: list[str],
) -> dict[str, list[dict[str, Any]]]:
    tool_defs = get_tool_definitions(
        enabled_toolsets=enabled_toolsets,
        disabled_toolsets=None,
        disabled_tools=disabled_tools,
        quiet_mode=True,
    )
    tools: list[dict[str, Any]] = []
    for td in tool_defs:
        fn = td.get("function") or {}
        name = str(fn.get("name") or "").strip()
        if not name:
            continue
        desc = _summarize_text(str(fn.get("description") or ""))
        tools.append(
            {
                "id": name,
                "summary": desc,
                "tags": _tags_from_text(name, desc),
            }
        )

    skills_raw = _find_all_skills(skip_disabled=False, include_paths=False)
    skills: list[dict[str, Any]] = []
    for sk in skills_raw:
        name = str(sk.get("name") or "").strip()
        if not name:
            continue
        desc = _summarize_text(str(sk.get("description") or ""))
        cat = str(sk.get("category") or "")
        skills.append(
            {
                "id": name,
                "summary": desc,
                "tags": _tags_from_text(name, desc, cat),
            }
        )

    return {"tools": tools, "skills": skills}

