# Phase 9e — Scout Research UI

**Status:** CLOSED (D-080)  
**Repo:** `/home/sketch/animus`  
**Slice:** 9e-ui (Research subsection on Goals detail)

## Scope

Read-only Research card on Goals detail tab in `animus-chat/app/governance-hub.js`:

- Scout metadata label (`include_research` default false)
- Findings table when `GET /api/governance/goals/{id}/research/findings` returns data
- License badge with `reference_only` highlight
- Relevance display
- Evidence link via BFF `repos/{repo_id}/runs/{goal_id}/artifacts/{evidence_ref}`

Driver tab unchanged. No gate actions.

## Verification

```bash
python3 -m unittest animus-chat.tests.test_governance_hub_scout -q
```

## Platform dependency

Findings list requires animus-platform `GET goals/{goal_id}/research/findings` (9d follow-up if absent). UI degrades to metadata-only when endpoint 404s.
