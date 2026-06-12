"""Shared Architect pre-commit gate checks (diff + release freshness)."""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


class GateBlocked(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


def _parse_iso(ts: str) -> datetime | None:
    text = str(ts or "").strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def check_architect_gate(
    *,
    active: dict[str, Any],
    review: dict[str, Any],
    release_state: dict[str, Any] | None,
) -> str:
    """Return success line or raise GateBlocked."""
    request_id = str(active.get("request_id") or "").strip()
    if not request_id:
        raise GateBlocked("architect-gate: BLOCKED — active_request.json has no request_id")

    if review.get("request_id") != request_id:
        raise GateBlocked(
            f"architect-gate: BLOCKED — last_review request_id {review.get('request_id')!r} "
            f"does not match active {request_id!r}"
        )

    if review.get("review_type") != "diff":
        raise GateBlocked(
            f"architect-gate: BLOCKED — last_review review_type={review.get('review_type')!r}; need 'diff'"
        )

    if review.get("status") != "APPROVED":
        raise GateBlocked(
            f"architect-gate: BLOCKED — diff gate status={review.get('status')!r}; need APPROVED"
        )

    if not release_state:
        raise GateBlocked(
            "architect-gate: BLOCKED — missing .architect/release_state.json; "
            "run architect_release_gate before commit"
        )

    release_status = str(release_state.get("last_release_status") or "").strip()
    if release_status != "RELEASE_APPROVED":
        raise GateBlocked(
            f"architect-gate: BLOCKED — release gate status={release_status!r}; need RELEASE_APPROVED"
        )

    release_at = _parse_iso(str(release_state.get("last_release_at") or ""))
    diff_review_at = _parse_iso(str(release_state.get("last_diff_review_at") or ""))
    reviewed_at = _parse_iso(str(review.get("reviewed_at") or ""))

    if release_at is None:
        raise GateBlocked("architect-gate: BLOCKED — release_state missing valid last_release_at")

    anchor = diff_review_at or reviewed_at
    if anchor is None:
        raise GateBlocked(
            "architect-gate: BLOCKED — cannot verify release freshness (no diff review timestamp)"
        )

    if release_at < anchor:
        raise GateBlocked(
            "architect-gate: BLOCKED — stale release_state: last_release_at is before "
            "last_diff_review_at; re-run architect_release_gate after diff approval"
        )

    return f"architect-gate: OK request={request_id} diff=APPROVED release=RELEASE_APPROVED fresh=yes"


def check_repo(architect_dir: Path) -> str:
    active_path = architect_dir / "active_request.json"
    review_path = architect_dir / "last_review.json"
    release_path = architect_dir / "release_state.json"

    if not active_path.is_file() or not review_path.is_file():
        raise GateBlocked(
            "architect-gate: BLOCKED — missing .architect/active_request.json or .architect/last_review.json"
        )

    release_state = load_json(release_path) if release_path.is_file() else None
    return check_architect_gate(
        active=load_json(active_path),
        review=load_json(review_path),
        release_state=release_state,
    )


def main(argv: list[str]) -> int:
    if len(argv) >= 2:
        architect_dir = Path(argv[1])
    else:
        architect_dir = Path(".architect")
    try:
        line = check_repo(architect_dir)
    except GateBlocked as exc:
        print(exc.message, file=sys.stderr)
        print(
            "Run architect_start_request → architect_review_plan → implement → "
            "architect_review_diff → architect_release_gate before commit.",
            file=sys.stderr,
        )
        return 1
    print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
