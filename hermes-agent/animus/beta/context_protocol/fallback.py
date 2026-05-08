from __future__ import annotations

from dataclasses import dataclass


@dataclass
class BetaFallback:
    used: bool
    reason: str | None = None


def fallback(reason: str | None) -> BetaFallback:
    return BetaFallback(used=True, reason=reason or "unknown")

