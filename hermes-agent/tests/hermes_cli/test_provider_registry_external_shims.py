"""Guardrail: ``hermes_provider`` on /v1/chat/completions must resolve.

Gateway + ANIMUS send ``hermes_provider`` from the UI; resolution uses
``resolve_provider_full`` → ``get_provider`` / ``HERMES_OVERLAYS``.
Subprocess shims (``external_process`` in ``PROVIDER_REGISTRY``) are not
on models.dev — they *must* have a Hermes overlay or users see
``Unknown provider`` / empty SSE replies.
"""

from __future__ import annotations

import pytest

from hermes_cli.auth import PROVIDER_REGISTRY
from hermes_cli.providers import HERMES_OVERLAYS, resolve_provider_full


@pytest.mark.parametrize(
    "provider_id",
    sorted(
        pid
        for pid, cfg in PROVIDER_REGISTRY.items()
        if getattr(cfg, "auth_type", "") == "external_process"
    ),
)
def test_external_process_provider_has_overlay_and_resolves(provider_id: str) -> None:
    assert provider_id in HERMES_OVERLAYS, (
        f"PROVIDER_REGISTRY declares external_process provider {provider_id!r} but "
        f"HERMES_OVERLAYS has no entry. Add HermesOverlay for it in "
        f"hermes_cli/providers.py (gateway /v1/chat/completions + ANIMUS)."
    )
    pdef = resolve_provider_full(provider_id, {}, None)
    assert pdef is not None, f"resolve_provider_full({provider_id!r}) returned None"
    assert pdef.id == provider_id
    assert pdef.transport in ("openai_chat", "codex_responses", "anthropic_messages")
