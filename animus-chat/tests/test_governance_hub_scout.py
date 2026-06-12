"""Phase 9e Scout UI helper contract tests (mirrors governance-hub.js helpers)."""

from __future__ import annotations

import unittest


def format_research_label(research: dict | None) -> str:
    meta = research if isinstance(research, dict) else {}
    enabled = bool(meta.get("include_research"))
    count = int(meta.get("finding_count") or 0)
    last = str(meta.get("last_scout_at") or "—")
    flag = "enabled" if enabled else "disabled (default false)"
    return f"Scout: {flag} · findings {count} · last {last}"


def format_license_badge(license_name: str | None, license_flags: list | None) -> dict:
    label = str(license_name or "UNKNOWN")
    flags = license_flags if isinstance(license_flags, list) else []
    reference_only = "reference_only" in flags
    return {
        "label": label,
        "referenceOnly": reference_only,
        "className": "scout-license scout-license-ref" if reference_only else "scout-license",
    }


def format_relevance_bar(relevance: float | str | None) -> dict:
    try:
        value = float(relevance)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        value = float("nan")
    if value != value:
        return {"pct": 0, "label": "—"}
    pct = max(0, min(100, round(value * 100)))
    return {"pct": pct, "label": f"{value:.2f}"}


def build_evidence_artifact_path(repo_id: str, goal_id: str, evidence_ref: str) -> str:
    if not repo_id or not goal_id or not evidence_ref:
        return ""
    return (
        f"repos/{repo_id}/runs/{goal_id}/artifacts/{evidence_ref}"
    )


def build_finding_row_html(finding: dict, repo_id: str, goal_id: str) -> str:
    badge = format_license_badge(finding.get("license"), finding.get("license_flags"))
    rel = format_relevance_bar(finding.get("relevance"))
    evidence_path = build_evidence_artifact_path(
        repo_id,
        str(finding.get("goal_id") or goal_id),
        str(finding.get("evidence_ref") or ""),
    )
    evidence_cell = (
        f'<a href="/api/governance/{evidence_path}" target="_blank" rel="noopener">evidence</a>'
        if evidence_path
        else "—"
    )
    ref_suffix = " · ref-only" if badge["referenceOnly"] else ""
    return (
        f"<tr><td>{finding.get('source', '')}</td>"
        f"<td><span class=\"{badge['className']}\">{badge['label']}{ref_suffix}</span></td>"
        f"<td><span class=\"scout-relevance\">{rel['label']}</span></td>"
        f"<td>{evidence_cell}</td></tr>"
    )


class GovernanceHubScoutTests(unittest.TestCase):
    def test_format_research_label_default_false(self) -> None:
        label = format_research_label({"include_research": False, "finding_count": 0})
        self.assertIn("disabled (default false)", label)
        self.assertIn("findings 0", label)

    def test_format_license_badge_reference_only(self) -> None:
        badge = format_license_badge("UNKNOWN", ["reference_only"])
        self.assertTrue(badge["referenceOnly"])
        self.assertIn("scout-license-ref", badge["className"])

    def test_format_relevance_bar(self) -> None:
        rel = format_relevance_bar(0.716)
        self.assertEqual(rel["pct"], 72)
        self.assertEqual(rel["label"], "0.72")

    def test_build_evidence_artifact_path(self) -> None:
        path = build_evidence_artifact_path("repo-1", "goal-1", "abc123")
        self.assertEqual(path, "repos/repo-1/runs/goal-1/artifacts/abc123")

    def test_build_finding_row_html(self) -> None:
        row = build_finding_row_html(
            {
                "source": "github:org/repo",
                "license": "GPL-3.0",
                "license_flags": ["reference_only"],
                "relevance": 0.65,
                "evidence_ref": "deadbeefdeadbeefdeadbeefdeadbeef",
            },
            "repo-1",
            "goal-1",
        )
        self.assertIn("github:org/repo", row)
        self.assertIn("ref-only", row)
        self.assertIn("/api/governance/repos/repo-1/runs/goal-1/artifacts/", row)


if __name__ == "__main__":
    unittest.main()
