# Project Knowledge

Durable project lessons only.

Do not full-read by default.

## Related Docs

Current state:

- `project_status.md`

History:

- `project_history.md`

Repo navigation:

- `repo_map.md`
- `project_memory/index.json`

## Read Policy

Use:

```bash
grep -n '^## ' project_knowledge.md
grep -n -i "keyword" project_knowledge.md
sed -n 'START,ENDp' project_knowledge.md
```

## Durable Rules

- Add only rules that should survive future sessions.

## Conventions

- Add stable coding, naming, architecture, and workflow conventions.

## Known Pitfalls

Add recurring problems, causes, and fixes.

Format:

```md
### YYYY-MM-DD HH:MM — short pitfall name

Problem:
- concise description

Cause:
- concise cause

Fix:
- concise fix
```

## Validation Notes

- Add commands or checks that are repeatedly useful.

## New Notes Inbox

Append new durable facts here first.

Format:

```md
### YYYY-MM-DD HH:MM — short title

Fact:
- concise durable fact

Reason:
- why this matters
```

## Rules

Agents must:

- append new knowledge only
- keep entries concise
- add only durable facts
- update `project_memory/index.json` if navigation/indexing changes
- avoid storing temporary task status here

Do not:

- duplicate history
- duplicate status
- duplicate `project_memory/index.json`
- paste logs
- add speculative notes
