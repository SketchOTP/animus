---
name: hermes-project-workspace
description: Create or refresh project_history.md and repo_map.md in a Hermes project directory (CLI + behavior)
version: 1.0.0
metadata:
  hermes:
    tags: [hermes, project, workspace, repo-map, history]
    related_skills: []
---

# Hermes project workspace (`project_history.md` / `repo_map.md`)

## When to use

The user wants workspace files under a **real project root** (e.g. `~/Projects/kuki`), not a generic folder. Tasks: initialize missing files, append a history line, or regenerate the repository map from disk.

## Rules

- Paths are always the **absolute resolved project directory** (the repo root).
- `project_history.md` — one timestamped line per event; created with a standard header if missing.
- `repo_map.md` — tree scan (depth/size capped); regenerated with **repo-map-refresh** when the user wants an up-to-date index.

## CLI (hermes-agent on `PATH`)

From the project root, or pass `--path`:

```bash
# Create missing project_history.md and repo_map.md (full scan for new repo_map)
hermes project init --path /absolute/path/to/project

# Same but skip generating repo_map (only touch history header if missing)
hermes project init --path /absolute/path/to/project --skip-repo-map

# Regenerate repo_map.md from disk (overwrites)
hermes project repo-map-refresh --path /absolute/path/to/project

# Append one history line
hermes project history-append --path /absolute/path/to/project --summary "Shipped v2" --source cli

# Print current contents
hermes project show --path /absolute/path/to/project --file project_history
hermes project show --path /absolute/path/to/project --file repo_map
```

## Integrations

- **Hermes Chat**: project paths come from `projects.json` (`CHAT_DATA_DIR`). Opening **History** / **Repo map** triggers ensure+read on the server; **↻ Map** calls repo-map-refresh.
- **Gateway**: requests with `hermes_project_path` (or `HERMES_PROJECT_PATH`) run `ensure_workspace_files` before the agent so tool history and files stay under that directory.
- **Cron** (Hermes Chat project delivery): same ensure before the job runs.

## Python (same repo)

```python
from pathlib import Path
from agent.project_workspace import ensure_workspace_files, refresh_repo_map, append_project_history_line

root = Path("/absolute/path/to/project").resolve()
ensure_workspace_files(root)
refresh_repo_map(root)
append_project_history_line(root, "Manual note", source="agent")
```
