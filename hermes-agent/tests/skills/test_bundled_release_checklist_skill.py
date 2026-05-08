"""Bundled skill sanity: release-checklist-automation frontmatter loads like production."""

from __future__ import annotations

from pathlib import Path

from agent.skill_utils import parse_frontmatter, skill_matches_platform

_SKILL_ROOT = (
    Path(__file__).resolve().parents[2]
    / "skills"
    / "devops"
    / "release-checklist-automation"
)
SKILL_PATH = _SKILL_ROOT / "SKILL.md"
TEMPLATE_PATH = _SKILL_ROOT / "templates" / "minimal-release-checklist.md"


def test_release_checklist_skill_exists_and_parses():
    assert SKILL_PATH.is_file(), f"missing bundled skill: {SKILL_PATH}"
    raw = SKILL_PATH.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(raw)

    assert fm.get("name") == "release-checklist-automation"
    assert isinstance(fm.get("description"), str) and fm["description"].strip()
    assert fm.get("version")
    meta = fm.get("metadata") or {}
    hermes = meta.get("hermes") or {}
    assert isinstance(hermes.get("tags"), list) and hermes["tags"]
    assert hermes.get("category") == "devops"

    assert skill_matches_platform(fm)
    assert body.lstrip().startswith("#"), "expected markdown body after frontmatter"


def test_release_checklist_skill_mentions_hermes_release_script():
    body = SKILL_PATH.read_text(encoding="utf-8")
    assert "scripts/release.py" in body
    assert "scripts/run_tests.sh" in body


def test_release_checklist_template_exists():
    assert TEMPLATE_PATH.is_file(), f"missing template: {TEMPLATE_PATH}"
    text = TEMPLATE_PATH.read_text(encoding="utf-8")
    assert "{{REPO_NAME}}" in text and "{{VERSION}}" in text
