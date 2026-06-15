# D-142P1 — Command Center UX Stabilization

Post-D-142C Mission Control UX commit for the dedicated `animus-command-center` dashboard.

## Status

`COMMAND_CENTER_UX_STABILIZED`

## Scope (animus repo only)

Mission Control layout with Overview / Projects / Goals / History tabs, Animus purple theme, taste-skill visual polish, LAN host binding, styled dropdowns/buttons/cards, governance action delegation fix, silent auto-refresh, and driver status panel on Overview.

**Not in this slice:** animus-platform kernel/API changes (project registry CRUD API, goal freshness/archive/cancel API) — deferred to D-142P2/P3 on `animus-platform`.

## Launch

```bash
./scripts/run-command-center.sh
# Local:  http://127.0.0.1:3010/
# LAN:    http://<host-ip>:3010/  (COMMAND_CENTER_HOST=0.0.0.0 default)
```

## UI contract summary

| Tab | Purpose |
|-----|---------|
| **Overview** | Platform pulse, action inbox, goal pipeline, driver status |
| **Projects** | Registry grid with project metadata |
| **Goals** | Per-project goal list, filters, inline approve/sign-off |
| **History** | Run audit per project |

Navigation: icon sidebar (`ccNav`), no separate Driver/Release tabs. Ghost icon branding. Custom project dropdowns on Goals/History tabs.

## Verification

```bash
pytest -q tests/test_command_center_d140.py tests/test_command_center_d141.py
curl -fsS http://127.0.0.1:3010/healthz
```

## Baseline

Builds on D-142C commit `7a1203c03` (live refresh hotfix: `workspace_id` + per-project `project_id`).
