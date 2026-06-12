# D-082 — Architect enforcement graduation (animus)

**Date:** 2026-06-12  
**Status:** APPROVED (human operator, D-078 delegated authority)  
**Scope:** `/home/sketch/animus` monorepo (animus-chat BFF, hermes-agent bundle)

## Decision

Set `enforcement_active: true` in `.architect/supervision_config.json` for this repository.

## What is enforced

| Layer | Mechanism | Blocks commits? |
|-------|-----------|-----------------|
| v1 supervision | `architect_review_plan` / `architect_review_diff` / `architect_release_gate` | Yes — agents must stop on non-approval |
| Mechanical guard | `scripts/git-hooks/pre-commit-architect-gate` (+ release freshness) | Yes — refuses commit without diff APPROVED + fresh RELEASE_APPROVED |
| Implementation guard | `scripts/assert_slice_approved.sh` | Advisory at shell — agents must run before edits |
| RSAL | dry-run gates, comprehension, drift | **No** — `rsal_enforcement_active: false` |

## Observation window

Record gate friction for the next 2–3 real Architect requests under this config.

## Rollback

Set `enforcement_active: false` with a new decision record; do not disable the pre-commit hook without operator approval.
