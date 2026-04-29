"""ANIMUS Help bot — answers from ``docs/animus-user-guide.md`` only (no tools, no mutations)."""

from __future__ import annotations

import logging
import os
import re
from pathlib import Path

import httpx
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

log = logging.getLogger("animus.help")

_MONO_ROOT = Path(__file__).resolve().parent.parent
_GUIDE_PATH = _MONO_ROOT / "docs" / "animus-user-guide.md"
HERMES_API = (os.environ.get("HERMES_API_URL") or "http://127.0.0.1:8642").strip().rstrip("/")
HERMES_KEY = (os.environ.get("HERMES_API_KEY") or "").strip()

_MAX_GUIDE_CHARS = 120_000

HELP_SYSTEM_INSTRUCTIONS = """You are the ANIMUS Help assistant.

RULES (follow on every reply):
1. Use ONLY information explicitly stated inside the <guide> section in the user message. Treat the guide as the single source of truth for this product.
2. If the guide does not answer the question, say briefly that you do not find that in the user guide. You may name a relevant area (e.g. Settings, Projects, Cron) if the guide mentions it, but do not invent details.
3. You cannot change settings, restart services, run shell commands, edit files, call tools, or open URLs for the user. Never imply you did.
4. Do not invent features, API paths, env vars, ports, file paths, or CLI flags that are not written in the guide.
5. Prefer concise answers; use short markdown lists when the guide lists steps.

Reply in plain text or light markdown only (no HTML)."""


def _load_guide_text() -> tuple[str, str | None]:
    try:
        p = _GUIDE_PATH
        if not p.is_file():
            return "", f"Guide file missing: {p}"
        raw = p.read_text(encoding="utf-8", errors="replace")
        if len(raw) > _MAX_GUIDE_CHARS:
            raw = raw[:_MAX_GUIDE_CHARS] + "\n\n[Guide truncated for length.]"
        return raw, None
    except OSError as exc:
        return "", str(exc)


_FAQ_SECTION_TITLE_RE = re.compile(r"(?ms)^##\s+Frequently asked questions\s*\n")

_FAQ_TITLE_LOWER = "frequently asked questions"


def _slugify_heading(title: str) -> str:
    s = title.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = s.strip("-") or "topic"
    return s[:80]


def _topics_from_markdown(md: str) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    seen: set[str] = set()
    for line in md.splitlines():
        if not line.startswith("## ") or line.startswith("###"):
            continue
        title = line[3:].strip()
        if not title or title.lower() == _FAQ_TITLE_LOWER:
            continue
        sid = _slugify_heading(title)
        base = sid
        n = 2
        while sid in seen:
            sid = f"{base}-{n}"
            n += 1
        seen.add(sid)
        out.append({"id": sid, "title": title})
    return out


def _faq_markdown_from_guide(md: str) -> str:
    m = _FAQ_SECTION_TITLE_RE.search(md)
    if not m:
        return ""
    tail = md[m.end() :]
    m2 = re.search(r"(?m)^##\s+", tail)
    body = tail[: m2.start()] if m2 else tail
    return body.strip()


def _topics_view_markdown(md: str) -> str:
    """Guide body for the Topics tab (FAQ block removed so it is not duplicated)."""
    m = _FAQ_SECTION_TITLE_RE.search(md)
    if not m:
        return md.strip()
    start = m.start()
    tail = md[m.end() :]
    m2 = re.search(r"(?m)^##\s+", tail)
    if m2:
        after = tail[m2.start() :].lstrip("\n")
        return (md[:start].rstrip() + "\n\n" + after).strip()
    return md[:start].rstrip()


def _chat_completion_text(payload: dict) -> str:
    choices = payload.get("choices") if isinstance(payload, dict) else None
    if not choices:
        return ""
    first = choices[0] if isinstance(choices[0], dict) else {}
    msg = first.get("message") if isinstance(first.get("message"), dict) else {}
    content = msg.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        out: list[str] = []
        for part in content:
            if isinstance(part, dict) and part.get("text"):
                out.append(str(part.get("text")))
        return "\n".join(out)
    return ""


async def help_guide_get(_: Request) -> Response:
    text, err = _load_guide_text()
    if err:
        return JSONResponse(
            {
                "ok": False,
                "error": err,
                "markdown": "",
                "full_markdown": "",
                "topics_markdown": "",
                "faq_markdown": "",
                "topics": [],
            },
        )
    faq = _faq_markdown_from_guide(text)
    topics_md = _topics_view_markdown(text)
    # Topics must match ``##`` headings in ``topics_md`` (FAQ block stripped there).
    topics = _topics_from_markdown(topics_md)
    return JSONResponse(
        {
            "ok": True,
            "error": None,
            "markdown": text,
            "full_markdown": text,
            "topics_markdown": topics_md,
            "faq_markdown": faq,
            "topics": topics,
        },
    )


async def help_ask_post(req: Request) -> Response:
    if not HERMES_KEY:
        return JSONResponse(
            {"ok": False, "error": "HERMES_API_KEY is not configured. Complete onboarding or edit animus.env."},
            status_code=503,
        )
    try:
        body = await req.json()
    except Exception:
        body = {}
    q = str(body.get("question") or "").strip()
    if not q or len(q) > 8000:
        return JSONResponse({"ok": False, "error": "question required (max 8000 characters)"}, status_code=400)
    model = str(body.get("model") or "").strip()
    hp = str(body.get("hermes_provider") or "").strip()
    if not model or not hp:
        return JSONResponse({"ok": False, "error": "model and hermes_provider are required"}, status_code=400)
    if model.lower() == "auto" and hp.lower() == "openai-codex":
        model = "gpt-5.2-codex"
    base_url = str(body.get("hermes_base_url") or "").strip()
    guide, gerr = _load_guide_text()
    if gerr or not guide.strip():
        return JSONResponse({"ok": False, "error": gerr or "Guide is empty."}, status_code=500)
    user_block = "<guide>\n" + guide + "\n</guide>\n\nUser question:\n" + q
    payload: dict = {
        "model": model,
        "hermes_provider": hp,
        "stream": False,
        "messages": [
            {"role": "system", "content": HELP_SYSTEM_INSTRUCTIONS},
            {"role": "user", "content": user_block},
        ],
    }
    if base_url:
        payload["hermes_base_url"] = base_url
    headers = {"Authorization": f"Bearer {HERMES_KEY}", "Content-Type": "application/json"}
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(connect=15, read=120, write=30, pool=5)) as c:
            resp = await c.post(f"{HERMES_API}/v1/chat/completions", json=payload, headers=headers)
        try:
            data = resp.json() if resp.content else {}
        except Exception:
            data = {}
    except Exception as exc:
        log.exception("help ask transport error")
        return JSONResponse({"ok": False, "error": str(exc)[:500]}, status_code=502)
    if resp.status_code >= 400:
        err = data.get("error") if isinstance(data, dict) else None
        if isinstance(err, dict):
            msg = str(err.get("message") or err)[:1200]
        elif isinstance(err, str):
            msg = err[:1200]
        else:
            msg = (resp.text or "")[:800] or f"HTTP {resp.status_code}"
        return JSONResponse({"ok": False, "error": msg}, status_code=502)
    answer = _chat_completion_text(data if isinstance(data, dict) else {}).strip()
    if not answer:
        return JSONResponse({"ok": False, "error": "Empty response from model."}, status_code=502)
    try:
        from token_usage import record_token_usage

        usage = data.get("usage") if isinstance(data, dict) else None
        if isinstance(usage, dict):
            inp_raw = usage.get("prompt_tokens")
            out_raw = usage.get("completion_tokens")
            try:
                inp_i = int(inp_raw) if inp_raw is not None else None
            except (TypeError, ValueError):
                inp_i = None
            try:
                out_i = int(out_raw) if out_raw is not None else None
            except (TypeError, ValueError):
                out_i = None
            resolved = str(data.get("model") or model).strip()
            record_token_usage(hp, resolved, inp_i, out_i, "help", "")
    except Exception:
        pass
    return JSONResponse({"ok": True, "answer": answer})


def help_route_table():
    from starlette.routing import Route

    return [
        Route("/api/help/guide", help_guide_get, methods=["GET"]),
        Route("/api/help/ask", help_ask_post, methods=["POST"]),
    ]
