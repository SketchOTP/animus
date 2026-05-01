"""Cron API — proxies Hermes gateway ``/api/jobs`` (OpenAI server) with in-process fallback on transport errors."""

from __future__ import annotations

import json
import logging
import urllib.parse
from datetime import datetime as dtmod
from typing import Any
from zoneinfo import ZoneInfo as ZI

import httpx
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from hermes_runner import append_audit, gateway_upstream_headers, run_hermes, run_hermes_cron
from hermes_service_client import gateway_http_json, hermes_api_base

log = logging.getLogger("animus.cron")


def _audit(op: str, **parts: str) -> None:
    bits = " ".join(f"{k}={v}" for k, v in parts.items())
    append_audit("cron_audit.log", f"{op}  {bits}")


def _gateway_error_message(body: Any) -> str:
    if not isinstance(body, dict):
        return str(body)
    e = body.get("error")
    if isinstance(e, dict):
        return str(e.get("message") or e.get("code") or json.dumps(e)[:800])
    if isinstance(e, str):
        return e
    return str(body.get("detail") or body.get("message") or json.dumps(body)[:800])


def _job_id_hex12(job_id: str) -> bool:
    import re

    return bool(re.fullmatch(r"[a-f0-9]{12}", (job_id or "").strip().lower()))


def _chat_completion_choice_text(payload: dict) -> str:
    choices = payload.get("choices") if isinstance(payload, dict) else None
    if not choices:
        return ""
    first = choices[0] if isinstance(choices[0], dict) else {}
    msg = first.get("message") if isinstance(first.get("message"), dict) else {}
    content = msg.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        out = []
        for part in content:
            if isinstance(part, dict) and part.get("text"):
                out.append(str(part.get("text")))
        return "\n".join(out)
    return ""


async def _gw(method: str, path: str, json_body: Any = None) -> tuple[int, Any]:
    return await gateway_http_json(method, path, json_body=json_body, timeout=90.0)


async def cron_list_api(_req: Request) -> Response:
    status, body = await _gw("GET", "/api/jobs?include_disabled=true")
    if status == 200 and isinstance(body, dict) and "jobs" in body:
        return JSONResponse(body.get("jobs") or [])
    try:
        from cron.jobs import list_jobs

        return JSONResponse(list_jobs(include_disabled=True))
    except Exception:
        log.exception("cron_list_api fallback failed")
    return JSONResponse({"error": _gateway_error_message(body)}, status_code=status or 502)


async def cron_status_api(_req: Request) -> Response:
    res = run_hermes_cron(["status"], timeout=15)
    text = (res["stdout"] + "\n" + res["stderr"]).lower()
    running = res["ok"] and ("running" in text or "active" in text or "scheduler" in text or "ok" in text)
    job_count = 0
    st, body = await _gw("GET", "/api/jobs?include_disabled=true")
    if st == 200 and isinstance(body, dict):
        job_count = len(body.get("jobs") or [])
    else:
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
    sched = str(body.get("schedule", "") or "").strip()
    if not sched:
        return JSONResponse({"error": "schedule is required"}, status_code=400)
    if "prompt" not in body:
        return JSONResponse({"error": "prompt is required"}, status_code=400)
    raw_deliver = body.get("deliver")
    if isinstance(raw_deliver, str) and not raw_deliver.strip():
        raw_deliver = None
    gw_body: dict[str, Any] = {
        "name": str(body.get("name", "") or "").strip() or "ANIMUS job",
        "schedule": sched,
        "prompt": body["prompt"],
        "deliver": raw_deliver if raw_deliver is not None else "local",
    }
    if body.get("schedule_tz") is not None:
        gw_body["schedule_tz"] = body.get("schedule_tz")
    if body.get("workdir") is not None:
        gw_body["workdir"] = body.get("workdir")
    st, resp = await _gw("POST", "/api/jobs", gw_body)
    if st == 200 and isinstance(resp, dict) and resp.get("job"):
        job = resp["job"]
        _audit("CREATE", job_id=str(job.get("id", "")), result="ok")
        return JSONResponse(job)
    if st == 0:
        try:
            from cron.jobs import create_job

            job = create_job(
                prompt=body["prompt"],
                schedule=sched,
                name=body.get("name", ""),
                deliver=raw_deliver,
                schedule_tz=body.get("schedule_tz"),
                workdir=body.get("workdir"),
            )
            _audit("CREATE", job_id=str(job.get("id", "")), result="ok_fallback")
            return JSONResponse(job)
        except Exception as exc:
            log.exception("cron_create_api fallback failed")
            _audit("CREATE", result="error", detail=str(exc)[:400])
            return JSONResponse({"error": str(exc)}, status_code=400)
    _audit("CREATE", result="error", detail=_gateway_error_message(resp)[:400])
    return JSONResponse({"error": _gateway_error_message(resp)}, status_code=st or 502)


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
    if not _job_id_hex12(job_id):
        return JSONResponse({"error": "Invalid job ID"}, status_code=400)
    sanitized: dict[str, Any] = {}
    if "name" in body:
        sanitized["name"] = str(body.get("name") or "").strip()
    if "prompt" in body:
        prompt = str(body.get("prompt") or "").strip()
        if not prompt:
            return JSONResponse({"error": "prompt cannot be empty"}, status_code=400)
        sanitized["prompt"] = prompt
    if "deliver" in body:
        raw = body.get("deliver")
        sanitized["deliver"] = (str(raw).strip() if raw is not None else "") or "local"
    if "schedule" in body:
        schedule = str(body.get("schedule") or "").strip()
        if not schedule:
            return JSONResponse({"error": "schedule cannot be empty"}, status_code=400)
        sanitized["schedule"] = schedule
    if "schedule_tz" in body:
        raw_tz = body.get("schedule_tz")
        sanitized["schedule_tz"] = None if raw_tz is None else (str(raw_tz).strip() or None)
    if "workdir" in body:
        wd = body.get("workdir")
        if wd in (None, "", False):
            sanitized["workdir"] = None
        else:
            sanitized["workdir"] = str(wd).strip()

    if not sanitized:
        return JSONResponse({"error": "no fields to update"}, status_code=400)

    st, resp = await _gw("PATCH", f"/api/jobs/{job_id}", sanitized)
    if st == 200 and isinstance(resp, dict) and resp.get("job"):
        job = resp["job"]
        _audit("UPDATE", job_id=job_id, result="ok")
        return JSONResponse(job)
    if st == 0:
        from cron.jobs import get_job, update_job

        if not get_job(job_id):
            return JSONResponse({"error": "Not found"}, status_code=404)
        try:
            job = update_job(job_id, sanitized)
        except ValueError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        except Exception as exc:
            log.exception("cron update fallback failed")
            return JSONResponse({"error": str(exc)}, status_code=500)
        if not job:
            return JSONResponse({"error": "Not found"}, status_code=404)
        _audit("UPDATE", job_id=job_id, result="ok_fallback")
        return JSONResponse(job)
    if st == 404:
        return JSONResponse({"error": "Not found"}, status_code=404)
    return JSONResponse({"error": _gateway_error_message(resp)}, status_code=st or 502)


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
    if not _job_id_hex12(job_id):
        return JSONResponse({"error": "Invalid job ID"}, status_code=400)
    st, resp = await _gw("DELETE", f"/api/jobs/{job_id}")
    if st == 200:
        _audit("DELETE", job_id=job_id, result="ok")
        return JSONResponse({"ok": True})
    if st == 0:
        from cron.jobs import remove_job

        ok = remove_job(job_id)
        if not ok:
            return JSONResponse({"error": "Job not found"}, status_code=404)
        _audit("DELETE", job_id=job_id, result="ok_fallback")
        return JSONResponse({"ok": True})
    if st == 404:
        return JSONResponse({"error": "Job not found"}, status_code=404)
    return JSONResponse({"error": _gateway_error_message(resp)}, status_code=st or 502)


async def _lifecycle(job_id: str, action: str) -> Response:
    if not _job_id_hex12(job_id):
        return JSONResponse({"error": "Invalid job ID"}, status_code=400)
    st, resp = await _gw("POST", f"/api/jobs/{job_id}/{action}")
    if st == 200 and isinstance(resp, dict) and resp.get("job"):
        job = resp["job"]
        return JSONResponse(job)
    if st == 0:
        from cron.jobs import get_job, pause_job, resume_job, trigger_job

        if not get_job(job_id):
            return JSONResponse({"error": "Not found"}, status_code=404)
        fn = {"pause": pause_job, "resume": resume_job, "run": trigger_job}[action]
        job = fn(job_id)
        return JSONResponse(job or {"error": "Not found"}, status_code=200 if job else 404)
    if st == 404:
        return JSONResponse({"error": "Not found"}, status_code=404)
    return JSONResponse(resp if isinstance(resp, dict) else {"error": str(resp)}, status_code=st or 502)


async def cron_pause_api(req: Request) -> Response:
    job_id = urllib.parse.unquote(req.path_params["job_id"])
    r = await _lifecycle(job_id, "pause")
    _audit("PAUSE", job_id=job_id, result="ok" if r.status_code == 200 else "err")
    return r


async def cron_resume_api(req: Request) -> Response:
    job_id = urllib.parse.unquote(req.path_params["job_id"])
    r = await _lifecycle(job_id, "resume")
    _audit("RESUME", job_id=job_id, result="ok" if r.status_code == 200 else "err")
    return r


async def cron_trigger_api(req: Request) -> Response:
    job_id = urllib.parse.unquote(req.path_params["job_id"])
    r = await _lifecycle(job_id, "run")
    if r.status_code == 200:
        try:
            from token_usage import record_token_usage

            stj, body = await _gw("GET", f"/api/jobs/{job_id}")
            job: dict[str, Any] = {}
            if stj == 200 and isinstance(body, dict) and isinstance(body.get("job"), dict):
                job = body["job"]
            prov = str(job.get("provider") or job.get("hermes_provider") or "").strip() or "hermes"
            model = str(job.get("model") or "").strip() or ""
            record_token_usage(
                prov,
                model or "(job)",
                None,
                None,
                "cron",
                str(job.get("id") or job_id),
                animus_client="cron",
            )
        except Exception as exc:
            log.debug("cron token record skipped: %s", exc)
    _audit("TRIGGER", job_id=job_id, result="ok" if r.status_code == 200 else "err")
    return r


async def cron_run_api(req: Request) -> Response:
    return await cron_trigger_api(req)


async def cron_logs_api(req: Request) -> Response:
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


async def cron_optimize_prompt_api(req: Request) -> Response:
    """Rewrite a cron task prompt for clarity and completeness (non-streaming chat)."""
    try:
        body = await req.json()
    except Exception:
        body = {}
    raw = str(body.get("prompt") or "").strip()
    if not raw:
        return JSONResponse({"error": "prompt is required"}, status_code=400)
    if len(raw) > 24_000:
        return JSONResponse({"error": "prompt too long"}, status_code=400)
    sched_hint = str(body.get("schedule_summary") or "").strip()
    proj = str(body.get("project_name") or "").strip()
    model = str(body.get("model") or "").strip() or "gpt-4o-mini"
    hermes_provider = str(body.get("hermes_provider") or "").strip() or "openai"
    extra = ""
    if sched_hint:
        extra += f"\nSchedule context: {sched_hint}"
    if proj:
        extra += f"\nProject name: {proj}"
    user_msg = (
        "Rewrite the following cron-job task instructions for an autonomous coding agent.\n"
        "Goals: make them specific, actionable, and self-contained; add any missing "
        "constraints (scope, outputs, success criteria) when obvious; keep the same intent.\n"
        "Return only the rewritten instructions as plain text — no preamble or markdown fences."
        f"{extra}\n\n--- Original ---\n{raw}"
    )
    payload: dict[str, Any] = {
        "model": model,
        "hermes_provider": hermes_provider,
        "stream": False,
        "temperature": 0.3,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a prompt engineer for scheduled autonomous agent jobs. "
                    "Output only the improved task text."
                ),
            },
            {"role": "user", "content": user_msg},
        ],
    }
    url = f"{hermes_api_base()}/v1/chat/completions"
    headers = gateway_upstream_headers()
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(connect=15, read=120, write=30, pool=5)) as c:
            resp = await c.post(url, json=payload, headers=headers)
        data = resp.json() if resp.content else {}
    except Exception as exc:
        log.exception("cron_optimize_prompt transport error")
        return JSONResponse({"error": str(exc)[:500]}, status_code=502)
    if resp.status_code >= 400:
        err = data.get("error") if isinstance(data, dict) else None
        if isinstance(err, dict):
            msg = str(err.get("message") or err)[:1200]
        elif isinstance(err, str):
            msg = err[:1200]
        else:
            msg = (resp.text or "")[:800] or f"HTTP {resp.status_code}"
        return JSONResponse({"error": msg}, status_code=502)
    out = _chat_completion_choice_text(data if isinstance(data, dict) else {}).strip()
    if not out:
        return JSONResponse({"error": "Empty response from model."}, status_code=502)
    try:
        from token_usage import chat_usage_in_out, record_token_usage

        u = data.get("usage") if isinstance(data, dict) else None
        inp_i, out_i = chat_usage_in_out(u if isinstance(u, dict) else None)
        if inp_i is not None or out_i is not None:
            resolved = str((data if isinstance(data, dict) else {}).get("model") or model).strip()
            record_token_usage(
                hermes_provider,
                resolved or model,
                inp_i,
                out_i,
                "cron",
                "optimize-prompt",
                animus_client="prompt-optimizer",
            )
    except Exception:
        pass
    return JSONResponse({"ok": True, "prompt": out})


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
        Route("/api/cron/optimize-prompt", cron_optimize_prompt_api, methods=["POST"]),
    ]
