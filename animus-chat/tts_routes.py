"""TTS helpers — browser vs local Piper (optional binary)."""

from __future__ import annotations

import asyncio
import logging
import os
import shutil
import threading
import subprocess  # exempt: piper subprocess for WAV synthesis
import tempfile
from pathlib import Path
from typing import Any

import httpx
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

log = logging.getLogger("animus.tts")

_HF_VOICE_BASE = (
    os.environ.get("PIPER_VOICE_HF_BASE", "").strip().rstrip("/")
    or "https://huggingface.co/rhasspy/piper-voices/resolve/main"
)
# (HF relative path without leading slash, onnx stem)
_DEFAULT_VOICE_PAIRS: tuple[tuple[str, str], ...] = (
    ("en/en_GB/alan/medium/en_GB-alan-medium", "en_GB-alan-medium"),
    ("en/en_US/lessac/medium/en_US-lessac-medium", "en_US-lessac-medium"),
    ("en/en_US/amy/medium/en_US-amy-medium", "en_US-amy-medium"),
    ("en/en_US/ryan/medium/en_US-ryan-medium", "en_US-ryan-medium"),
    ("en/en_US/norman/medium/en_US-norman-medium", "en_US-norman-medium"),
    ("de/de_DE/thorsten/medium/de_DE-thorsten-medium", "de_DE-thorsten-medium"),
)

_piper_schedule_lock = threading.Lock()
_voice_fetch_task: asyncio.Task[Any] | None = None
_voice_dl_state: str = "idle"  # idle | running | ok | error
_voice_dl_error: str | None = None


def _piper_bin() -> str | None:
    override = (os.environ.get("PIPER_BIN") or "").strip()
    if override:
        p = Path(override).expanduser()
        if p.is_file():
            return str(p)
        w = shutil.which(override)
        return w
    return shutil.which("piper")


def _piper_voice_dirs() -> list[Path]:
    raw = (os.environ.get("PIPER_VOICES_DIR") or "").strip()
    dirs: list[Path] = []
    if raw:
        dirs.append(Path(raw).expanduser().resolve())
    home = Path.home()
    for rel in (
        ".local/share/piper",
        ".piper/voices",
        ".cache/piper",
        "piper-voices",
    ):
        dirs.append((home / rel).resolve())
    return dirs


def _default_voice_install_dir() -> Path:
    raw = (os.environ.get("PIPER_VOICES_DIR") or "").strip()
    if raw:
        p = Path(raw).expanduser().resolve()
    else:
        p = (Path.home() / ".local/share/piper").resolve()
    p.mkdir(parents=True, exist_ok=True)
    return p


def _download_hf_file(client: httpx.Client, rel_url: str, dest: Path) -> None:
    """Stream download from HF. Skips if dest exists and non-empty."""
    if dest.is_file() and dest.stat().st_size > 0:
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    url = f"{_HF_VOICE_BASE}/{rel_url.lstrip('/')}"
    tmp = dest.with_suffix(dest.suffix + f".partial.{os.getpid()}")
    try:
        with client.stream("GET", url) as r:
            r.raise_for_status()
            with tmp.open("wb") as out:
                for chunk in r.iter_bytes(65536):
                    if chunk:
                        out.write(chunk)
        tmp.replace(dest)
    except Exception:
        try:
            tmp.unlink(missing_ok=True)
        except OSError:
            pass
        raise


def _ensure_default_piper_voices_sync() -> None:
    """Download default Piper onnx+json into the primary voice dir when missing."""
    if (os.environ.get("SKIP_ANIMUS_PIPER_VOICES") or "").strip() == "1":
        log.info("Piper voices: SKIP_ANIMUS_PIPER_VOICES=1 — not downloading.")
        return
    if not _piper_bin():
        return
    if _collect_piper_voice_files():
        return
    dest_dir = _default_voice_install_dir()
    log.info("Piper: downloading default voice bundle into %s", dest_dir)
    to = httpx.Timeout(900.0, connect=30.0)
    with httpx.Client(follow_redirects=True, timeout=to) as client:
        for relp, stem in _DEFAULT_VOICE_PAIRS:
            onnx = dest_dir / f"{stem}.onnx"
            jsn = dest_dir / f"{stem}.onnx.json"
            _download_hf_file(client, f"{relp}.onnx", onnx)
            _download_hf_file(client, f"{relp}.onnx.json", jsn)
    n = len(_collect_piper_voice_files())
    log.info("Piper: voice bundle finished (%d model(s) visible to scanner)", n)


def _collect_piper_voice_files() -> list[dict]:
    out: list[dict] = []
    seen: set[str] = set()
    for base in _piper_voice_dirs():
        if not base.is_dir():
            continue
        try:
            for p in base.rglob("*.onnx"):
                if not p.is_file():
                    continue
                sid = p.stem
                if sid in seen:
                    continue
                seen.add(sid)
                out.append({"id": sid, "path": str(p), "label": sid.replace("_", " ")})
        except OSError:
            continue
    out.sort(key=lambda x: str(x.get("id") or "").lower())
    return out


async def _background_piper_voice_fetch() -> None:
    global _voice_dl_state, _voice_dl_error, _voice_fetch_task  # noqa: PLW0603
    if (os.environ.get("SKIP_ANIMUS_PIPER_VOICES") or "").strip() == "1":
        _voice_dl_state = "idle"
        return
    if not _piper_bin():
        _voice_dl_state = "idle"
        return
    if _collect_piper_voice_files():
        _voice_dl_state = "ok"
        _voice_dl_error = None
        return
    _voice_dl_state = "running"
    _voice_dl_error = None
    try:
        await asyncio.to_thread(_ensure_default_piper_voices_sync)
        if _collect_piper_voice_files():
            _voice_dl_state = "ok"
        else:
            _voice_dl_state = "error"
            _voice_dl_error = "download finished but no .onnx models found"
    except Exception as exc:
        log.exception("Piper default voice download failed")
        _voice_dl_state = "error"
        _voice_dl_error = str(exc)[:500]
    finally:
        _voice_fetch_task = None


async def schedule_default_piper_voices_if_needed() -> None:
    """Start at most one background download when Piper is installed but no models exist."""
    global _voice_fetch_task, _voice_dl_state  # noqa: PLW0603
    if (os.environ.get("SKIP_ANIMUS_PIPER_VOICES") or "").strip() == "1":
        return
    if not _piper_bin():
        return
    if _collect_piper_voice_files():
        _voice_dl_state = "ok"
        return
    with _piper_schedule_lock:
        if _voice_fetch_task is not None and not _voice_fetch_task.done():
            return
        loop = asyncio.get_running_loop()
        _voice_fetch_task = loop.create_task(_background_piper_voice_fetch())


def _voices_payload() -> dict[str, Any]:
    voices = _collect_piper_voice_files()
    t = _voice_fetch_task
    fetching = _voice_dl_state == "running" or (t is not None and not t.done())
    return {
        "voices": voices,
        "fetching": fetching,
        "fetch_error": _voice_dl_error if _voice_dl_state == "error" else None,
    }


async def tts_backends_api(_req: Request) -> Response:
    backends = ["browser"]
    if _piper_bin():
        backends.append("piper")
    return JSONResponse({"backends": backends})


async def tts_piper_voices_api(_req: Request) -> Response:
    if not _piper_bin():
        return JSONResponse({"voices": [], "error": "piper not installed", "fetching": False, "fetch_error": None})
    await schedule_default_piper_voices_if_needed()
    return JSONResponse(_voices_payload())


async def tts_piper_speak_api(req: Request) -> Response:
    if not _piper_bin():
        return JSONResponse({"ok": False, "error": "piper not installed"}, status_code=400)
    try:
        body = await req.json()
    except Exception:
        body = {}
    text = str(body.get("text") or "").strip()
    voice = str(body.get("voice") or "").strip()
    if not text:
        return JSONResponse({"ok": False, "error": "text is required"}, status_code=400)
    await schedule_default_piper_voices_if_needed()
    # Brief wait if download just started (best-effort — client should retry)
    for _ in range(30):
        voices = {v["id"]: v["path"] for v in _collect_piper_voice_files()}
        if voice in voices:
            break
        if _voice_dl_state != "running":
            break
        await asyncio.sleep(1.0)
    voices = {v["id"]: v["path"] for v in _collect_piper_voice_files()}
    model_path = voices.get(voice)
    if not model_path:
        if _voice_dl_state == "running":
            return JSONResponse(
                {"ok": False, "error": "Piper voices are still downloading — try again in a minute."},
                status_code=503,
            )
        return JSONResponse({"ok": False, "error": "unknown voice"}, status_code=400)
    tmp = Path(tempfile.mkstemp(prefix="animus-piper-", suffix=".wav")[1])
    try:
        proc = subprocess.run(  # exempt: piper one-shot WAV synthesis
            [_piper_bin(), "-m", model_path, "-f", str(tmp)],
            input=text,
            capture_output=True,
            text=True,
            timeout=120,
        )
        if proc.returncode != 0 or not tmp.is_file() or tmp.stat().st_size == 0:
            err = (proc.stderr or proc.stdout or "piper failed").strip()
            return JSONResponse({"ok": False, "error": err[:800]}, status_code=500)
        data = tmp.read_bytes()
        return Response(data, media_type="audio/wav")
    except subprocess.TimeoutExpired:
        return JSONResponse({"ok": False, "error": "piper timed out"}, status_code=504)
    except Exception as exc:
        log.exception("tts_piper_speak failed")
        return JSONResponse({"ok": False, "error": str(exc)}, status_code=500)
    finally:
        try:
            tmp.unlink(missing_ok=True)  # type: ignore[arg-type]
        except OSError:
            pass


def tts_route_table():
    from starlette.routing import Route

    return [
        Route("/api/tts/backends", tts_backends_api, methods=["GET"]),
        Route("/api/tts/piper/voices", tts_piper_voices_api, methods=["GET"]),
        Route("/api/tts/piper/speak", tts_piper_speak_api, methods=["POST"]),
    ]
