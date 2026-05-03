"""Skills API — in-process skill discovery + ``hermes skills`` CLI for mutations."""

from __future__ import annotations

import json
import logging
import os
import re
import urllib.parse
from pathlib import Path
from typing import Any

from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from hermes_runner import append_audit, chat_data_dir, run_hermes
from hermes_service_client import (
    dashboard_get_skills,
    dashboard_put_skill_toggle,
    gateway_http_json,
    hermes_dashboard_session_token,
)
from skills_md import skills_raw_get, skills_raw_put

log = logging.getLogger("animus.skills")

_ANIMUS_BARE_MIN_TOOL_NAMES = [
    "terminal",
    "read_file",
    "write_file",
    "patch",
    "search_files",
    "process",
    "execute_code",
    "delegate_task",
    "todo",
]


def _animus_client_config_path() -> Path:
    return chat_data_dir() / "config.json"


def _read_animus_client_config() -> dict:
    p = _animus_client_config_path()
    if not p.is_file():
        return {}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def _write_animus_client_config(cfg: dict) -> None:
    p = _animus_client_config_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(cfg, indent=2), encoding="utf-8")


def _animus_disabled_tools_from_cfg(cfg: dict) -> set[str]:
    ui = cfg.get("animus_ui_settings")
    if not isinstance(ui, dict):
        return set()
    raw = ui.get("disabled_tools")
    if not isinstance(raw, list):
        return set()
    out: set[str] = set()
    for item in raw:
        nm = str(item or "").strip()
        if nm:
            out.add(nm)
    return out


def _set_animus_disabled_tools(disabled_tools: set[str]) -> None:
    cfg = _read_animus_client_config()
    ui = cfg.get("animus_ui_settings")
    if not isinstance(ui, dict):
        ui = {}
    ui = dict(ui)
    ui["disabled_tools"] = sorted(disabled_tools)
    cfg["animus_ui_settings"] = ui
    _write_animus_client_config(cfg)


def _skills_tree_has_any_skill_md(skills_root: Path) -> bool:
    """True if *skills_root* contains at least one ``SKILL.md`` (any category)."""
    if not skills_root.is_dir():
        return False
    for _dirpath, dirnames, filenames in os.walk(skills_root):
        dirnames[:] = [d for d in dirnames if d not in {".git", ".github", ".hub"}]
        if "SKILL.md" in filenames:
            return True
    return False


def _ensure_bundled_skills_seeded_if_needed() -> None:
    """Run manifest-based bundled sync when the user tree was never populated.

    Covers:

    - Import-time ``sync_skills`` in ``server.py`` failed (no manifest).
    - A **wrote manifest but copied nothing** case: first boot had no bundled
      skills on disk (wrong ``HERMES_AGENT_DIR`` / incomplete tree), so
      ``.bundled_manifest`` exists but is **empty** while there is no
      ``SKILL.md`` under ``HERMES_HOME/skills``. Previously we skipped forever.

    Does **not** re-seed when the manifest is non-empty and there are no
    ``SKILL.md`` files (Hermes treats that as “user removed skills”).
    """
    try:
        from hermes_constants import get_hermes_home
        from tools.skills_sync import (
            _discover_bundled_skills,
            _get_bundled_dir,
            _read_manifest,
            sync_skills,
        )

        skills_root = get_hermes_home() / "skills"
        manifest_path = skills_root / ".bundled_manifest"
        bundled_dir = _get_bundled_dir()
        bundled_n = (
            len(_discover_bundled_skills(bundled_dir)) if bundled_dir.is_dir() else 0
        )

        needs_sync = not manifest_path.is_file()
        if (
            not needs_sync
            and bundled_n > 0
            and not _skills_tree_has_any_skill_md(skills_root)
        ):
            try:
                mf = _read_manifest()
            except Exception:
                mf = {}
            if not mf:
                needs_sync = True

        if not needs_sync:
            return
        sync_skills(quiet=True)
    except Exception:
        log.debug("Bundled skills seed-on-list failed", exc_info=True)


def _audit(op: str, **parts: str) -> None:
    bits = " ".join(f"{k}={v}" for k, v in parts.items())
    append_audit("skills_audit.log", f"{op}  {bits}")


def _normalize_skills_list(skills: list) -> list:
    out = []
    for s in skills:
        if not isinstance(s, dict):
            continue
        row = dict(s)
        nm = str(row.get("name") or "").strip()
        row["id"] = nm
        row.setdefault("enabled", True)
        row.setdefault("version", "")
        row.setdefault("source", "local")
        row.setdefault("last_updated", "")
        row.setdefault("path", row.get("path") or "")
        out.append(row)
    return out


async def skills_list_api(_req: Request) -> Response:
    try:
        _ensure_bundled_skills_seeded_if_needed()
        # Prefer Hermes gateway skills service so the UI reflects runtime truth.
        st_gw, data_gw = await gateway_http_json("GET", "/api/skills/list", timeout=30.0)
        if st_gw == 200:
            if isinstance(data_gw, list):
                return JSONResponse(_normalize_skills_list(data_gw))
            if isinstance(data_gw, dict):
                rows = data_gw.get("skills")
                if isinstance(rows, list):
                    return JSONResponse(_normalize_skills_list(rows))
        elif st_gw not in (0, 404, 401):
            log.warning("gateway GET /api/skills/list returned %s: %s", st_gw, data_gw)

        if hermes_dashboard_session_token():
            st, data = await dashboard_get_skills()
            if st == 200 and isinstance(data, list):
                return JSONResponse(_normalize_skills_list(data))
            if st not in (0, 401):
                log.warning("dashboard GET /api/skills returned %s: %s", st, data)

        from tools.skills_tool import _find_all_skills, _get_disabled_skill_names

        disabled = _get_disabled_skill_names()
        skills = _find_all_skills(skip_disabled=True, include_paths=True)
        for s in skills:
            nm = str(s.get("name") or "").strip()
            s["id"] = nm
            s["enabled"] = nm not in disabled if nm else True
            s.setdefault("version", "")
            s.setdefault("source", "local")
            s.setdefault("last_updated", "")
        return JSONResponse(skills)
    except Exception as exc:
        log.exception("skills_list_api failed")
        return JSONResponse({"error": str(exc)}, status_code=500)


def _skill_body_after_frontmatter(text: str) -> str:
    if not text.strip().startswith("---"):
        return text
    parts = text.split("---", 2)
    if len(parts) >= 3:
        return parts[2].lstrip("\n")
    return text


async def skills_detail_api(req: Request) -> Response:
    sid = urllib.parse.unquote(req.path_params["skill_id"])
    res = run_hermes(["skills", "inspect", sid], timeout=60)
    raw = (res.get("stdout") or "") + ("\n" + (res.get("stderr") or "") if res.get("stderr") else "")
    path_hint: str | None = None
    try:
        from tools.skills_tool import _find_all_skills

        for row in _find_all_skills(skip_disabled=True, include_paths=True):
            if str(row.get("name") or "").strip() == sid:
                path_hint = str(row.get("path") or "").strip() or None
                break
    except Exception:
        path_hint = None

    readme = ""
    description = ""
    version = ""
    if path_hint:
        try:
            p = Path(path_hint)
            if p.is_file():
                full = p.read_text(encoding="utf-8", errors="replace")
                readme = _skill_body_after_frontmatter(full)
                if "---" in full[:4000]:
                    try:
                        fm_block = full.split("---", 2)[1]
                        for line in fm_block.splitlines():
                            if ":" in line:
                                k, _, v = line.partition(":")
                                k, v = k.strip().lower(), v.strip().strip('"').strip("'")
                                if k == "description":
                                    description = v
                                if k == "version":
                                    version = v
                    except Exception:
                        pass
        except OSError:
            readme = ""

    if not description and raw:
        m = re.search(r"(?im)^description:\s*(.+)$", raw)
        if m:
            description = m.group(1).strip()

    payload: dict[str, Any] = {
        "ok": res["ok"],
        "id": sid,
        "name": sid,
        "version": version or "",
        "description": description or "",
        "category": "",
        "readme": readme or (raw if res["ok"] else ""),
        "raw": raw.strip(),
        "path": path_hint,
    }
    if not res["ok"]:
        payload["error"] = res["stderr"] or res["stdout"] or "inspect failed"
        return JSONResponse(payload, status_code=404)
    return JSONResponse(payload)


def _skills_user_dir() -> Path:
    try:
        from hermes_constants import get_hermes_home  # type: ignore

        return Path(get_hermes_home()) / "skills"
    except Exception:
        from pathlib import Path as _P

        return _P.home() / ".hermes" / "skills"


_SKILL_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,62}$")


async def skills_create_api(req: Request) -> Response:
    try:
        body = await req.json()
    except Exception:
        body = {}
    raw_name = str(body.get("name") or "").strip().lower().replace(" ", "-")
    if not raw_name or not _SKILL_NAME_RE.match(raw_name):
        return JSONResponse({"ok": False, "error": "Skill name must be lowercase letters, digits, hyphens only."}, status_code=400)
    display = str(body.get("display_name") or raw_name).strip() or raw_name
    desc = str(body.get("description") or "").strip()
    ver = str(body.get("version") or "1.0.0").strip() or "1.0.0"
    content = str(body.get("content") or "").strip()
    base = _skills_user_dir()
    skill_dir = (base / raw_name).resolve()
    try:
        base_r = base.resolve()
        skill_dir.relative_to(base_r)
    except (OSError, ValueError):
        return JSONResponse({"ok": False, "error": "Invalid skills path"}, status_code=400)
    if skill_dir.exists():
        return JSONResponse({"ok": False, "error": f"Skill '{raw_name}' already exists"}, status_code=400)
    try:
        skill_dir.mkdir(parents=True, exist_ok=False)
        def _dq(s: str) -> str:
            return '"' + s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'

        nm = raw_name[:64]
        dsc = (desc or f"User-created skill {raw_name}")[:1024]
        vr = ver[:32]
        body_md = content if content else f"# {display}\n\nDescribe what this skill does.\n"
        skill_md = (
            "---\n"
            f"name: {_dq(nm)}\n"
            f"description: {_dq(dsc)}\n"
            f"version: {_dq(vr)}\n"
            "---\n\n"
            + body_md
        )
        (skill_dir / "SKILL.md").write_text(skill_md, encoding="utf-8")
    except OSError as exc:
        _audit("CREATE_FAIL", name=raw_name, detail=str(exc)[:200])
        return JSONResponse({"ok": False, "error": str(exc)}, status_code=500)
    _audit("CREATE", skill_id=raw_name, result="ok")
    return JSONResponse({"ok": True, "id": raw_name})


async def skills_install_api(req: Request) -> Response:
    try:
        body = await req.json()
    except Exception:
        body = {}
    source = str(body.get("source") or "").strip()
    if not source:
        return JSONResponse({"ok": False, "error": "source is required"}, status_code=400)
    res = run_hermes(["skills", "install", source], timeout=120)
    _audit("INSTALL", source=source[:200], result="ok" if res["ok"] else "error")
    if not res["ok"]:
        return JSONResponse({"ok": False, "error": res["stderr"] or res["stdout"]}, status_code=400)
    return JSONResponse({"ok": True, "id": None, "stdout": res["stdout"]})


async def skills_update_one_api(req: Request) -> Response:
    sid = urllib.parse.unquote(req.path_params["skill_id"])
    res = run_hermes(["skills", "update", sid], timeout=120)
    _audit("UPDATE", skill_id=sid, result="ok" if res["ok"] else "error")
    if not res["ok"]:
        return JSONResponse({"ok": False, "error": res["stderr"] or res["stdout"]}, status_code=400)
    return JSONResponse({"ok": True, "version_before": "", "version_after": "", "stdout": res["stdout"]})


async def skills_update_all_api(_req: Request) -> Response:
    _ensure_bundled_skills_seeded_if_needed()
    res = run_hermes(["skills", "update"], timeout=300)
    _audit("UPDATE_ALL", result="ok" if res["ok"] else "error")
    if not res["ok"]:
        return JSONResponse({"ok": False, "updated": [], "errors": [res["stderr"] or res["stdout"]]}, status_code=400)
    return JSONResponse({"ok": True, "updated": [], "errors": [], "stdout": res["stdout"]})


async def skills_remove_api(req: Request) -> Response:
    sid = urllib.parse.unquote(req.path_params["skill_id"])
    res = run_hermes(["skills", "uninstall", sid], timeout=120)
    _audit("REMOVE", skill_id=sid, result="ok" if res["ok"] else "error")
    if not res["ok"]:
        return JSONResponse({"ok": False, "error": res["stderr"] or res["stdout"]}, status_code=400)
    return JSONResponse({"ok": True})


async def _skills_set_enabled(skill_id: str, enabled: bool) -> tuple[bool, str]:
    if hermes_dashboard_session_token():
        st, body = await dashboard_put_skill_toggle(skill_id, enabled)
        if st == 200 and isinstance(body, dict) and body.get("ok"):
            return True, ""
        return False, str((body or {}).get("detail") or body or f"HTTP {st}")
    try:
        from hermes_cli.config import load_config
        from hermes_cli.skills_config import get_disabled_skills, save_disabled_skills

        config = load_config()
        disabled = get_disabled_skills(config)
        if enabled:
            disabled.discard(skill_id)
        else:
            disabled.add(skill_id)
        save_disabled_skills(config, disabled)
        return True, ""
    except Exception as exc:
        return False, str(exc)


async def skills_enable_api(req: Request) -> Response:
    sid = urllib.parse.unquote(req.path_params["skill_id"])
    ok, err = await _skills_set_enabled(sid, True)
    _audit("ENABLE", skill_id=sid, result="ok" if ok else "error")
    if ok:
        return JSONResponse({"ok": True})
    return JSONResponse({"ok": False, "error": err or "toggle failed"}, status_code=400)


async def skills_disable_api(req: Request) -> Response:
    sid = urllib.parse.unquote(req.path_params["skill_id"])
    ok, err = await _skills_set_enabled(sid, False)
    _audit("DISABLE", skill_id=sid, result="ok" if ok else "error")
    if ok:
        return JSONResponse({"ok": True})
    return JSONResponse({"ok": False, "error": err or "toggle failed"}, status_code=400)


async def skills_updates_available_api(_req: Request) -> Response:
    res = run_hermes(["skills", "check"], timeout=120)
    text = (res.get("stdout") or "") + "\n" + (res.get("stderr") or "")
    updates: list[dict[str, Any]] = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "→" in line or "->" in line:
            sep = "→" if "→" in line else "->"
            left, _, right = line.partition(sep)
            updates.append(
                {
                    "id": left.strip().split()[-1] if left.strip() else "",
                    "name": left.strip(),
                    "current_version": "",
                    "latest_version": right.strip(),
                }
            )
    return JSONResponse(
        {
            "ok": res["ok"],
            "updates": updates[:50],
            "raw": res.get("stdout") or "",
            "stderr": res.get("stderr") or "",
        }
    )


def _tool_summary(desc: str) -> str:
    s = str(desc or "").strip()
    if not s:
        return ""
    first = s.splitlines()[0].strip()
    if not first:
        return s[:160]
    if len(first) > 220:
        first = first[:217].rstrip() + "..."
    return first


def _load_api_server_tools() -> list[dict[str, Any]]:
    from gateway.run import _load_gateway_config
    from hermes_cli.tools_config import _get_platform_tools
    from model_tools import get_tool_definitions

    cfg = _load_gateway_config()
    enabled_toolsets = sorted(_get_platform_tools(cfg, "api_server"))
    if "skills" not in enabled_toolsets:
        enabled_toolsets = sorted(set(enabled_toolsets) | {"skills"})
    defs = get_tool_definitions(enabled_toolsets=enabled_toolsets, quiet_mode=True)
    rows: list[dict[str, Any]] = []
    for td in defs:
        fn = td.get("function") if isinstance(td, dict) else None
        if not isinstance(fn, dict):
            continue
        name = str(fn.get("name") or "").strip()
        if not name:
            continue
        rows.append(
            {
                "name": name,
                "summary": _tool_summary(str(fn.get("description") or "")),
                "description": str(fn.get("description") or ""),
            }
        )
    rows.sort(key=lambda r: str(r.get("name") or ""))
    return rows


async def tools_list_api(_req: Request) -> Response:
    try:
        cfg = _read_animus_client_config()
        disabled = _animus_disabled_tools_from_cfg(cfg)
        rows: list[dict[str, Any]] = []
        st_gw, data_gw = await gateway_http_json("GET", "/api/tools/list", timeout=30.0)
        if st_gw == 200 and isinstance(data_gw, dict) and isinstance(data_gw.get("tools"), list):
            for row in data_gw.get("tools") or []:
                if not isinstance(row, dict):
                    continue
                nm = str(row.get("name") or "").strip()
                if not nm:
                    continue
                desc = str(row.get("description") or "")
                rows.append(
                    {
                        "name": nm,
                        "summary": _tool_summary(desc),
                        "description": desc,
                    }
                )
        else:
            rows = _load_api_server_tools()
        rows.sort(key=lambda r: str(r.get("name") or ""))
        for r in rows:
            nm = str(r.get("name") or "")
            r["enabled"] = nm not in disabled
        return JSONResponse(
            {
                "tools": rows,
                "disabled_tools": sorted(disabled),
                "bare_minimum_tools": list(_ANIMUS_BARE_MIN_TOOL_NAMES),
            }
        )
    except Exception as exc:
        log.exception("tools_list_api failed")
        return JSONResponse({"error": str(exc)}, status_code=500)


def _set_tool_enabled(tool_id: str, enabled: bool) -> tuple[bool, str]:
    try:
        nm = str(tool_id or "").strip()
        if not nm:
            return False, "tool id required"
        current = _animus_disabled_tools_from_cfg(_read_animus_client_config())
        if enabled:
            current.discard(nm)
        else:
            current.add(nm)
        _set_animus_disabled_tools(current)
        return True, ""
    except Exception as exc:
        return False, str(exc)


async def tools_enable_api(req: Request) -> Response:
    tid = urllib.parse.unquote(req.path_params["tool_id"])
    ok, err = _set_tool_enabled(tid, True)
    if ok:
        return JSONResponse({"ok": True})
    return JSONResponse({"ok": False, "error": err or "toggle failed"}, status_code=400)


async def tools_disable_api(req: Request) -> Response:
    tid = urllib.parse.unquote(req.path_params["tool_id"])
    ok, err = _set_tool_enabled(tid, False)
    if ok:
        return JSONResponse({"ok": True})
    return JSONResponse({"ok": False, "error": err or "toggle failed"}, status_code=400)


async def skills_capabilities_api(_req: Request) -> Response:
    out = {
        "enable_disable_supported": True,
        "check_updates_supported": False,
        "install_supported": False,
    }
    for argv in (["skills", "--help"], ["skill", "--help"]):
        r = run_hermes(list(argv), timeout=12)
        blob = ((r.get("stdout") or "") + "\n" + (r.get("stderr") or "")).lower()
        if not blob.strip():
            continue
        out["install_supported"] = out["install_supported"] or ("install" in blob)
        out["check_updates_supported"] = out["check_updates_supported"] or (
            "check" in blob and "update" in blob
        )
        out["enable_disable_supported"] = out["enable_disable_supported"] or (
            "enable" in blob and "disable" in blob
        )
    return JSONResponse(out)


async def skills_audit_api(req: Request) -> Response:
    from hermes_runner import chat_data_dir

    limit = int(req.query_params.get("limit") or "100")
    path = chat_data_dir() / "skills_audit.log"
    if not path.is_file():
        return JSONResponse({"lines": []})
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()[-limit:]
    return JSONResponse({"lines": lines})


def skills_route_table():
    from starlette.routing import Route

    return [
        Route("/api/tools/list", tools_list_api, methods=["GET"]),
        Route("/api/tools/enable/{tool_id}", tools_enable_api, methods=["POST"]),
        Route("/api/tools/disable/{tool_id}", tools_disable_api, methods=["POST"]),
        Route("/api/skills/capabilities", skills_capabilities_api, methods=["GET"]),
        Route("/api/skills/list", skills_list_api, methods=["GET"]),
        Route("/api/skills/detail/{skill_id}", skills_detail_api, methods=["GET"]),
        Route("/api/skills/create", skills_create_api, methods=["POST"]),
        Route("/api/skills/install", skills_install_api, methods=["POST"]),
        Route("/api/skills/update/{skill_id}", skills_update_one_api, methods=["POST"]),
        Route("/api/skills/update-all", skills_update_all_api, methods=["POST"]),
        Route("/api/skills/remove/{skill_id}", skills_remove_api, methods=["DELETE"]),
        Route("/api/skills/enable/{skill_id}", skills_enable_api, methods=["POST"]),
        Route("/api/skills/disable/{skill_id}", skills_disable_api, methods=["POST"]),
        Route("/api/skills/updates-available", skills_updates_available_api, methods=["GET"]),
        Route("/api/skills/audit", skills_audit_api, methods=["GET"]),
        Route("/api/skills/raw", skills_raw_get, methods=["GET"]),
        Route("/api/skills/raw", skills_raw_put, methods=["PUT"]),
    ]
