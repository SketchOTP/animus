"""Append-only token usage log + read API (Phase 7)."""

from __future__ import annotations

import datetime as dt
import fcntl
import json
import logging
from pathlib import Path
from typing import Any

from starlette.requests import Request
from starlette.responses import JSONResponse

from hermes_runner import chat_data_dir

log = logging.getLogger("animus.tokens")


def _usage_path() -> Path:
    return chat_data_dir() / "token_usage.jsonl"


def record_token_usage(
    provider: str,
    model: str,
    input_tokens: int | None,
    output_tokens: int | None,
    source: str,
    source_id: str = "",
) -> None:
    """Append one JSON line to ``token_usage.jsonl`` (locked)."""
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


async def tokens_usage_get(req: Request) -> JSONResponse:
    try:
        days = int((req.query_params.get("days") or "30").strip())
    except ValueError:
        days = 30
    source = (req.query_params.get("source") or "all").strip().lower() or "all"
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
    record_token_usage(prov, model, inp_i, out_i, src, sid)
    return JSONResponse({"ok": True})


def token_usage_route_table():
    from starlette.routing import Route

    return [
        Route("/api/tokens/usage", tokens_usage_get, methods=["GET"]),
        Route("/api/tokens/record", tokens_record_post, methods=["POST"]),
    ]
