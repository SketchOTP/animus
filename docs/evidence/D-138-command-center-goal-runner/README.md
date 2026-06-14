# D-138 — Command Center Goal Runner UI v1

Operator-facing Goal Runner panel in Command Center (Governance hub).

## Surface

- Tab: **Goal Runner**
- Controls: project selector, goal statement, research/run/approval modes, budget fields, Run, Refresh
- Panels: timeline, research, breakdown, execution, blocker/recovery, memory, outcome

## API (via BFF)

- `GET /api/governance/projects`
- `GET /api/governance/projects/{project_id}`
- `POST /api/governance/projects/{project_id}/goal-runs`
- `GET /api/governance/goal-runs/{goal_run_id}`
- `GET /api/governance/goals/{goal_id}`
- `GET /api/governance/driver/status`

## Verification

```bash
python3 -m unittest animus-chat.tests.test_governance_hub_d138 -q
```

See `evidence-bundle.json`.
