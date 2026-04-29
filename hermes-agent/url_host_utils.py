"""Hostname-safe URL matching for provider routing (split out for partial deploys).

Cron and gateways occasionally run from a ``~/.hermes/hermes-agent`` tree that
lags ``main``.  If ``utils.py`` predates ``base_url_host_matches`` but this
module is present, ``cron.scheduler`` patches ``utils`` before importing
``run_agent``.
"""

from __future__ import annotations

from urllib.parse import urlparse


def base_url_hostname(base_url: str) -> str:
    """Return the lowercased hostname for a base URL, or ``""`` if absent."""
    raw = (base_url or "").strip()
    if not raw:
        return ""
    parsed = urlparse(raw if "://" in raw else f"//{raw}")
    return (parsed.hostname or "").lower().rstrip(".")


def base_url_host_matches(base_url: str, domain: str) -> bool:
    """Return True when the base URL's hostname is ``domain`` or a subdomain."""
    hostname = base_url_hostname(base_url)
    if not hostname:
        return False
    domain = (domain or "").strip().lower().rstrip(".")
    if not domain:
        return False
    return hostname == domain or hostname.endswith("." + domain)
