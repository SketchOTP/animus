from __future__ import annotations

import json
import re
from typing import Any


def _balanced_object_slice(s: str, start: int) -> str | None:
    """Return substring from ``{`` at ``start`` through matching ``}``, respecting JSON strings."""
    depth = 0
    in_string = False
    escape = False
    for i in range(start, len(s)):
        ch = s[i]
        if escape:
            escape = False
            continue
        if in_string:
            if ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return s[start : i + 1]
    return None


def extract_json_object(text: str) -> dict[str, Any] | None:
    """Parse first JSON object from model output; tolerates markdown fences and preamble."""
    if not isinstance(text, str):
        return None
    s = text.strip()
    if not s:
        return None
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", s, re.IGNORECASE)
    if fence:
        s = fence.group(1).strip()

    start = s.find("{")
    if start < 0:
        return None

    chunk = _balanced_object_slice(s, start)
    if chunk:
        try:
            out = json.loads(chunk)
            if isinstance(out, dict):
                return out
        except json.JSONDecodeError:
            pass

    end = s.rfind("}")
    if end > start:
        try:
            out = json.loads(s[start : end + 1])
            if isinstance(out, dict):
                return out
        except json.JSONDecodeError:
            pass
    return None
