# D-141 — Dedicated Command Center API Integration

Wire the dedicated `animus-command-center` shell to live governance data and controlled Goal Runner actions.

## API mapping

| UI surface | HTTP |
|---|---|
| Project registry list | `GET /api/governance/projects` |
| Project registry detail | `GET /api/governance/projects/{project_id}` |
| Goal Runner submit | `POST /api/governance/projects/{project_id}/goal-runs` |
| Goal run detail | `GET /api/governance/goal-runs/{goal_run_id}` |
| Goal detail | `GET /api/governance/goals/{goal_id}` |
| Driver snapshot | `GET /api/governance/driver/status` |

## Defaults

- `run_mode`: `draft_only`
- `approval_mode`: `manual_approval`
- `research_mode`: profile default or `light`
- Budget fields: profile `budget_defaults`

## Controls

- Run draft_only (POST)
- Refresh (re-fetch goal run panels)
- Open evidence links (outcome panel)
- Driver controls remain disabled

## Verification

```bash
pytest -q tests/test_command_center_d140.py tests/test_command_center_d141.py
```

See `evidence-bundle.json` for DOM/test proof.
