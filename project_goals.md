# Project Goals — animus (Governance hub UI)

## Product Goal

**animus** chat shell exposes read-only Governance hub views backed by animus-platform projection APIs.

Phase 7 adds a Goals tab: goal list, milestone/phase summary, queue table with materialization statuses.

## Success Criteria

- Goals tab loads `/api/governance/goals` for linked platform project
- Goal detail shows hierarchy counts and queue rows
- `animus-chat/tests/test_governance_hub_phase7.py` passes
- `scripts/run_phase7_ui_acceptance.sh` writes `.evidence/phase7_ui_acceptance.json`

## Non Goals

- Goal mutation or breakdown approval in UI (operator tools elsewhere)
- Phase 8 queue dispatch controls

## Architecture Principles

- BFF proxy only — no duplicated projection logic
- Parse helpers tested via unittest contract

## Module Ownership Rules

| module | owns |
|--------|------|
| `animus-chat/app/governance-hub.js` | Governance overlay tabs |
| `animus/plugins/governance_hub/` | API proxy |

## Required Testing

- `animus-chat/tests/test_governance_hub_phase7.py`

## Release Gates

- Plan approved
- Diff reviewed
- Tests pass

## Drift Definition

Changes outside approved Architect plan scope.

## Long Term Vision

Single operator surface for registry, runs, and goal pipeline visibility.

## Repository Maturity Level

Level 2 — Development
