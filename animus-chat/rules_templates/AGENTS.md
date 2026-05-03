# AGENTS.md

Canonical project contract for all AI coding agents.

## Source of Truth

Roles are **split** (see **Priority Order** below). Root-level project docs plus `project_memory/index.json` remain the default **governance and continuity** surface.

- **`.project_intel/`** — machine or tool **state** (caches, runs, derived artifacts). Use when the workflow writes there; do **not** treat it as replacing `AGENTS.md` or `.cursor/rules` for policy.

## Priority Order (conflict resolution)

When sources disagree, **higher** wins:

1. **`.cursor/rules/*.mdc`** — Cursor hard enforcement.
2. **`AGENTS.md`** — this governance contract.
3. **`CLAUDE.md`** — Claude adapter defaults.
4. **`project_index.md`** if the repo adds it; **else** **`project_memory/index.json`** — compact navigation.
5. **`project_status.md`**, **`project_knowledge.md`**, **`project_history.md`** — continuity (bounded reads by default).
6. **`.project_intel/`** — state only; does **not** override 1–3.

Canonical Cursor-side spelling of this stack: `.cursor/rules/00-project-contract.mdc`.

## Dual chronology (anti-drift)

- **`project_history.md`** — human / **audit** history (decisions, policy changes, impact). Small policy edits still belong here; they change agent behavior.
- **`.project_intel/`** — **machine state ledger** (tool output, structured runs, derived indices).

**Correlation rule:** If both are updated for the **same** change, use the **same ISO date** (`YYYY-MM-DD`) and the **same one-line summary** (the correlation key) in each place, and cross-reference so audit lines and ledger entries can be paired. If only one side is updated, no pairing is required.

## Future governance checks (CI, not implemented)

Planned automated checks (to be added later) should verify, among other things: classification block present in outputs; no core files modified during feature-scoped tasks; module layout conventions followed. **Rollout:** when CI lands, keep checks **warn-only** first, then enforce in stages (classification → core boundary → module structure) to limit false positives and disruption.

Required project docs:

- `project_status.md`
- `project_history.md`
- `project_knowledge.md`
- `repo_map.md`
- `project_memory/index.json`

## Missing Project Docs Rule

If required project docs are missing, create them before continuing.

Rules:

- create only missing files
- create `project_memory/` if missing
- initialize empty files with the standard minimal template
- do not overwrite existing docs unless explicitly told
- append the doc-creation event to `project_history.md`
- update `project_status.md`
- update `project_memory/index.json` when navigation or doc set changes

## Read Order

In **Cursor**, applicable `.cursor/rules/*.mdc` load with the session; start from **Priority Order** in `.cursor/rules/00-project-contract.mdc`, then:

1. `AGENTS.md`
2. `project_status.md`
3. `project_memory/index.json`
4. targeted `repo_map.md` section
5. targeted `project_knowledge.md` section
6. recent tail of `project_history.md`

## Token Rules

Read the smallest useful slice.

Allowed full reads:

- `AGENTS.md`
- `project_status.md`
- `project_memory/index.json`
- `project_goal.md` only if scope is unclear

Do not full-read by default:

- `project_history.md`
- `repo_map.md`
- `project_knowledge.md`

Use bounded reads:

```bash
tail -n 80 project_history.md
grep -n '^## ' repo_map.md
grep -n '^## ' project_knowledge.md
grep -n -i "keyword" repo_map.md
grep -n -i "keyword" project_history.md
sed -n 'START,ENDp' file.md
```

Full-read exception for large docs requires:

1. bounded lookup failed
2. task cannot proceed without broader context
3. agent states why

## Work Rules

- Make scoped changes only.
- Prefer existing patterns.
- Follow **Dependency Rule** before adding any new dependency.
- Do not rename or move files without updating docs (see **Existing Repo Handling** when the repo already has structure).
- Do not duplicate facts across docs.
- If docs and code disagree, report the conflict.
- If nothing materially changed, do not update docs.

## Existing Repo Handling

If this repository already has an architecture, **do not** force renames or moves to match a greenfield layout. Map existing folders to the conceptual areas below and **document the mapping in `repo_map.md`** (append or extend the conventional layout section there).

Conceptual areas to map:

- `core`
- `modules` / `plugins`
- `adapters`
- `schemas`
- `tests`

Update the mapping when layout or responsibilities change.

## Dependency Rule

New dependencies require justification **before** they are added:

- **Why** it is needed (problem it solves).
- **Where** it will be used (modules, entry points, build).
- **Lighter alternatives** considered (stdlib, existing deps, small local code).

No dependency may be added **only** for convenience.

## Testing Rule

Every **module** (cohesive unit behind a clear boundary) must have tests covering:

- **Enabled path** — default or turned-on behavior works.
- **Disabled path** — feature flag / optional integration off, or module inactive, behaves as specified.
- **Failure isolation** — errors in dependencies or collaborators do not leak in undocumented ways; boundaries hold.
- **Replacement compatibility** — when the module is swappable (adapter, backend, transport), tests cover the contract so replacements do not break silently.

Skip items only when genuinely not applicable; say so in the PR or task notes.

## Schema Rule

Any **data shape** change (API payloads, config files, DB columns, persisted events, interchange formats) must include:

- **Schema version** (bump or explicit version field as appropriate for the system).
- **Migration notes** (how to move from old to new shape).
- **Backward compatibility notes** (what old producers/consumers may still send; deprecation timeline if any).

## Documentation Rules

After meaningful changes:

| Change | Required update |
|---|---|
| task completed | `project_status.md`, append `project_history.md` |
| behavior changed | `project_status.md`, append `project_history.md` |
| architecture changed | append `repo_map.md` delta, update `project_memory/index.json`, append `project_history.md` |
| durable lesson found | append `project_knowledge.md`, update `project_memory/index.json` if navigation changed |
| blocker found | `project_status.md`, append `project_history.md` |
| docs created | `project_status.md`, `project_memory/index.json`, append `project_history.md` |
| both `project_history.md` and `.project_intel/` touched for same change | same `YYYY-MM-DD` + same one-line summary in both (see **Dual chronology**); append audit to `project_history.md` |

## Write Rules

- Append new history entries only.
- Append new knowledge notes only.
- Append repo-map deltas unless full regeneration is explicitly requested.
- Keep `project_status.md` short and current.
- Keep `project_memory/index.json` compact and valid JSON.
- Update `project_memory/index.json` after structural/doc navigation changes.
- Never rewrite full `project_history.md` just to add an entry.
- Never regenerate `repo_map.md` unless requested.

## Final Response Must Include

Completion-style report. Include each item; use “n/a” or one line when not applicable.

- **Files changed** — code and docs paths.
- **Docs read** — which project docs or files were consulted (bounded reads count).
- **Docs changed** — created, updated, or appended; say if none.
- **Rules added or changed** — Cursor rules, `AGENTS.md` policy, hooks, etc.; say if none.
- **Architecture mapping** — if layout or folder roles were discovered or changed, point to the `repo_map.md` section or delta; say if none.
- **Unresolved risks** — known follow-ups or merge/deploy risks; say “none known.”
- **Commands run** — with enough context to reproduce (cwd, tool).
- **Command results** — pass/fail and short outcome; say if no commands were run.
- **Blockers** — if any.

If the agent relied on a **large full-read** of a normally bounded doc, say which file and **why** the exception was needed.

## Project memory (optional)

- Prefer `project_memory/index.json` for lightweight navigation when populated.
- Use `repo_map.md` for human-oriented layout; avoid full reads of `project_history.md` by default.
- Keep `project_memory/index.json` aligned with the repo when structure or doc paths change.
