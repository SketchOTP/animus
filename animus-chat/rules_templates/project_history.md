# Project History

Append-only project timeline.

Do not full-read by default.

## Related Docs

Current state:

- `project_status.md`

Durable knowledge:

- `project_knowledge.md`

Repo navigation:

- `repo_map.md`
- `project_memory/index.json`

## Read Policy

Use:

```bash
tail -n 80 project_history.md
grep -n -i "keyword" project_history.md
```

Read older entries only by targeted keyword lookup.

## Entry Format

```md
## YYYY-MM-DD HH:MM — short title

Changed:
- `path`

Summary:
- concise factual result

Validation:
- command — result

Docs:
- updated/appended docs
```

## Rules

Agents must:

- append only
- keep entries short
- record meaningful completed work
- record blockers and failed validation
- record creation of required project docs
- mention `project_memory/index.json` when updated
- never rewrite old entries unless explicitly asked

Do not:

- paste full conversations
- paste large logs
- duplicate `project_status.md`
- duplicate `project_memory/index.json`
- use history as current state

## Entries

<!-- Append new entries below. -->
