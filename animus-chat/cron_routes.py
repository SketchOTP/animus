"""Cron API — uses Hermes Agent ``cron.jobs`` (same store as gateway) plus ``hermes cron status`` for daemon health."""

from __future__ import annotations

import json
import logging
import urllib.parse
from datetime import datetime as dtmod
from typing import Any
from zoneinfo import ZoneInfo as ZI

from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from hermes_runner import append_audit, run_hermes, run_hermes_cron

log = logging.getLogger("animus.cron")


def _audit(op: str, **parts: str) -> None:
    bits = " ".join(f"{k}={v}" for k, v in parts.items())
    append_audit("cron_audit.log", f"{op}  {bits}")


async def cron_list_api(_req: Request) -> Response:
    try:
        from cron.jobs import list_jobs

        return JSONResponse(list_jobs(include_disabled=True))
    except Exception as exc:
        log.exception("cron_list_api failed")
        return JSONResponse({"error": str(exc)}, status_code=500)


async def cron_status_api(_req: Request) -> Response:
    res = run_hermes_cron(["status"], timeout=15)
    text = (res["stdout"] + "\n" + res["stderr"]).lower()
    running = res["ok"] and ("running" in text or "active" in text or "scheduler" in text or "ok" in text)
    job_count = 0
    try:
        from cron.jobs import list_jobs

        job_count = len(list_jobs(include_disabled=True) or [])
    except Exception:
        pass
    return JSONResponse(
        {
            "ok": res["ok"],
            "running": bool(running),
            "job_count": job_count,
            "stdout": res["stdout"],
            "stderr": res["stderr"],
        }
    )


async def cron_create_api(req: Request) -> Response:
    try:
        body = await req.json()
    except Exception:
        return JSONResponse({"error": "invalid json"}, status_code=400)
    try:
        from cron.jobs import create_job

        sched = str(body.get("schedule", "") or "").strip()
        if not sched:
            return JSONResponse({"error": "schedule is required"}, status_code=400)
        raw_deliver = body.get("deliver")
        if isinstance(raw_deliver, str) and not raw_deliver.strip():
            raw_deliver = None
        job = create_job(
            prompt=body["prompt"],
            schedule=sched,
            name=body.get("name", ""),
            deliver=raw_deliver,
            schedule_tz=body.get("schedule_tz"),
        )
        _audit("CREATE", job_id=str(job.get("id", "")), result="ok")
        return JSONResponse(job)
    except KeyError:
        return JSONResponse({"error": "prompt is required"}, status_code=400)
    except Exception as exc:
        log.exception("cron_create_api failed")
        _audit("CREATE", result="error", detail=str(exc)[:400])
        return JSONResponse({"error": str(exc)}, status_code=400)


async def cron_wallclock_iso(req: Request) -> Response:
    try:
        body = await req.json()
    except Exception:
        return JSONResponse({"error": "invalid json"}, status_code=400)
    date_s = str(body.get("date", "")).strip()
    time_s = str(body.get("time", "")).strip()
    iana = str(body.get("iana", "")).strip()
    if not date_s or not time_s or not iana:
        return JSONResponse(
            {"error": "date, time, and iana (timezone) are required"},
            status_code=400,
        )
    try:
        if len(time_s) == 5:
            time_s = time_s + ":00"
        local = dtmod.strptime(f"{date_s} {time_s}", "%Y-%m-%d %H:%M:%S").replace(tzinfo=ZI(iana))
        return JSONResponse({"iso": local.isoformat()})
    except Exception as exc:
        log.exception("cron_wallclock_iso failed")
        return JSONResponse({"error": str(exc)}, status_code=400)


async def _cron_apply_job_updates(job_id: str, body: dict) -> Response:
    from cron.jobs import get_job, update_job

    if not get_job(job_id):
        return JSONResponse({"error": "Not found"}, status_code=404)

    updates: dict = {}
    if "name" in body:
        updates["name"] = str(body.get("name") or "").strip()
    if "prompt" in body:
        prompt = str(body.get("prompt") or "").strip()
        if not prompt:
            return JSONResponse({"error": "prompt cannot be empty"}, status_code=400)
        updates["prompt"] = prompt
    if "deliver" in body:
        raw = body.get("deliver")
        updates["deliver"] = (str(raw).strip() if raw is not None else "") or "local"
    if "schedule" in body:
        schedule = str(body.get("schedule") or "").strip()
        if not schedule:
            return JSONResponse({"error": "schedule cannot be empty"}, status_code=400)
        updates["schedule"] = schedule
    if "schedule_tz" in body:
        raw_tz = body.get("schedule_tz")
        if raw_tz is None:
            updates["schedule_tz"] = None
        else:
            updates["schedule_tz"] = str(raw_tz).strip() or None

    if not updates:
        return JSONResponse({"error": "no fields to update"}, status_code=400)

    try:
        job = update_job(job_id, updates)
    except ValueError as exc:
        return JSONResponse({"error": str(exc)}, status_code=400)
    except Exception as exc:
        log.exception("cron update failed")
        return JSONResponse({"error": str(exc)}, status_code=500)

    if not job:
        return JSONResponse({"error": "Not found"}, status_code=404)
    _audit("UPDATE", job_id=job_id, result="ok")
    return JSONResponse(job)


async def cron_update_put_api(req: Request) -> Response:
    job_id = urllib.parse.unquote(req.path_params["job_id"])
    try:
        body = await req.json()
    except Exception as exc:
        return JSONResponse({"error": f"invalid JSON: {exc}"}, status_code=400)
    return await _cron_apply_job_updates(job_id, body)


async def cron_edit_post(req: Request) -> Response:
    try:
        body = await req.json()
    except Exception as exc:
        return JSONResponse({"error": f"invalid JSON: {exc}"}, status_code=400)
    jid = str(body.get("id") or body.get("job_id") or "").strip()
    if not jid:
        return JSONResponse({"error": "missing id or job_id in JSON body"}, status_code=400)
    return await _cron_apply_job_updates(jid, body)


async def cron_delete_api(req: Request) -> Response:
    job_id = urllib.parse.unquote(req.path_params["job_id"])
    try:
        from cron.jobs import remove_job

        ok = remove_job(job_id)
        if not ok:
            return JSONResponse({"error": "Job not found"}, status_code=404)
        _audit("DELETE", job_id=job_id, result="ok")
        return JSONResponse({"ok": True})
    except Exception as exc:
        log.exception("cron_delete_api failed")
        return JSONResponse({"error": str(exc)}, status_code=500)


async def cron_pause_api(req: Request) -> Response:
    job_id = urllib.parse.unquote(req.path_params["job_id"])
    try:
        from cron.jobs import pause_job

        job = pause_job(job_id)
        _audit("PAUSE", job_id=job_id, result="ok" if job else "missing")
        return JSONResponse(job or {"error": "Not found"}, status_code=200 if job else 404)
    except Exception as exc:
        return JSONResponse({"error": str(exc)}, status_code=500)


async def cron_resume_api(req: Request) -> Response:
    job_id = urllib.parse.unquote(req.path_params["job_id"])
    try:
        from cron.jobs import resume_job

        job = resume_job(job_id)
        _audit("RESUME", job_id=job_id, result="ok" if job else "missing")
        return JSONResponse(job or {"error": "Not found"}, status_code=200 if job else 404)
    except Exception as exc:
        return JSONResponse({"error": str(exc)}, status_code=500)


async def cron_trigger_api(req: Request) -> Response:
    job_id = urllib.parse.unquote(req.path_params["job_id"])
    try:
        from cron.jobs import trigger_job

        job = trigger_job(job_id)
        _audit("TRIGGER", job_id=job_id, result="ok" if job else "missing")
        if job:
            try:
                from token_usage import record_token_usage

                prov = str(job.get("provider") or job.get("hermes_provider") or "").strip() or "hermes"
                model = str(job.get("model") or "").strip() or ""
                record_token_usage(prov, model or "(job)", None, None, "cron", str(job.get("id") or job_id))
            except Exception as exc:
                log.debug("cron token record skipped: %s", exc)
        return JSONResponse(job or {"error": "Not found"}, status_code=200 if job else 404)
    except Exception as exc:
        log.exception("cron_trigger_api failed")
        return JSONResponse({"error": str(exc)}, status_code=500)


async def cron_run_api(req: Request) -> Response:
    """Manual run — same as trigger (queue on next tick)."""
    return await cron_trigger_api(req)


async def cron_logs_api(req: Request) -> Response:
    """Tail cron output: try ``hermes cron logs``, then ``~/.hermes/cron/output/<id>/*.md``."""
    job_id = urllib.parse.unquote(req.path_params["job_id"])
    try:
        lim = int(req.query_params.get("lines") or "50")
    except ValueError:
        lim = 50
    lim = max(1, min(200, lim))
    stderr_hint = ""

    for argv in (
        ["cron", "logs", job_id, "--lines", str(lim)],
        ["cron", "logs", job_id],
    ):
        res = run_hermes(argv, timeout=25)
        if res["ok"] and (res.get("stdout") or "").strip():
            raw_lines = [ln for ln in (res["stdout"] or "").splitlines() if ln.strip()]
            lines_out = [{"timestamp": None, "message": ln, "level": "info"} for ln in raw_lines[-lim:]]
            return JSONResponse({"lines": lines_out})
        if (res.get("stderr") or "").strip():
            stderr_hint = (res.get("stderr") or "")[:400]

    try:
        from cron.jobs import OUTPUT_DIR

        job_dir = OUTPUT_DIR / job_id
        if job_dir.is_dir():
            files = sorted(job_dir.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
            collected: list[dict[str, Any]] = []
            for fp in files[:8]:
                try:
                    for ln in fp.read_text(encoding="utf-8", errors="replace").splitlines():
                        if ln.strip():
                            collected.append({"timestamp": None, "message": ln, "level": "info"})
                except OSError:
                    continue
            if collected:
                return JSONResponse({"lines": collected[-lim:]})
    except Exception as exc:
        log.debug("cron_logs disk tail skipped: %s", exc)

    err_msg = (
        "Log access is not available from this ANIMUS host for this Hermes Agent build. "
        "Try `hermes cron logs <job_id>` in a terminal on the machine that runs the gateway, "
        "or inspect markdown files under ~/.hermes/cron/output/<job_id>/."
    )
    if stderr_hint:
        err_msg = err_msg + " CLI: " + stderr_hint.strip()
    return JSONResponse({"lines": [], "error": err_msg})


async def cron_audit_api(req: Request) -> Response:
    from hermes_runner import chat_data_dir

    limit = int(req.query_params.get("limit") or "100")
    path = chat_data_dir() / "cron_audit.log"
    if not path.is_file():
        return JSONResponse({"lines": []})
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()[-limit:]
    return JSONResponse({"lines": lines})


def cron_route_table():
    from starlette.routing import Route

    return [
        Route("/api/cron/wallclock-iso", cron_wallclock_iso, methods=["POST"]),
        Route("/api/cron/edit", cron_edit_post, methods=["POST"]),
        Route("/api/cron/list", cron_list_api, methods=["GET"]),
        Route("/api/cron/status", cron_status_api, methods=["GET"]),
        Route("/api/cron/create", cron_create_api, methods=["POST"]),
        Route("/api/cron/trigger/{job_id}", cron_trigger_api, methods=["POST"]),
        Route("/api/cron/pause/{job_id}", cron_pause_api, methods=["POST"]),
        Route("/api/cron/resume/{job_id}", cron_resume_api, methods=["POST"]),
        Route("/api/cron/update/{job_id}", cron_update_put_api, methods=["PUT"]),
        Route("/api/cron/delete/{job_id}", cron_delete_api, methods=["DELETE"]),
        Route("/api/cron/run/{job_id}", cron_run_api, methods=["POST"]),
        Route("/api/cron/logs/{job_id}", cron_logs_api, methods=["GET"]),
        Route("/api/cron/audit", cron_audit_api, methods=["GET"]),
    ]
