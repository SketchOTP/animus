# Bootstrap guide: agent continuity layout for `[repo]`

This document describes **exactly** how to create the same repository documentation and agent-rule layout that exists alongside this file. Treat **`[repo]`** as a placeholder: substitute your repository or product display name everywhere `[repo]` appears (for example replace `[repo]` with `my-service`), or perform one global find-and-replace before committing.

**Audience:** Humans and AI coding agents. An agent with only this file should be able to recreate the full structure and file contents.

**Important:** Four files must be **byte-for-byte identical** after substitution (same text, same line endings). Any edit to the rules must be applied to all four:

| Path | Role |
|------|------|
| `[repo-root]/AGENTS.md` | Primary copy; workflow step 1 refers to this file |
| `[repo-root]/.cursorrules` | Cursor legacy root rules file |
| `[repo-root]/CLAUDE.md` | Claude Code / Anthropic-style project rules |
| `[repo-root]/.cursor/rules/operating_rules.md` | Cursor project rules (nested path) |

Those mirrors (and **Appendix A** in this file) include **token discipline**: minimize reads/output, use `repo_map.md` before broad codebase exploration, enrich `project_knowledge.md` with navigation and token-saving tips, and **append-only** updates to `project_history.md` without full-file reads for logging.

---

## 1. Target directory layout

After setup, the repository root (call it **`[repo-root]`** — the folder that contains `.git` or will contain it) should contain:

```text
[repo-root]/
  AGENTS.md
  CLAUDE.md
  .cursorrules
  setup_repo.md                    # optional but recommended: copy this guide for re-bootstrap elsewhere
  project_goal.md
  project_status.md
  project_history.md
  project_knowledge.md
  repo_map.md
  .cursor/
    rules/
      operating_rules.md
```

No other files are required by this layout. Application code, manifests, and CI may be added later.

---

## 2. Preconditions

- You can create directories and files under `[repo-root]`.
- Line endings: use **LF** (`\n`) for all text files unless your platform standard dictates otherwise; keep all four rule mirrors consistent.
- Encoding: **UTF-8** without BOM for all Markdown files.

---

## 3. Step-by-step: directories

1. `cd` to `[repo-root]`.
2. Create the nested rules directory:
   - `mkdir -p .cursor/rules`

---

## 4. Step-by-step: create the five project continuity files

Create each file at `[repo-root]/<filename>` with the content in the subsection below. Replace `[repo]` in titles and body if you are not using a global replace later.

### 4.1 `project_goal.md`

```markdown
# Project goal ([repo])

## What we are building

The **[repo]** repository is the home for this project’s software and documentation. The concrete product surface (libraries, apps, services) will be spelled out here as the codebase grows; until then, success means a maintainable repo with clear intent and agent-friendly continuity.

## Who it serves

Primary users and operators will be defined when the product direction is set. Contributors and AI agents are interim consumers of these project files.

## Success

- Code and docs match an agreed purpose and are easy to change safely.
- `AGENTS.md` and the five project files stay accurate so sessions start with shared context.
- Validation exists for the chosen stack and is run when behavior changes.

## Non-goals

- Using `project_goal.md` as a task backlog.
- Storing secrets or credentials in any tracked doc.
- Large speculative refactors without an explicit request.

When the north star changes (product, audience, or definition of success), update this file before deep implementation continues.
```

### 4.2 `project_status.md`

```markdown
# Project status ([repo])

## Current state

Repository root contains agent continuity documentation (`AGENTS.md`, `project_*.md`, `repo_map.md`, `setup_repo.md`), Cursor/Claude rule mirrors (`.cursorrules`, `CLAUDE.md`, `.cursor/rules/operating_rules.md`). No application source tree or package manifest unless already added separately.

## Active goal

Establish and maintain accurate project documentation for multi-session work.

## Current priorities

1. Define stack and layout when implementation starts; then update `repo_map.md` and `project_knowledge.md` with validation commands.
2. Keep status and history current after each meaningful change.

## Recently completed work

- Bootstrapped structure per `setup_repo.md`: continuity docs and mirrored agent rules.

## In-progress work

- None.

## Known issues

- None tracked.

## Blockers

- None.

## Validation status

- Not applicable until a build/test toolchain exists (or document your stack’s commands in `project_knowledge.md`).

## Last validation run

- N/A

## Next recommended actions

- Add the real project entrypoint (e.g. `package.json`, `Cargo.toml`, `pyproject.toml`) when work begins; document commands in `project_knowledge.md` and update this file.
```

### 4.3 `project_history.md`

Create the file with the header and one initial entry. **Replace** `HHMM DDMMYY` with the output of:

```bash
date '+%H%M %d%m%y'
```

(use 24-hour local time as specified in `AGENTS.md`).

```markdown
# Project history ([repo])

Chronological work log. Newest entries at the bottom.

HHMM DDMMYY - Bootstrapped agent continuity docs and Cursor/Claude rule mirrors from setup_repo.md.
Files touched:
- AGENTS.md
- CLAUDE.md
- .cursorrules
- .cursor/rules/operating_rules.md
- project_goal.md
- project_status.md
- project_history.md
- project_knowledge.md
- repo_map.md
- setup_repo.md
```

If you **omit** `setup_repo.md` from your clone of this layout, remove it from the list above and from `repo_map.md` § 4.5.

**Logging efficiency:** After the file exists, agents should **append** new history entries at the bottom without reading the full file. At session start, skim **recent** entries only unless a full audit is required.

### 4.4 `project_knowledge.md`

```markdown
# Project knowledge ([repo])

Durable lessons for future agents. Not a backlog or duplicate of `project_history.md`.

---

## Conventions

- **Session start:** Read `AGENTS.md` then `project_goal.md`, `project_status.md`, recent tail of `project_history.md` (not necessarily the full file), this file, and `repo_map.md` before code edits.
- **Session end:** Append `project_history.md` at the bottom **without** full-file read for logging; update this file with new lessons or a no-new-knowledge note; refresh `project_status.md` / `repo_map.md` when state or layout changes.
- **Token and navigation:** Add bullets here that help the next agent save time (e.g. smallest useful test command, which paths matter, what to skip, how to use `repo_map.md`).

---

## Stack and validation

- **No toolchain yet** (unless you already added one). When a stack is added, record canonical install, build, test, and lint commands here so agents do not guess.

---

## Bootstrap

- Agent rules are mirrored in four paths; keep them identical when changing policy (see `setup_repo.md`).

---

## No-new-knowledge template

When a session adds nothing durable, append:

```text
DDMMYY — No new durable knowledge (routine doc-only / trivial change).
```
```

### 4.5 `repo_map.md`

```markdown
# Repo map ([repo])

Quick navigation for agents. Update when layout, entrypoints, or roles change.

## Repository root

| Path | Purpose |
|------|---------|
| `AGENTS.md` | Mandatory agent workflow and rules for this repo |
| `CLAUDE.md` | Same rules as `AGENTS.md` (Claude Code) |
| `.cursorrules` | Same rules as `AGENTS.md` (Cursor legacy) |
| `setup_repo.md` | Instructions to reproduce this documentation layout |
| `project_goal.md` | North star: purpose, success, non-goals |
| `project_status.md` | Current snapshot: state, priorities, blockers |
| `project_history.md` | Append-only session log |
| `project_knowledge.md` | Lessons, commands, gotchas |
| `repo_map.md` | This map |

## Cursor rules

| Path | Purpose |
|------|---------|
| `.cursor/rules/operating_rules.md` | Same body as `AGENTS.md` (Cursor nested rules) |

## Application / library code

- **None yet** (unless added separately). Add sections (e.g. `src/`, `apps/`, `packages/`) when code exists.

## Tests

- **None yet.**

## Config and tooling

- **None yet.** (e.g. CI, linters, env templates — document here when added.)

## Generated / runtime (typical)

- Not tracked until the project defines artifacts; then list paths and whether they are gitignored.

## Deprecated / obsolete

- None.
```

---

## 5. Step-by-step: create the four identical rule files

1. Open **Appendix A** below.
2. Copy **everything** inside the appendix fence (from the first `---` of YAML through the final line of the Operating Principle section) into a new file **`[repo-root]/AGENTS.md`**.
3. Copy the **same** bytes to:
   - `[repo-root]/.cursorrules`
   - `[repo-root]/CLAUDE.md`
   - `[repo-root]/.cursor/rules/operating_rules.md`
4. Verify identity (optional):

```bash
cmp AGENTS.md .cursorrules && cmp AGENTS.md CLAUDE.md && cmp AGENTS.md .cursor/rules/operating_rules.md && echo "OK: all four rule files identical"
```

---

## 6. Step-by-step: add this bootstrap guide (optional)

To allow the same propagation again later, copy **`setup_repo.md`** itself into `[repo-root]/setup_repo.md` (the file you are reading, or this project’s version). If you skip this, update `project_status.md`, `project_history.md`, and `repo_map.md` to remove references to `setup_repo.md`.

---

## 7. Verification checklist

Before considering setup complete:

- [ ] `project_goal.md`, `project_status.md`, `project_history.md`, `project_knowledge.md`, `repo_map.md` exist and use consistent `[repo]` (or your substituted name).
- [ ] `project_history.md` has at least one entry with correct `HHMM DDMMYY` and a complete `Files touched:` list.
- [ ] `AGENTS.md`, `.cursorrules`, `CLAUDE.md`, `.cursor/rules/operating_rules.md` exist and are identical.
- [ ] `AGENTS.md` workflow still lists reading the five `project_*` / `repo_map` files before code edits.
- [ ] If applicable, `setup_repo.md` is present and listed in `repo_map.md` / history.

---

## 8. After setup (agent behavior)

Any AI agent working in `[repo-root]` should:

1. Read `AGENTS.md` (and per `AGENTS.md`, read the five project files before editing code).
2. Treat `project_goal.md` as the north star; keep `project_status.md`, `project_history.md`, `project_knowledge.md`, and `repo_map.md` current per the rules in Appendix A.

---

## Appendix A — Full canonical body for `AGENTS.md` and the three mirrors

**Instruction:** Use the fenced block below whose first line is four backticks followed by `markdown`. The **entire** file body for each mirrored file is everything from the YAML opening `---` through the final inner closing fence of the Operating Principle section (the last ``` text block’s closing line), **excluding** the outer four-backtick open/close lines themselves. Do not add or remove lines except when doing a deliberate global policy change across all four.

````markdown
---
description: Mandatory operating rules for AI coding agents in the [repo] repository.
alwaysApply: true
---

## Purpose

This file defines the mandatory operating rules for all AI coding agents working in the **[repo]** repository.

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
- **Enrich `project_knowledge.md` for the next agent:** When you learn shortcuts that save time or tokens (fast validation commands, safe edit paths, folders to skip, search patterns, navigation tips), add concise bullets there. That file is for durable, reusable efficiency lessons—not for duplicating `project_history.md`.
- **`project_history.md` when logging:** To add a session entry, **append** a new block at the bottom. Do **not** read or reload the full `project_history.md` just to append. Full-file reads of history are only for tasks that truly require auditing the entire log.

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
````

---

*End of `setup_repo.md`.*
