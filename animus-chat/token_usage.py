"""Append-only token usage log + read API (Phase 7)."""

from __future__ import annotations

import datetime as dt
import fcntl
import json
import logging
from pathlib import Path
from typing import Any, Optional

from starlette.requests import Request
from starlette.responses import JSONResponse

from hermes_runner import chat_data_dir

log = logging.getLogger("animus.tokens")

# PWA / in-app ``fetch`` sets ``X-Animus-Client`` to one of these slugs so ``token_usage.jsonl`` rows
# can be attributed to ANIMUS surfaces vs external OpenAI-shaped clients (which omit the header).
ANIMUS_CLIENT_HEADER = "X-Animus-Client"
ANIMUS_CLIENT_SLUGS: frozenset[str] = frozenset(
    {
        "web",  # generic in-app (legacy / fallback)
        "chat",  # main Hermes project chat
        "plan",  # Plan tab pipeline (non-stream usage via ``/api/tokens/record``)
        "skills",  # Skills tab mutations that report usage
        "wizard",  # setup / wizard flows that report usage
        "help",  # in-app Help ask (header; server also stamps ``animus_client=help``)
        "cron",  # cron UI actions (header; server stamps cron job / optimizer paths)
        "prompt-optimizer",  # cron prompt rewrite (UI + server log)
    }
)


def normalize_animus_client_slug(raw: str | None) -> str | None:
    s = (raw or "").strip().lower()
    return s if s in ANIMUS_CLIENT_SLUGS else None


def animus_client_from_request(req: Request) -> str | None:
    """Return allowed slug from ``X-Animus-Client`` when present."""
    try:
        return normalize_animus_client_slug(req.headers.get(ANIMUS_CLIENT_HEADER))
    except Exception:
        return None


def chat_usage_in_out(usage: dict[str, Any] | None) -> tuple[Optional[int], Optional[int]]:
    """Map OpenAI / Anthropic-style ``usage`` to (input_tokens, output_tokens) for JSONL."""
    if not isinstance(usage, dict):
        return None, None
    pt = usage.get("prompt_tokens")
    ct = usage.get("completion_tokens")
    it = usage.get("input_tokens")
    ot = usage.get("output_tokens")

    def _as_int(v: object) -> Optional[int]:
        if v is None:
            return None
        try:
            return int(v)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            return None

    inp_i = _as_int(pt if pt is not None else it)
    out_i = _as_int(ct if ct is not None else ot)
    if inp_i is None and out_i is None:
        tt = _as_int(usage.get("total_tokens"))
        if tt is not None and tt > 0:
            return tt, 0
    return inp_i, out_i


def _usage_path() -> Path:
    return chat_data_dir() / "token_usage.jsonl"


def record_token_usage(
    provider: str,
    model: str,
    input_tokens: int | None,
    output_tokens: int | None,
    source: str,
    source_id: str = "",
    *,
    animus_client: str | None = None,
) -> None:
    """Append one JSON line to ``token_usage.jsonl`` (locked).

    When ``animus_client`` is a slug in ``ANIMUS_CLIENT_SLUGS``, the row is attributed to that
    ANIMUS surface. ``None`` / unknown = external client or legacy rows without a stamp.
    """
    p = _usage_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    record: dict[str, Any] = {
        "ts": dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z"),
        "provider": str(provider or "").strip(),
        "model": str(model or "").strip(),
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "source": str(source or "other").strip() or "other",
        "source_id": str(source_id or "").strip(),
    }
    ac = normalize_animus_client_slug(animus_client)
    if ac:
        record["animus_client"] = ac
    line = json.dumps(record, separators=(",", ":")) + "\n"
    try:
        with p.open("a", encoding="utf-8") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            try:
                f.write(line)
            finally:
                fcntl.flock(f, fcntl.LOCK_UN)
    except OSError as exc:
        log.warning("record_token_usage failed: %s", exc)


def _parse_ts_ms(raw: str) -> float:
    s = (raw or "").strip()
    if not s:
        return 0.0
    try:
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        return dt.datetime.fromisoformat(s).timestamp() * 1000
    except Exception:
        return 0.0


def _num_tokens(v: Any) -> int:
    if v is None:
        return 0
    try:
        n = int(v)
        return max(0, n)
    except (TypeError, ValueError):
        return 0


def read_usage_window(days: int, source_filter: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Return raw records in window + summary aggregates."""
    days = max(1, min(int(days or 30), 366))
    cutoff = dt.datetime.now(dt.timezone.utc).timestamp() * 1000 - (days - 1) * 86400000
    p = _usage_path()
    records: list[dict[str, Any]] = []
    if p.is_file():
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            text = ""
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(row, dict):
                continue
            ts_ms = _parse_ts_ms(str(row.get("ts") or ""))
            if ts_ms < cutoff:
                continue
            src = str(row.get("source") or "other").strip() or "other"
            if source_filter and source_filter != "all" and src != source_filter:
                continue
            records.append(row)
    by_provider: dict[str, dict[str, int]] = {}
    by_model: dict[str, dict[str, int]] = {}
    by_source: dict[str, dict[str, int]] = {}
    tot_in = tot_out = 0
    for r in records:
        pr = str(r.get("provider") or "unknown").strip() or "unknown"
        md = str(r.get("model") or "unknown").strip() or "unknown"
        sc = str(r.get("source") or "other").strip() or "other"
        pi = _num_tokens(r.get("input_tokens"))
        po = _num_tokens(r.get("output_tokens"))
        tot_in += pi
        tot_out += po
        for bucket, key in ((by_provider, pr), (by_model, md), (by_source, sc)):
            cur = bucket.setdefault(key, {"input": 0, "output": 0})
            cur["input"] += pi
            cur["output"] += po
    summary = {
        "by_provider": by_provider,
        "by_model": by_model,
        "by_source": by_source,
        "total": {"input": tot_in, "output": tot_out},
    }
    return records, summary


def read_usage_all(source_filter: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Return every row in ``token_usage.jsonl`` (no date cutoff) + aggregates."""
    p = _usage_path()
    records: list[dict[str, Any]] = []
    if p.is_file():
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            text = ""
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(row, dict):
                continue
            src = str(row.get("source") or "other").strip() or "other"
            if source_filter and source_filter != "all" and src != source_filter:
                continue
            records.append(row)
    by_provider: dict[str, dict[str, int]] = {}
    by_model: dict[str, dict[str, int]] = {}
    by_source: dict[str, dict[str, int]] = {}
    tot_in = tot_out = 0
    for r in records:
        pr = str(r.get("provider") or "unknown").strip() or "unknown"
        md = str(r.get("model") or "unknown").strip() or "unknown"
        sc = str(r.get("source") or "other").strip() or "other"
        pi = _num_tokens(r.get("input_tokens"))
        po = _num_tokens(r.get("output_tokens"))
        tot_in += pi
        tot_out += po
        for bucket, key in ((by_provider, pr), (by_model, md), (by_source, sc)):
            cur = bucket.setdefault(key, {"input": 0, "output": 0})
            cur["input"] += pi
            cur["output"] += po
    summary = {
        "by_provider": by_provider,
        "by_model": by_model,
        "by_source": by_source,
        "total": {"input": tot_in, "output": tot_out},
    }
    return records, summary


async def tokens_usage_get(req: Request) -> JSONResponse:
    source = (req.query_params.get("source") or "all").strip().lower() or "all"
    full_q = (req.query_params.get("full") or "").strip().lower() in ("1", "true", "yes", "all")
    if full_q:
        records, summary = read_usage_all(source)
        payload: dict[str, Any] = {"records": records, "summary": summary, "full": True}
        try:
            from hermes_service_client import dashboard_get_analytics_usage, hermes_dashboard_session_token

            if hermes_dashboard_session_token():
                st, body = await dashboard_get_analytics_usage(366)
                if st == 200 and isinstance(body, dict):
                    payload["hermes_analytics"] = body
        except Exception as exc:
            log.debug("Hermes analytics merge skipped: %s", exc)
        return JSONResponse(payload)
    try:
        days = int((req.query_params.get("days") or "30").strip())
    except ValueError:
        days = 30
    records, summary = read_usage_window(days, source)
    payload: dict[str, Any] = {"records": records, "summary": summary}
    try:
        from hermes_service_client import dashboard_get_analytics_usage, hermes_dashboard_session_token

        if hermes_dashboard_session_token():
            st, body = await dashboard_get_analytics_usage(days)
            if st == 200 and isinstance(body, dict):
                payload["hermes_analytics"] = body
    except Exception as exc:
        log.debug("Hermes analytics merge skipped: %s", exc)
    return JSONResponse(payload)


async def tokens_record_post(req: Request) -> JSONResponse:
    try:
        body = await req.json()
    except Exception:
        body = {}
    if not isinstance(body, dict):
        return JSONResponse({"ok": False, "error": "invalid json"}, status_code=400)
    prov = str(body.get("provider") or "")
    model = str(body.get("model") or "")
    src = str(body.get("source") or "other").strip() or "other"
    sid = str(body.get("source_id") or "")
    inp = body.get("input_tokens")
    out = body.get("output_tokens")
    inp_i: int | None
    out_i: int | None
    try:
        inp_i = int(inp) if inp is not None and str(inp).strip() != "" else None
    except (TypeError, ValueError):
        inp_i = None
    try:
        out_i = int(out) if out is not None and str(out).strip() != "" else None
    except (TypeError, ValueError):
        out_i = None
    ac = animus_client_from_request(req)
    record_token_usage(prov, model, inp_i, out_i, src, sid, animus_client=ac)
    return JSONResponse({"ok": True})


def token_usage_route_table():
    from starlette.routing import Route

    return [
        Route("/api/tokens/usage", tokens_usage_get, methods=["GET"]),
        Route("/api/tokens/record", tokens_record_post, methods=["POST"]),
    ]
