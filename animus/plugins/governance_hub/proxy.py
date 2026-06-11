"""HTTP proxy to animus-platform governance-api (read-only BFF)."""

from __future__ import annotations

import os
from typing import Any

import httpx
from starlette.requests import Request
from starlette.responses import JSONResponse, Response


def governance_api_base() -> str:
    return os.environ.get("GOVERNANCE_API_URL", "http://127.0.0.1:8120").rstrip("/")


async def governance_proxy(request: Request) -> Response:
    """Proxy /api/governance/* to governance-api — no repo filesystem reads in animus-chat."""
    tail = str(request.path_params.get("path") or "").lstrip("/")
    query = str(request.url.query)
    url = f"{governance_api_base()}/api/governance/{tail}"
    if query:
        url = f"{url}?{query}"
    headers = {"Accept": "application/json"}
    body: bytes | None = None
    if request.method in ("POST", "PUT", "PATCH"):
        body = await request.body()
        ct = request.headers.get("content-type")
        if ct:
            headers["Content-Type"] = ct
    timeout = httpx.Timeout(connect=5.0, read=60.0, write=15.0, pool=5.0)
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            upstream = await client.request(request.method, url, headers=headers, content=body)
    except httpx.RequestError as exc:
        return JSONResponse(
            {
                "ok": False,
                "error": "governance_api_unreachable",
                "detail": str(exc),
                "governance_api_url": governance_api_base(),
            },
            status_code=502,
        )
    content_type = upstream.headers.get("content-type", "application/json")
    if "application/json" in content_type:
        try:
            payload: Any = upstream.json()
        except Exception:
            payload = {"raw": upstream.text}
        return JSONResponse(payload, status_code=upstream.status_code)
    return Response(content=upstream.content, status_code=upstream.status_code, media_type=content_type)


async def governance_health(_request: Request) -> Response:
    url = f"{governance_api_base()}/healthz"
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(4.0)) as client:
            resp = await client.get(url)
    except httpx.RequestError as exc:
        return JSONResponse(
            {
                "ok": False,
                "service": "governance_proxy",
                "governance_api_url": governance_api_base(),
                "error": str(exc),
            },
            status_code=502,
        )
    return JSONResponse(
        {
            "ok": resp.status_code == 200,
            "service": "governance_proxy",
            "governance_api_url": governance_api_base(),
            "upstream_status": resp.status_code,
            "upstream": resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {},
        }
    )
