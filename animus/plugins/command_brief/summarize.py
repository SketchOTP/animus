from __future__ import annotations

import json
import logging
from typing import Any

import httpx

from animus.plugins.command_brief.governance import GovernanceBundle, governance_digest_for_prompt
from animus.plugins.command_brief.json_extract import extract_json_object

log = logging.getLogger("animus.command_brief")

_SYSTEM = """You are generating a compact Animus project status summary.
Use only the provided project governance docs.
Do not invent missing information.
If status is unclear, mark it unknown.
Return valid JSON only.
Keep bullets under 18 words.

Required top-level JSON keys:
- status (one of: active, stale, inactive, blocked, unknown)
- currentFocus (string)
- recentChanges (array of strings)
- nextActions (array of strings)
- risks (array of strings)
- sourceFiles (array of strings, relative paths you relied on)
"""


def normalize_summary_dict(raw: dict[str, Any], *, source_files_fallback: list[str]) -> dict[str, Any]:
    status = str(raw.get("status") or "unknown").strip().lower()
    if status not in ("active", "stale", "inactive", "blocked", "unknown"):
        status = "unknown"
    def _list(key: str) -> list[str]:
        v = raw.get(key)
        if not isinstance(v, list):
            return []
        out: list[str] = []
        for x in v:
            s = str(x).strip()
            if s:
                out.append(s[:500])
        return out[:24]

    sf = _list("sourceFiles")
    if not sf:
        sf = list(source_files_fallback)
    return {
        "status": status,
        "currentFocus": str(raw.get("currentFocus") or "").strip()[:2000] or "unknown",
        "recentChanges": _list("recentChanges")[:12],
        "nextActions": _list("nextActions")[:12],
        "risks": _list("risks")[:12],
        "sourceFiles": sf[:32],
    }


async def run_summary_completion(
    *,
    hermes_api: str,
    headers: dict[str, str],
    model: str,
    hermes_provider: str,
    hermes_base_url: str,
    bundle: GovernanceBundle,
    timeout: httpx.Timeout | None = None,
) -> tuple[dict[str, Any] | None, str | None, str]:
    """Returns (normalized_summary_dict_or_none, assistant_raw_text, model_used_label)."""
    digest = governance_digest_for_prompt(bundle)
    if not digest.strip():
        digest = "(no governance file contents were available; return unknown status and empty bullets)"

    upstream: dict[str, Any] = {
        "model": model,
        "stream": False,
        "temperature": 0.1,
        "max_tokens": 4096,
        "messages": [
            {"role": "system", "content": _SYSTEM},
            {
                "role": "user",
                "content": "Governance documents follow.\n\n" + digest + "\n\nRespond with JSON only.",
            },
        ],
    }
    hp = (hermes_provider or "").strip()
    hb = (hermes_base_url or "").strip()
    if hp:
        upstream["hermes_provider"] = hp
    if hb:
        upstream["hermes_base_url"] = hb

    url = f"{hermes_api.rstrip('/')}/v1/chat/completions"
    to = timeout or httpx.Timeout(connect=15.0, read=300.0, write=60.0, pool=5.0)
    raw = ""
    r: httpx.Response | None = None
    async with httpx.AsyncClient(timeout=to) as client:
        body_with_json_mode = {**upstream, "response_format": {"type": "json_object"}}
        r = await client.post(url, headers=headers, json=body_with_json_mode)
        raw = (await r.aread()).decode("utf-8", errors="replace")
        if r.status_code >= 400:
            log.info(
                "command_brief summarize retry without response_format (HTTP %s)",
                r.status_code,
            )
            r = await client.post(url, headers=headers, json=upstream)
            raw = (await r.aread()).decode("utf-8", errors="replace")

    if r is None or r.status_code >= 400:
        log.warning("command_brief summarize HTTP %s: %s", r.status_code if r else "?", raw[:500])
        return None, raw, model

    try:
        payload = json.loads(raw) if raw.strip() else {}
    except Exception:
        return None, raw, model

    # Reuse animus-chat server helper when available
    try:
        import server as srv  # type: ignore

        assistant = srv._assistant_text_from_chat_completion_payload(payload)
    except Exception:
        assistant = ""
        choices = payload.get("choices") if isinstance(payload, dict) else None
        if isinstance(choices, list) and choices:
            msg = choices[0].get("message") if isinstance(choices[0], dict) else None
            if isinstance(msg, dict) and isinstance(msg.get("content"), str):
                assistant = msg["content"].strip()

    parsed = extract_json_object(assistant)
    fallback_sf = sorted(bundle.texts.keys())
    if not parsed:
        return None, assistant, model
    return normalize_summary_dict(parsed, source_files_fallback=fallback_sf), assistant, model
