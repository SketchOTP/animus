# Project Goals — animus (Governance hub UI)

## Product Goal

**animus** chat shell exposes read-only Governance hub views backed by animus-platform projection APIs.

Phase 7 adds a Goals tab: goal list, milestone/phase summary, queue table with materialization statuses.

Phase 8 adds a Driver tab: driver status, controls (start/pause/resume/halt/stop), stop reason, budget hint, pending_completion sign-off.

## Success Criteria

- Goals tab loads `/api/governance/goals` for linked platform project
- Goal detail shows hierarchy counts and queue rows (including dispatched/completed)
- Driver tab loads `/api/governance/driver/status` and posts control events
- `animus-chat/tests/test_governance_hub_phase7.py` passes
- `animus-chat/tests/test_governance_hub_phase8.py` passes
- `scripts/run_phase7_ui_acceptance.sh` writes `.evidence/phase7_ui_acceptance.json`
- `scripts/run_phase8_ui_acceptance.sh` writes `.evidence/phase8_ui_acceptance.json`

## Non Goals

- Goal mutation or breakdown approval in UI (operator tools elsewhere)
- Autonomous dispatch in UI (driver daemon + env flag)

## Architecture Principles

- BFF proxy only — no duplicated projection logic
- Parse helpers tested via unittest contract

## Module Ownership Rules

| module | owns |
|--------|------|
| `animus-chat/app/governance-hub.js` | Governance overlay tabs (incl. Driver) |
| `animus/plugins/governance_hub/` | API proxy |

## Required Testing

- `animus-chat/tests/test_governance_hub_phase7.py`
- `animus-chat/tests/test_governance_hub_phase8.py`

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
