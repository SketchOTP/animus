from __future__ import annotations

from animus.plugins.governance_hub.proxy import governance_health, governance_proxy


def governance_hub_route_table() -> list:
    from starlette.routing import Route

    return [
        Route("/api/governance/health", governance_health, methods=["GET"]),
        Route("/api/governance/{path:path}", governance_proxy, methods=["GET", "POST", "PUT", "PATCH"]),
    ]
