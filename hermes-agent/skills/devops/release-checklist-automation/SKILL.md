---
name: release-checklist-automation
description: >
  Repeatable release workflow for software projects — branch hygiene, automated
  test/lint gates, version and changelog alignment, tagging, GitHub release, and
  post-release verification. Includes Hermes Agent–specific commands where applicable.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    category: devops
    tags: [release, CI/CD, versioning, changelog, shipping, automation, git, GitHub]
    related_skills: [github-pr-workflow, requesting-code-review, webhook-subscriptions]
---

# Release Checklist Automation

Structured checklist for cutting a release with **automatable gates first**, then human sign-off. Adapt commands to the stack (Python, Node, Rust, Go, etc.); defaults below favor common open-source patterns.

## When to use

- User asks to **ship**, **cut a release**, **tag**, **publish**, or **prep CHANGELOG**
- After a merge-ready PR lands on the release branch (`main`, `master`, or `release/x.y`)
- When you must ensure **tests + version + changelog + tag** stay in sync

**Pair with:** `requesting-code-review` before the final merge; `github-pr-workflow` for PR/CI/merge mechanics.

---

## Phase 0 — Preconditions (manual + quick commands)

1. **Target branch** — Confirm release is cut from the correct branch (usually `main`).
2. **Clean working tree** — No stray edits; everything intended is committed.
   ```bash
   git status
   ```
3. **CI green on the commit you will tag** — Do not tag a red build unless explicitly waived.
4. **Secrets / tokens** — Publishing (PyPI, npm, GH releases) requires credentials; never commit them.

---

## Phase 1 — Automated quality gates

Run the project’s canonical test and lint commands. **Discover** them from repo files rather than guessing:

| Signal | Typical command |
|--------|-----------------|
| `scripts/run_tests.sh` | `./scripts/run_tests.sh` or `bash scripts/run_tests.sh` |
| `pytest` / `pyproject.toml` | `python -m pytest` or project wrapper |
| `package.json` test | `npm test` or `pnpm test` |
| `Makefile` | `make test` |
| Rust | `cargo test` |
| Go | `go test ./...` |

**Hermes Agent repo (reference):** from repo root, use the project test wrapper:

```bash
cd /path/to/hermes-agent
./scripts/run_tests.sh
```

Record exit code; **block the release** if tests fail unless the user explicitly accepts risk.

**Lint / typecheck** — run only if configured (`ruff`, `mypy`, `eslint`, `cargo clippy`, etc.).

---

## Phase 2 — Version and changelog alignment

1. **Single source of truth** — Bump version wherever the project defines it (`pyproject.toml`, `package.json`, `Cargo.toml`, `__init__.py`, Helm chart, etc.). Keep duplicates in sync.
2. **Changelog** — Add a dated section: highlights, breaking changes, migrations, deprecations. Link PRs/issues when the project does that consistently.
3. **Diff review** — `git diff` for version + changelog only; no unrelated edits in the release commit.

**Hermes Agent (reference):** `scripts/release.py` reads `hermes_cli/__init__.py` and `pyproject.toml`. Preview:

```bash
cd /path/to/hermes-agent
python scripts/release.py
```

Publish flow (when user asks to actually ship): see `python scripts/release.py --help` for `--bump`, `--publish`, and CalVer options.

---

## Phase 3 — Tag and release artifact

1. **Tag** — Use the project’s tagging convention (`v1.2.3`, `release/2026.05.03`, etc.). Annotated tags are preferred for apps/libraries.
   ```bash
   git tag -a vX.Y.Z -m "Release vX.Y.Z"
   git push origin vX.Y.Z
   ```
2. **GitHub Release** — `gh release create` with notes from the changelog, or use `scripts/release.py --publish` if that is the team workflow.
3. **Package registry** — PyPI, npm, crates.io, container registry: follow existing `publish` / `release` CI jobs or documented `twine`/`npm publish` steps.

---

## Phase 4 — Post-release

1. Confirm the **release artifact** appears (GitHub Releases page, PyPI project, Docker tag).
2. If the project maintains **docs or website** version strings, bump or trigger deploy.
3. **Announce** per team norms (Slack, Discord, blog) — optional unless user requests.
4. **Branch hygiene** — merge or cherry-pick hotfix strategy documented for the team.

---

## Templates

- `templates/minimal-release-checklist.md` — blank checklist with placeholders (`{{REPO_NAME}}`, `{{VERSION}}`). Copy into a GitHub issue, PR description, or release ticket and replace placeholders.

---

## Minimal printable checklist

Copy into an issue or PR description; check off in order:

- [ ] Release branch / commit identified; CI green
- [ ] Tests (and lint if applicable) pass locally or in CI for that commit
- [ ] Version bumped in all required locations
- [ ] Changelog / release notes updated
- [ ] Release commit pushed (or PR merged) to the release line
- [ ] Tag created and pushed
- [ ] GitHub Release (or equivalent) published with correct notes
- [ ] Package / container published if applicable
- [ ] Post-release smoke test (install from registry or run binary)

---

## Pitfalls

- Tagging **before** changelog/version commits — creates wrong metadata on the tag; delete and retag only if no consumers pulled the bad tag yet.
- **CalVer vs SemVer** — match whatever the repo already uses; do not mix schemes in one project without maintainer approval.
- **Squash-merge drift** — stale release branches can revert fixes; rebase or merge `main` before cutting.
- Skipping **schema/config migration notes** when the release changes persisted formats (see project Schema Rule).

---

## Automation hints for agents

- Prefer **one release commit** that only touches version + changelog when possible.
- Use `read_file` / `search_files` to find version keys and CI entrypoints instead of assuming filenames.
- If the user only asked for a **dry run**, execute tests + `git diff` summary and stop before `git tag` or `--publish`.
