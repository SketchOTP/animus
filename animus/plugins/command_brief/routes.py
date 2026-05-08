from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from animus.plugins.command_brief.cache_store import get_summary, load_cache, put_summary, save_cache
from animus.plugins.command_brief.daily_log import append_daily_summary, ensure_daily_log_template, read_daily_log
from animus.plugins.command_brief.constants import NO_RECENT_WORK_FOCUS
from animus.plugins.command_brief.governance import (
    GovernanceBundle,
    _iso_mtime,
    governance_fresh_for_command_brief_inference,
    read_governance_bundle,
    read_governance_stats,
)
from animus.plugins.command_brief.prefs import command_brief_prefs_from_cfg
from animus.plugins.command_brief.regenerate import classify_display_status, should_regenerate_auto
from animus.plugins.command_brief.summarize import run_summary_completion

log = logging.getLogger("animus.command_brief")


def _iso_now() -> str:
    return datetime.now(tz=timezone.utc).isoformat().replace("+00:00", "Z")


def _model_label(inf: dict[str, Any]) -> str:
    p = str(inf.get("hermes_provider") or "").strip() or "unknown"
    m = str(inf.get("model") or "").strip() or "unknown"
    return f"{p}/{m}"


def _coerce_no_recent_summary(
    *,
    base: dict[str, Any],
    stats: GovernanceBundle,
    gen_at: str | None,
    recent_window_days: int,
) -> dict[str, Any]:
    disp = classify_display_status(
        bundle=stats,
        generated_at_iso=gen_at,
        recent_window_days=recent_window_days,
        blocked=False,
    )
    return {
        **base,
        "status": disp,
        "lastActivityAt": _iso_mtime(stats.max_mtime_epoch),
        "currentFocus": NO_RECENT_WORK_FOCUS,
        "recentChanges": [],
        "nextActions": [],
        "risks": [],
        "sourceFiles": [],
        "sourceFileModifiedTimes": dict(stats.mtimes_iso),
    }


async def command_brief_state(_req: Request) -> Response:
    import server as srv

    from agent.project_workspace import workspace_files_path_raw

    cfg = srv._read_animus_client_config()
    prefs = command_brief_prefs_from_cfg(cfg)
    if not prefs["enabled"]:
        return JSONResponse({"disabled": True, "prefs": prefs})
    data = load_cache(srv.DATA_DIR)
    summaries = data.get("summaries") if isinstance(data.get("summaries"), dict) else {}
    raw_projects = srv._read("projects.json", [])
    if not isinstance(raw_projects, list):
        raw_projects = []
    excl = srv._read_exclusion_set()
    projects = srv._filter_projects_by_exclusions(raw_projects, excl)
    rwd = int(prefs["recentWindowDays"])
    plist: list[dict[str, str]] = []
    out_list: list[dict[str, Any]] = []
    for item in projects:
        if not isinstance(item, dict):
            continue
        pid = str(item.get("id") or "").strip()
        if not pid:
            continue
        name = str(item.get("name") or "").strip() or "(unnamed)"
        plist.append(
            {
                "id": pid,
                "name": name,
                "path": str(item.get("path") or "").strip(),
            }
        )
        cached = get_summary(summaries, pid)
        raw_wp = workspace_files_path_raw(item)
        if not str(raw_wp or "").strip():
            if cached:
                out_list.append(cached)
            else:
                out_list.append(
                    {
                        "projectId": pid,
                        "name": name,
                        "status": "unknown",
                        "lastActivityAt": None,
                        "generatedAt": None,
                        "modelUsed": None,
                        "currentFocus": "",
                        "recentChanges": [],
                        "nextActions": [],
                        "risks": [],
                        "sourceFiles": [],
                        "sourceFileModifiedTimes": {},
                    }
                )
            continue
        try:
            root = srv._require_registered_project_path(raw_wp)
        except Exception:
            if cached:
                out_list.append(cached)
            else:
                out_list.append(
                    {
                        "projectId": pid,
                        "name": name,
                        "status": "unknown",
                        "lastActivityAt": None,
                        "generatedAt": None,
                        "modelUsed": None,
                        "currentFocus": "",
                        "recentChanges": [],
                        "nextActions": [],
                        "risks": [],
                        "sourceFiles": [],
                        "sourceFileModifiedTimes": {},
                    }
                )
            continue
        stats = read_governance_stats(root)
        gen_at = str((cached or {}).get("generatedAt") or "").strip() or None
        if not governance_fresh_for_command_brief_inference(stats):
            if cached:
                out_list.append(_coerce_no_recent_summary(base=cached, stats=stats, gen_at=gen_at, recent_window_days=rwd))
            else:
                out_list.append(
                    _coerce_no_recent_summary(
                        base={
                            "projectId": pid,
                            "name": name,
                            "generatedAt": None,
                            "modelUsed": None,
                        },
                        stats=stats,
                        gen_at=None,
                        recent_window_days=rwd,
                    )
                )
        elif cached:
            out_list.append(cached)
        else:
            out_list.append(
                {
                    "projectId": pid,
                    "name": name,
                    "status": "unknown",
                    "lastActivityAt": None,
                    "generatedAt": None,
                    "modelUsed": None,
                    "currentFocus": "",
                    "recentChanges": [],
                    "nextActions": [],
                    "risks": [],
                    "sourceFiles": [],
                    "sourceFileModifiedTimes": {},
                }
            )
    return JSONResponse({"disabled": False, "prefs": prefs, "summaries": out_list, "projects": plist})


async def command_brief_sync(req: Request) -> Response:
    import server as srv

    cfg = srv._read_animus_client_config()
    prefs = command_brief_prefs_from_cfg(cfg)
    if not prefs["enabled"]:
        return JSONResponse({"error": "command_brief_disabled"}, status_code=400)
    try:
        body = await req.json()
    except Exception:
        body = {}
    if not isinstance(body, dict):
        body = {}
    mode = str(body.get("mode") or "auto").strip().lower()
    if mode not in ("auto", "one", "all"):
        mode = "auto"
    project_id_filter = str(body.get("project_id") or "").strip()
    if mode == "one" and not project_id_filter:
        return JSONResponse({"error": "project_id is required when mode is one"}, status_code=400)
    if mode == "auto" and not bool(prefs["autoRefreshRecent"]):
        state_resp = await command_brief_state(req)
        payload = json.loads(state_resp.body.decode("utf-8"))
        if payload.get("disabled"):
            return JSONResponse({"error": "command_brief_disabled"}, status_code=400)
        return JSONResponse({"ok": True, "summaries": payload.get("summaries") or [], "errors": []})
    inference = body.get("inference") if isinstance(body.get("inference"), dict) else {}
    model = str(inference.get("model") or "").strip()
    hermes_provider = str(inference.get("hermes_provider") or "").strip()
    hermes_base_url = str(inference.get("hermes_base_url") or "").strip()
    if not model or not hermes_provider:
        return JSONResponse(
            {"error": "inference.model and inference.hermes_provider are required"},
            status_code=400,
        )

    from hermes_runner import gateway_upstream_headers

    headers = gateway_upstream_headers()
    hermes_api = srv.HERMES_API

    data = load_cache(srv.DATA_DIR)
    summaries: dict[str, Any] = data.get("summaries") if isinstance(data.get("summaries"), dict) else {}
    errors: list[str] = []

    raw_projects = srv._read("projects.json", [])
    if not isinstance(raw_projects, list):
        raw_projects = []
    excl = srv._read_exclusion_set()
    projects = srv._filter_projects_by_exclusions(raw_projects, excl)

    from agent.project_workspace import workspace_files_path_raw

    one_hit = False
    for item in projects:
        if not isinstance(item, dict):
            continue
        pid = str(item.get("id") or "").strip()
        if not pid:
            continue
        if mode == "one" and project_id_filter and pid != project_id_filter:
            continue
        if mode == "one" and project_id_filter and pid == project_id_filter:
            one_hit = True
        name = str(item.get("name") or "").strip() or "(unnamed)"
        raw_wp = workspace_files_path_raw(item)
        if not raw_wp.strip():
            errors.append(f"{pid}: missing workspace path")
            put_summary(
                summaries,
                pid,
                {
                    "projectId": pid,
                    "name": name,
                    "status": "blocked",
                    "lastActivityAt": None,
                    "generatedAt": get_summary(summaries, pid).get("generatedAt")
                    if get_summary(summaries, pid)
                    else None,
                    "modelUsed": None,
                    "currentFocus": "unknown",
                    "recentChanges": [],
                    "nextActions": [],
                    "risks": ["Missing workspace path"],
                    "sourceFiles": [],
                    "sourceFileModifiedTimes": {},
                },
            )
            continue
        try:
            root = srv._require_registered_project_path(raw_wp)
        except Exception as exc:
            errors.append(f"{pid}: {exc}")
            put_summary(
                summaries,
                pid,
                {
                    "projectId": pid,
                    "name": name,
                    "status": "blocked",
                    "lastActivityAt": None,
                    "generatedAt": get_summary(summaries, pid).get("generatedAt")
                    if get_summary(summaries, pid)
                    else None,
                    "modelUsed": None,
                    "currentFocus": "unknown",
                    "recentChanges": [],
                    "nextActions": [],
                    "risks": [str(exc)],
                    "sourceFiles": [],
                    "sourceFileModifiedTimes": {},
                },
            )
            continue

        stats = read_governance_stats(root)
        prev = get_summary(summaries, pid) or {}
        gen_at = str(prev.get("generatedAt") or "").strip() or None

        do_run = False
        if mode == "all":
            do_run = True
        elif mode == "one":
            do_run = bool(project_id_filter) and pid == project_id_filter
        else:
            do_run = should_regenerate_auto(
                enabled=True,
                auto_refresh_recent=bool(prefs["autoRefreshRecent"]),
                bundle=stats,
                generated_at_iso=gen_at,
                recent_window_days=int(prefs["recentWindowDays"]),
            )

        if not do_run:
            disp = classify_display_status(
                bundle=stats,
                generated_at_iso=gen_at,
                recent_window_days=int(prefs["recentWindowDays"]),
                blocked=False,
            )
            merged = {
                **prev,
                "projectId": pid,
                "name": name,
                "status": disp,
                "lastActivityAt": _iso_mtime(stats.max_mtime_epoch),
                "sourceFileModifiedTimes": dict(stats.mtimes_iso),
            }
            if not governance_fresh_for_command_brief_inference(stats):
                merged["currentFocus"] = NO_RECENT_WORK_FOCUS
                merged["recentChanges"] = []
                merged["nextActions"] = []
                merged["risks"] = []
                merged["sourceFiles"] = []
            put_summary(summaries, pid, merged)
            continue

        if not governance_fresh_for_command_brief_inference(stats):
            disp = classify_display_status(
                bundle=stats,
                generated_at_iso=gen_at,
                recent_window_days=int(prefs["recentWindowDays"]),
                blocked=False,
            )
            put_summary(
                summaries,
                pid,
                {
                    "projectId": pid,
                    "name": name,
                    "status": disp,
                    "lastActivityAt": _iso_mtime(stats.max_mtime_epoch),
                    "generatedAt": prev.get("generatedAt"),
                    "modelUsed": prev.get("modelUsed"),
                    "currentFocus": NO_RECENT_WORK_FOCUS,
                    "recentChanges": [],
                    "nextActions": [],
                    "risks": [],
                    "sourceFiles": [],
                    "sourceFileModifiedTimes": dict(stats.mtimes_iso),
                },
            )
            continue

        bundle = read_governance_bundle(root)
        try:
            norm, _raw, _m = await run_summary_completion(
                hermes_api=hermes_api,
                headers=headers,
                model=model,
                hermes_provider=hermes_provider,
                hermes_base_url=hermes_base_url,
                bundle=bundle,
            )
        except Exception as exc:
            log.warning("command_brief summarize failed for %s: %s", pid, exc)
            errors.append(f"{pid}: {exc}")
            disp = classify_display_status(
                bundle=bundle,
                generated_at_iso=gen_at,
                recent_window_days=int(prefs["recentWindowDays"]),
                blocked=True,
            )
            put_summary(
                summaries,
                pid,
                {
                    "projectId": pid,
                    "name": name,
                    "status": disp,
                    "lastActivityAt": _iso_mtime(bundle.max_mtime_epoch),
                    "generatedAt": prev.get("generatedAt"),
                    "modelUsed": prev.get("modelUsed"),
                    "currentFocus": str(prev.get("currentFocus") or "unknown"),
                    "recentChanges": list(prev.get("recentChanges") or []),
                    "nextActions": list(prev.get("nextActions") or []),
                    "risks": list(prev.get("risks") or []) + [f"Summarizer error: {exc}"],
                    "sourceFiles": list(prev.get("sourceFiles") or []),
                    "sourceFileModifiedTimes": dict(bundle.mtimes_iso),
                },
            )
            continue

        if not norm:
            errors.append(f"{pid}: empty or invalid JSON from model")
            continue

        st = str(norm.get("status") or "unknown")
        gen = _iso_now()
        row: dict[str, Any] = {
            "projectId": pid,
            "name": name,
            "status": st,
            "lastActivityAt": _iso_mtime(bundle.max_mtime_epoch),
            "generatedAt": gen,
            "modelUsed": _model_label(inference),
            "currentFocus": norm.get("currentFocus") or "unknown",
            "recentChanges": norm.get("recentChanges") or [],
            "nextActions": norm.get("nextActions") or [],
            "risks": norm.get("risks") or [],
            "sourceFiles": norm.get("sourceFiles") or [],
            "sourceFileModifiedTimes": dict(bundle.mtimes_iso),
        }
        put_summary(summaries, pid, row)
        try:
            append_daily_summary(
                root,
                model_label=_model_label(inference),
                status=st,
                source_files=list(row["sourceFiles"]),
                current_focus=str(row["currentFocus"]),
                recent_changes=list(row["recentChanges"]),
                next_actions=list(row["nextActions"]),
                risks=list(row["risks"]),
            )
        except OSError as exc:
            errors.append(f"{pid}: log append failed: {exc}")

    if mode == "one" and not one_hit:
        return JSONResponse({"error": "project_id not found"}, status_code=404)

    save_cache(srv.DATA_DIR, summaries)
    out: list[dict[str, Any]] = []
    for item in projects:
        if not isinstance(item, dict):
            continue
        pid = str(item.get("id") or "").strip()
        if not pid:
            continue
        r = get_summary(summaries, pid)
        if r:
            out.append(r)
    return JSONResponse({"ok": True, "summaries": out, "errors": errors})


async def command_brief_daily_log(req: Request) -> Response:
    """Read durable ``project_daily_summaries.md`` (no model). Allowed even when Command Brief is disabled."""
    import server as srv

    raw = str(req.query_params.get("path") or "").strip()
    if not raw:
        return JSONResponse({"error": "path required"}, status_code=400)
    try:
        root = srv._require_registered_project_path(raw)
    except Exception as exc:
        return JSONResponse({"error": str(exc)}, status_code=400)
    # Materialize template on first open (Summaries); never overwrites existing file.
    ensure_daily_log_template(root)
    text = read_daily_log(root)
    return JSONResponse({"path": str(root), "content": text})


def command_brief_route_table() -> list[Any]:
    from starlette.routing import Route

    return [
        Route("/api/command-brief/state", command_brief_state, methods=["GET"]),
        Route("/api/command-brief/sync", command_brief_sync, methods=["POST"]),
        Route("/api/command-brief/daily-log", command_brief_daily_log, methods=["GET"]),
    ]
