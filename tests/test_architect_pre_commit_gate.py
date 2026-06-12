"""Pre-commit Architect gate — diff + release freshness."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.architect_pre_commit_check import GateBlocked, check_architect_gate, check_repo


def _write(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_gate_ok_when_release_fresh(tmp_path: Path) -> None:
    architect = tmp_path / ".architect"
    architect.mkdir()
    _write(
        architect / "active_request.json",
        {"request_id": "abc123", "status": "NEEDS_PLAN"},
    )
    _write(
        architect / "last_review.json",
        {
            "request_id": "abc123",
            "review_type": "diff",
            "status": "APPROVED",
            "reviewed_at": "2026-06-12T12:00:00+00:00",
        },
    )
    _write(
        architect / "release_state.json",
        {
            "last_release_status": "RELEASE_APPROVED",
            "last_release_at": "2026-06-12T12:01:00+00:00",
            "last_diff_review_status": "APPROVED",
            "last_diff_review_at": "2026-06-12T12:00:00+00:00",
        },
    )
    line = check_repo(architect)
    assert "release=RELEASE_APPROVED" in line


def test_gate_blocks_stale_release_state(tmp_path: Path) -> None:
    architect = tmp_path / ".architect"
    architect.mkdir()
    _write(architect / "active_request.json", {"request_id": "abc123"})
    _write(
        architect / "last_review.json",
        {
            "request_id": "abc123",
            "review_type": "diff",
            "status": "APPROVED",
            "reviewed_at": "2026-06-12T13:00:00+00:00",
        },
    )
    _write(
        architect / "release_state.json",
        {
            "last_release_status": "RELEASE_APPROVED",
            "last_release_at": "2026-06-12T12:00:00+00:00",
            "last_diff_review_status": "APPROVED",
            "last_diff_review_at": "2026-06-12T13:00:00+00:00",
        },
    )
    with pytest.raises(GateBlocked, match="stale release_state"):
        check_repo(architect)


def test_gate_blocks_missing_release_state() -> None:
    with pytest.raises(GateBlocked, match="missing .architect/release_state.json"):
        check_architect_gate(
            active={"request_id": "x"},
            review={
                "request_id": "x",
                "review_type": "diff",
                "status": "APPROVED",
                "reviewed_at": "2026-06-12T12:00:00+00:00",
            },
            release_state=None,
        )
