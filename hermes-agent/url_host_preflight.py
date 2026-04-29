"""Patch a stale ``utils`` module with URL hostname helpers before other imports.

Stale ``~/.hermes/hermes-agent`` trees sometimes ship an older ``utils.py`` that
omits ``base_url_host_matches`` while ``gateway/run.py`` and ``run_agent`` expect
it.  Call :func:`apply` immediately after ``sys.path`` is seeded so the gateway
and cron ticker can run without manual intervention.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def apply() -> bool:
    """If ``utils`` lacks URL helpers, copy them from ``url_host_utils``.

    Returns:
        True if ``utils`` already had both helpers or patching succeeded.
    """
    try:
        import utils as u
    except Exception as exc:
        logger.warning("url_host_preflight: cannot import utils: %s", exc)
        return False
    has_matches = hasattr(u, "base_url_host_matches") and callable(
        getattr(u, "base_url_host_matches", None)
    )
    has_hostname = hasattr(u, "base_url_hostname") and callable(
        getattr(u, "base_url_hostname", None)
    )
    if has_matches and has_hostname:
        return True
    try:
        import url_host_utils as h

        u.base_url_host_matches = h.base_url_host_matches
        u.base_url_hostname = h.base_url_hostname
        logger.info("url_host_preflight: patched utils from url_host_utils")
        return True
    except Exception as exc:
        logger.warning(
            "url_host_preflight: utils missing URL helpers and patch failed: %s",
            exc,
        )
        return False
