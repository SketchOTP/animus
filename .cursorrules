---
description: Mandatory operating rules for AI coding agents in the animus repository.
alwaysApply: true
---

## Purpose

This file defines the mandatory operating rules for all AI coding agents working in the **animus** repository.

Agents must preserve project continuity by reading the local project goal, project status, project history, project knowledge, and repo map before starting work, then updating those records after work is complete.

| File | Role |
|------|------|
| `project_goal.md` | Project north star |
| `project_status.md` | Current operational snapshot |
| `project_history.md` | Chronological work log |
| `project_knowledge.md` | Durable lessons for future agents |
| `repo_map.md` | Living map of the codebase |

---

# Mandatory Session Start

Before touching any code, the agent must read these local repo files:

```text
project_goal.md
project_status.md
project_history.md
project_knowledge.md
repo_map.md
```

Hard rule:

```text
Do not edit, create, delete, refactor, or run destructive commands until project_goal.md, project_status.md, project_history.md, project_knowledge.md, and repo_map.md have been read.
```

If any required file is missing:

1. Stop.
2. Create the missing file using the required format.
3. If `project_history.md` is missing, create it first.
4. Record the creation of missing files in `project_history.md`.
5. Continue only after all required files exist and have been reviewed.

---

# Efficiency, navigation, and token discipline

Agents must:

- **Minimize tokens:** Use the least reading, search, tool output, and prose necessary to complete the task safely. Prefer narrow searches, partial file reads, and small diffs over whole-repo exploration or dumping large files when the task does not require it.
- **Navigate with `repo_map.md`:** Read `repo_map.md` early and follow it to entrypoints and owning directories. Do not read the entire codebase or enumerate every file by default—open only paths the map (or a targeted search) justifies.
- **Use compact memory index first:** Read `project_memory/index.json` before `repo_map.md` and code scans. Use it as the token-light machine index for entrypoints, areas, and high-value files; use `repo_map.md` as human-readable backup only.
- **Enrich `project_knowledge.md` for the next agent:** When you learn shortcuts that save time or tokens (fast validation commands, safe edit paths, folders to skip, search patterns, navigation tips), add concise bullets there. That file is for durable, reusable efficiency lessons—not for duplicating `project_history.md`.
- **`project_history.md` when logging:** To add a session entry, **append** a new block at the bottom. Do **not** read or reload the full `project_history.md` just to append. Full-file reads of history are only for tasks that truly require auditing the entire log.
- **Keep compact memory current:** After meaningful structural changes, refresh `project_memory/index.json` (or run the workspace refresh path that regenerates it) so future agents can navigate without broad repo scans.

---

# Local Project Files

## `project_goal.md`

This file is the project north star.

It defines what the project is trying to become, who it serves, what success looks like, and what should be avoided.

Every agent must read this file before making changes.

Update `project_goal.md` when:

- The project’s main purpose changes.
- The target user changes.
- The definition of success changes.
- The project scope expands or narrows.
- A new non-goal is discovered.
- A requested task conflicts with the current north star.
- The human explicitly says the direction has changed.

Rules:

- Keep it short.
- Keep it strategic, not implementation-heavy.
- Do not turn it into a backlog.
- Do not bury temporary tasks in this file.
- This file should guide decisions, not document every detail.
- If the north star shifts, update this file before implementation work continues.

---

## `project_status.md`

This file is the current operational snapshot of the project.

It should show:

- Current state
- Active goal
- Current priorities
- Recently completed work
- In-progress work
- Known issues
- Blockers
- Validation status
- Last validation run
- Next recommended actions

Every agent must read this file before making changes.

Update `project_status.md` when:

- Work meaningfully changes the project state.
- A priority changes.
- A task moves from in-progress to complete.
- A blocker appears or is resolved.
- A known issue is discovered or fixed.
- Validation status changes.
- A new next action becomes obvious.

Rules:

- Keep it current.
- Keep it practical.
- Do not duplicate the full work history.
- Do not turn it into a backlog dump.
- It should help the next agent understand what state the project is in right now.

---

## `project_history.md`

This file is the chronological work log for the repository.

Every completed work session must append a new entry using this exact format:

```text
HHMM DDMMYY - One line summary of what was done or changed.
Files touched:
- path/to/file1.ext
- path/to/file2.ext
- path/to/file3.ext
```

Example:

```text
1435 240426 - Added authentication middleware and updated route protection.
Files touched:
- src/middleware/auth.ts
- src/routes/login.ts
- tests/auth.middleware.test.ts
```

Rules:

- Use 24-hour time.
- Use local machine time.
- Keep the summary to one line.
- List every file created, edited, deleted, moved, or renamed.
- Do not omit documentation, config, test, script, generated source, moved, renamed, or deleted files.
- Do not include secrets, tokens, passwords, API keys, or private credentials.
- Newest entries should be appended at the bottom unless the repo already uses newest-first ordering.
- Every completed work session must have an entry before the agent reports completion.
- **Efficiency:** For routine session logging, append the new entry at the bottom **without** reading or reprinting the full file. For context at session start, read only **recent** entries (or the tail of the file), not the entire history, unless the task explicitly requires a full audit.

---

## `project_knowledge.md`

This file stores durable knowledge learned during agent sessions.

It is not a work log, backlog, repo map, or status tracker.  
It is for useful lessons that should make future agents smarter.

Every agent must read this file before making changes.

Every agent must update this file after a completed session with useful durable knowledge learned, or explicitly note that no new durable knowledge was learned.

Update `project_knowledge.md` when the agent learns:

- Important project conventions
- Gotchas or failure patterns
- Setup requirements
- Validation commands that matter
- Files that are easy to misunderstand
- Architecture decisions
- Dependency constraints
- Environment assumptions
- Known fragile areas
- Human preferences specific to this project
- Reusable debugging lessons
- Anything a future agent should know before changing code
- **Token and navigation tips:** e.g. smallest useful test/lint command, which subtrees matter for which features, paths safe to ignore for common tasks, effective `rg`/search scopes, and how to use `repo_map.md` to avoid broad codebase reads

Rules:

- Keep entries short and useful.
- Do not duplicate `project_history.md`.
- Do not use this as a backlog.
- Do not store secrets, tokens, passwords, API keys, or private credentials.
- Capture lessons that help the next agent avoid mistakes.
- If no useful durable knowledge was learned, add a no-new-knowledge entry.

---

## `repo_map.md`

This file is the living map of the codebase.

It should help any agent quickly understand:

- Where the main entry points are.
- Where core logic lives.
- Where UI components live.
- Where APIs/routes live.
- Where data/storage logic lives.
- Where scripts/tooling live.
- Where tests live.
- Where config lives.
- Which generated/runtime files matter.
- Which files are deprecated or obsolete.

Update `repo_map.md` when:

- A new code file is added.
- A code file is changed in a way that affects behavior, structure, ownership, or purpose.
- A file is moved or renamed.
- A module, service, route, component, script, test, or config file changes role.
- A public interface, API contract, schema, command, or entrypoint changes.
- A generated/runtime file becomes important enough to track.
- A file becomes deprecated or obsolete.

Rules:

- Keep descriptions short but useful.
- Update only the sections affected by the work.
- Do not turn this into full documentation.
- If a file is obsolete, mark it deprecated or remove it if deleted.
- The map must help the next agent know where to work.
- **Use this file as the primary navigation aid** before opening large subtrees or guessing paths; prefer map-guided partial reads over scanning the whole repository.

---

# Mandatory Workflow

Every agent session must follow this order:

```text
1. Read AGENTS.md.
2. Read project_goal.md.
3. Read project_status.md.
4. Skim recent project_history.md (latest entries or tail; avoid reading the entire file unless a full audit is required).
5. Read project_knowledge.md (focus sections relevant to the task if the file is long).
6. Read repo_map.md; use it to plan which code paths to open.
7. Confirm the task aligns with project_goal.md.
8. Understand the current project state from project_status.md.
9. Cross-check recent history insights against project_status.md (still avoid full history read unless needed).
10. Understand the current task; apply relevant lessons from project_knowledge.md (step 5) without rereading the whole file unless necessary.
11. Inspect only the files needed for the task (per repo_map.md and targeted search—never the whole codebase by default).
12. Make the smallest safe change.
13. Run relevant validation.
14. Update project_goal.md if the north star shifted.
15. Update project_status.md if project state changed.
16. Update project_history.md by appending one new entry at the bottom (append-only; do not full-read the file for this step).
17. Update project_knowledge.md with useful durable lessons from the session (include token/nav tips when applicable), or note that no new durable knowledge was learned.
18. Update repo_map.md if code structure changed.
19. Report what changed, what was tested, and any blockers.
```

---

# Work Rules

Agents must:

- Prefer small, controlled changes.
- Avoid broad refactors unless explicitly requested.
- **Use minimal tokens:** default to the narrowest reads, searches, and edits that still satisfy the task and safety; avoid dumping or reading entire large files or trees without cause.
- Read only the files needed for the task after the mandatory startup files; **use `repo_map.md` first** to choose those paths instead of exploratory full-repo passes.
- Preserve existing behavior unless the task requires changing it.
- Keep changes easy to review.
- Update documentation when behavior, structure, commands, config, or usage changes.
- Run the narrowest relevant validation possible.
- Clearly report validation results.
- Clearly report any blockers, risks, or assumptions.
- Stop and report the conflict if a requested task conflicts with `project_goal.md`.
- Update `project_goal.md` first if the human changes the project direction.
- Update `project_status.md` when the current project state changes.
- Update `project_history.md` for every completed work session.
- Update `project_knowledge.md` after every completed session with useful durable lessons, or explicitly stating no durable knowledge was learned.
- Update `repo_map.md` when code structure, behavior, ownership, purpose, entrypoints, APIs, schemas, config, scripts, or tests change.

---

# Validation Rules

Before reporting completion, the agent must verify:

```text
[ ] project_goal.md was reviewed
[ ] project_status.md was reviewed
[ ] project_history.md was reviewed
[ ] project_knowledge.md was reviewed
[ ] repo_map.md was reviewed
[ ] project_goal.md updated if the north star shifted
[ ] project_status.md updated if project state changed
[ ] project_history.md updated
[ ] project_knowledge.md updated with useful durable lessons, or marked as no new durable knowledge
[ ] repo_map.md updated if code files were added, moved, renamed, or behaviorally changed
[ ] Tests or validation were run, or reason for not running was documented
[ ] All changed files are listed in the final report
[ ] No unrelated files were modified
```

Validation may include, depending on the project (update `project_knowledge.md` when a canonical stack exists):

```text
npm test
npm run lint
npm run build
pytest
ruff check .
mypy .
go test ./...
cargo test
dotnet test
powershell -ExecutionPolicy Bypass -File ./scripts/validate.ps1
```

Use project-specific commands when they exist.

---

# Required Final Agent Report

At the end of the session, report:

```text
Summary:
- One-line summary of completed work.

Files changed:
- path/to/file1.ext
- path/to/file2.ext

Validation:
- Command run:
- Result:

Docs updated:
- project_goal.md:
- project_status.md:
- project_history.md:
- project_knowledge.md:
- repo_map.md:

Blockers / risks:
- None
```

If validation was not run, state why.

---

# Hard Constraints

Agents must not:

- Skip reading `project_goal.md`.
- Skip reading `project_status.md`.
- Skip the required review of `project_history.md` (but **do not** interpret this as requiring a full-file read—recent entries or tail are enough unless a full audit is needed).
- Skip reading `project_knowledge.md`.
- Skip reading `repo_map.md`.
- **Read or reload the entire `project_history.md` solely to append** a new session entry—append at the bottom without a full read.
- **Default to whole-repository reads or broad directory listing** when `repo_map.md` and targeted search can narrow the scope.
- Make code changes before reading required context.
- Make changes that conflict with `project_goal.md` without reporting the conflict.
- Allow the project north star to shift without updating `project_goal.md`.
- Allow project state to change without updating `project_status.md`.
- Finish a session without updating `project_history.md`.
- Finish a session without updating `project_knowledge.md` or explicitly stating no durable knowledge was learned.
- Store temporary task notes in `project_knowledge.md`.
- Duplicate `project_history.md` entries inside `project_knowledge.md`.
- Leave changed files undocumented.
- Update code without updating `project_history.md`.
- Add, move, rename, or behaviorally change code files without checking whether `repo_map.md` needs updates.
- Store secrets, tokens, passwords, API keys, or private credentials in repo docs.
- Commit local runtime state, generated caches, logs, databases, or machine-specific files unless explicitly required.
- Perform broad refactors unless explicitly requested.
- Delete or rename files without documenting the reason.
- Run destructive commands without explicit approval.
- Modify unrelated files while completing a task.

---

# Operating Principle

Prefer small, controlled, well-documented changes.

The project goal is the north star.  
The project status is the live snapshot.  
The project history is the audit trail.  
The project knowledge file is the durable lesson memory.  
The repo map is the navigation layer.

The next agent should be able to understand:

```text
What changed.
Why it changed.
Which files were touched.
How to validate it.
Where the related code lives.
What state the project is currently in.
What durable lessons are known.
What still needs attention.
```

<!-- hermes-project-memory-v1 -->
Compact project memory workflow:
- Read `project_memory/index.json` first for token-light navigation.
- Use `repo_map.md` as human-readable backup, not the primary full context payload.
- Do not load full `project_history.md` by default; only recent tail entries when needed.
- Keep `project_memory/index.json` current after structural changes.

