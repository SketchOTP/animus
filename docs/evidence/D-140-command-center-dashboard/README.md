# D-140 — Dedicated Animus Command Center Dashboard v1

Separate visual dashboard app (`animus-command-center/`) — not an expansion of `animus-chat`.

## Status

`DEDICATED_COMMAND_CENTER_SHELL_READY`

## Launch (dev only)

```bash
# governance-api on :8120 recommended
./scripts/run-command-center.sh
# → http://127.0.0.1:3010/
```

Environment:

| Variable | Default |
|----------|---------|
| `COMMAND_CENTER_HOST` | `127.0.0.1` |
| `COMMAND_CENTER_PORT` | `3010` |
| `GOVERNANCE_API_URL` | `http://127.0.0.1:8120` |

## Shell scope (v1)

- Icon sidebar navigation: Overview, Projects, Goals, Runs, Driver, Release
- Visual stat tiles, sparkline activity chart, health donut, driver ring
- Read-only governance data via BFF proxy (`/api/governance/*`)
- Driver control buttons rendered but disabled (read-only shell)
- No self-hosting / systemd in this slice

## Verification

```bash
pytest -q tests/test_command_center_d140.py
curl -fsS http://127.0.0.1:3010/healthz
```

## Non-goals (this slice)

- animus-chat / governance-hub.js changes
- Live goal-runner POST flows
- External harness rerun
- Operator sign-off (`pending_completion` remains human-only)
