# D-142P1 UI Contract Summary

## Shell IDs (index.html)

- `ccShell`, `ccSidebar`, `ccNav`, `ccBrandMark`
- Panels: `ccPanelOverview`, `ccPanelProjects`, `ccPanelGoals`, `ccPanelHistory`
- Goals: `ccGoalList`, `ccGoalFilterTabs`, `ccGoalsProjectSelect`, `ccGoalNewGoalCollapsible`
- History: `ccHistoryList`, `ccHistoryProjectSelect`
- Overview: `ccOverviewBody`, `ccStatGrid`

## Navigation sections (app.js)

`overview`, `projects`, `goals`, `history` — Driver and Release tabs removed.

## Theme (styles.css)

- Accent: `--cc-accent: #7c3aed`
- Fonts: Instrument Sans, Outfit, JetBrains Mono
- Components: `.cc-stat-grid`, `.cc-nav-btn`, `.cc-goal-card`, `.cc-history-item`, `.cc-approval-panel`

## Governance fetch contract

- `govFetch('projects')`
- `driver/status?workspace_id=`
- `goals?project_id=` and `runs?limit=24&project_id=` per project
- Goal run POST: `projects/{id}/goal-runs`

## Refresh behavior

- Auto-refresh (30s): silent, no full-shell dimming
- Manual refresh: brief `cc-loading-manual` on sidebar button
- `refreshInFlight` guard prevents overlapping cycles

## LAN support

- `COMMAND_CENTER_HOST` default `0.0.0.0` in `server.py` and `run-command-center.sh`
- Launcher prints local + LAN URLs

## Assets

- `ghostonlyicon.png` linked in index + favicon
- Desktop launcher scripts: `command-center-launch.sh`, `install-command-center-desktop.sh`
