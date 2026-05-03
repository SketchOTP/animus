# Repo Map

Token-light human navigation map.

Do not full-read by default.

Last updated: YYYY-MM-DD HH:MM

## Related Docs

Current state:

- `project_status.md`

History:

- `project_history.md`

Durable knowledge:

- `project_knowledge.md`

Machine-readable compact index:

- `project_memory/index.json`

## Read Policy

Use:

```bash
grep -n '^## ' repo_map.md
grep -n -i "keyword" repo_map.md
sed -n 'START,ENDp' repo_map.md
```

## Navigation Index

Populate as the repository grows (examples only):

- `src/` — main source code (if used)
- `tests/` — test suite (if used)
- `docs/` — documentation (if used)
- `scripts/` — utility scripts (if used)
- `.cursor/rules/` — Cursor rules
- `AGENTS.md` — canonical agent contract
- `CLAUDE.md` — Claude adapter
- `project_status.md` — current project state
- `project_history.md` — append-only timeline
- `project_knowledge.md` — durable project lessons
- `repo_map.md` — human repo navigation
- `project_memory/index.json` — compact navigation index

## Entry Points

- unknown

## Core / modules (conceptual)

- unknown — document mapping when layout exists; do not force renames (see `AGENTS.md` Existing Repo Handling).

## Conventional layout mapping

When the repository already has a layout, **do not** force renames to match a greenfield split. Record how existing paths map to conceptual areas:

| Conceptual area | Existing path(s) |
|---|---|
| core | *populate when known* |
| modules / plugins | *populate when known* |
| adapters | *populate when known* |
| schemas | *populate when known* |
| tests | *populate when known* |

## Tests

- unknown

## Config

- unknown

## Generated or Ignored

- unknown

## Repo Map Deltas

Append structural changes here unless full regeneration is explicitly requested.

Also update `project_memory/index.json` after structural changes.

Format:

```md
### YYYY-MM-DD HH:MM — short title

Added:
- `path` — purpose

Changed:
- `path` — new purpose

Removed:
- `path` — reason
```

## Rules

Agents must:

- use heading lookup before reading sections
- append deltas after structural changes
- update `project_memory/index.json` after structural/doc navigation changes
- avoid full regeneration unless requested
- keep descriptions short

Do not:

- document every file if not useful
- paste directory dumps
- duplicate code comments
- duplicate `project_memory/index.json`
- use this as project history
