from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import asdict
from datetime import datetime, timezone

from .schema import BetaDecisionLog

logger = logging.getLogger("animus.beta.context_protocol")


def now_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat().replace("+00:00", "Z")


def prompt_hash(prompt: str) -> str:
    digest = hashlib.sha256((prompt or "").encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def estimate_context_tokens(text: str) -> int:
    # Rough tokenizer fallback: ~4 chars/token.
    return max(0, int(len(text or "") / 4))


def log_decision(decision_log: BetaDecisionLog, *, full_prompt: str | None = None, log_full_prompts: bool = False) -> None:
    payload = asdict(decision_log)
    if log_full_prompts and full_prompt is not None:
        payload["prompt"] = full_prompt
    logger.info("beta_context_protocol %s", json.dumps(payload, ensure_ascii=False))

