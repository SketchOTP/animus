"""SKILL.md path resolution for the skills raw editor (shared with skills_routes)."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Optional, Tuple

_SKILL_MD_MAX_BYTES = 2 * 1024 * 1024


def resolve_skill_md_path(raw: str, *, must_exist: bool) -> Tuple[Optional[Path], Optional[str]]:
    """Return ``(resolved_path, None)`` or ``(None, reason)`` for SKILL.md under Hermes skill roots."""
    from agent.skill_utils import get_external_skills_dirs
    from tools.skills_tool import SKILLS_DIR, _EXCLUDED_SKILL_DIRS

    if not (raw or "").strip():
        return None, "empty"
    try:
        rp = Path(raw.strip()).expanduser().resolve()
    except Exception:
        return None, "invalid"
    if rp.name != "SKILL.md":
        return None, "not_skill_md"
    if _EXCLUDED_SKILL_DIRS & set(rp.parts):
        return None, "excluded"

    roots = []
    try:
        if SKILLS_DIR.exists():
            roots.append(SKILLS_DIR.resolve())
    except Exception:
        pass
    for d in get_external_skills_dirs():
        try:
            p = Path(d).expanduser().resolve()
            if p.exists():
                roots.append(p)
        except Exception:
            pass
    if not roots:
        return None, "no_roots"

    def _under_any(target: Path) -> bool:
        for root in roots:
            try:
                target.relative_to(root)
                return True
            except ValueError:
                continue
        return False

    if rp.is_file():
        if not _under_any(rp):
            return None, "outside"
        return rp, None
    if must_exist:
        return None, "not_found"
    try:
        pr = rp.parent.resolve()
    except Exception:
        return None, "invalid"
    if not pr.is_dir():
        return None, "missing_parent"
    if not _under_any(pr):
        return None, "outside"
    return rp, None


async def skills_raw_get(req):
    from starlette.responses import JSONResponse

    raw = req.query_params.get("path", "").strip()
    rp, err = resolve_skill_md_path(raw, must_exist=True)
    if err == "not_found":
        return JSONResponse({"error": "Not found"}, status_code=404)
    if rp is None:
        return JSONResponse({"error": "Invalid or disallowed path"}, status_code=403)
    try:
        data = rp.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return JSONResponse({"error": "read failed"}, status_code=500)
    if len(data.encode("utf-8")) > _SKILL_MD_MAX_BYTES:
        return JSONResponse({"error": "File too large"}, status_code=413)
    return JSONResponse({"path": str(rp), "content": data})


async def skills_raw_put(req):
    from starlette.responses import JSONResponse

    try:
        body = await req.json()
    except Exception:
        return JSONResponse({"error": "invalid json"}, status_code=400)
    raw = str(body.get("path", "") or "").strip()
    content = body.get("content")
    if not isinstance(content, str):
        return JSONResponse({"error": "content must be a string"}, status_code=400)
    blob = content.encode("utf-8")
    if len(blob) > _SKILL_MD_MAX_BYTES:
        return JSONResponse({"error": "Content too large"}, status_code=413)

    rp, err = resolve_skill_md_path(raw, must_exist=False)
    if rp is None:
        return JSONResponse({"error": "Invalid or disallowed path"}, status_code=403)

    tmp_path = None
    try:
        fd, tmp_path = tempfile.mkstemp(
            prefix=".skill_edit_",
            suffix=".tmp",
            dir=str(rp.parent),
        )
        try:
            os.write(fd, blob)
            os.fsync(fd)
        finally:
            os.close(fd)
        os.replace(tmp_path, rp)
        tmp_path = None
        return JSONResponse({"ok": True, "path": str(rp)})
    except Exception:
        if tmp_path:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
        return JSONResponse({"error": "write failed"}, status_code=500)
