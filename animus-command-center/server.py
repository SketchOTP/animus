"""Dedicated Animus Command Center dev server (D-140).

Serves the visual dashboard shell and proxies /api/governance/* to governance-api.
Does not modify the chat PWA overlay.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:

    def load_dotenv(*_a, **_k):
        return False


_PACKAGE_DIR = Path(__file__).resolve().parent
_MONOREPO_ROOT = _PACKAGE_DIR.parent
_APP_DIR = _PACKAGE_DIR / "app"

for _env_name in ("animus.env", "command-center.env"):
    _env_path = _MONOREPO_ROOT / _env_name
    if _env_path.is_file():
        load_dotenv(_env_path, override=False)

if str(_MONOREPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_MONOREPO_ROOT))

import uvicorn
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles

COMMAND_CENTER_REV = "20260614-d140-command-center-shell-v1"
HOST = (os.environ.get("COMMAND_CENTER_HOST") or "0.0.0.0").strip() or "0.0.0.0"
PORT = int(os.environ.get("COMMAND_CENTER_PORT", "3010"))

_GOVERNANCE_HUB_ROUTES: list = []
_GOVERNANCE_HUB_IMPORT_ERROR: str | None = None

try:
    from animus.plugins.governance_hub.routes import governance_hub_route_table

    _GOVERNANCE_HUB_ROUTES = governance_hub_route_table()
    if not _GOVERNANCE_HUB_ROUTES:
        _GOVERNANCE_HUB_IMPORT_ERROR = "governance_hub_route_table() returned no routes"
        _GOVERNANCE_HUB_ROUTES = []
except Exception as exc:
    _GOVERNANCE_HUB_ROUTES = []
    _GOVERNANCE_HUB_IMPORT_ERROR = str(exc) or type(exc).__name__


async def healthz(_: Request) -> JSONResponse:
    return JSONResponse(
        {
            "status": "ok",
            "service": "animus_command_center",
            "rev": COMMAND_CENTER_REV,
            "governance_proxy": bool(_GOVERNANCE_HUB_ROUTES),
            "governance_proxy_error": _GOVERNANCE_HUB_IMPORT_ERROR,
        }
    )


async def meta(_: Request) -> JSONResponse:
    return JSONResponse(
        {
            "app": "animus-command-center",
            "rev": COMMAND_CENTER_REV,
            "port": PORT,
            "governance_api_url": os.environ.get("GOVERNANCE_API_URL", "http://127.0.0.1:8120"),
        }
    )


app = Starlette(
    routes=[
        Route("/healthz", healthz, methods=["GET"]),
        Route("/api/command-center/meta", meta, methods=["GET"]),
        *_GOVERNANCE_HUB_ROUTES,
        Mount("/", StaticFiles(directory=str(_APP_DIR), html=True)),
    ],
)


def main() -> None:
    uvicorn.run(app, host=HOST, port=PORT, log_level="info")


if __name__ == "__main__":
    main()
