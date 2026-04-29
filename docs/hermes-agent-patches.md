# Hermes Agent — ANIMUS patch record

**Bundled version:** v0.11.0 (2026.4.23). **Upstream drift:** as of this ANIMUS release, upstream `hermes-agent` was **778 commits ahead** of the bundled tree (measured on the release host). Customers receive this **patched, tested** snapshot — **do not** run `hermes update` (or similar in-place upstream sync) inside the ANIMUS install; it can **overwrite** the customisations recorded below and break gateway/chat alignment until re-patched.

**v1.1+ planning:** Rebasing ANIMUS’s patches onto a newer Hermes Agent is a real upgrade task with real merge risk. The sections in this document are the checklist that makes that manageable when you choose to do it.

## How to read this doc

Each section summarizes how the bundled `hermes-agent/` in ANIMUS differs from the upstream public repository, and why that matters for releases.

## Upstream

- Remote: `https://github.com/NousResearch/hermes-agent.git`
- The copy under `hermes-agent/` at the ANIMUS monorepo root was taken from the owner's live install (not a fresh upstream clone). It may be **ahead/behind** `origin/main`. Smoke **Step 2** (2026-04-29) reported bundled **v0.11.0 (2026.4.23)** with upstream **778 commits** ahead — re-verify drift before each release (e.g. `git fetch origin && git rev-list --count HEAD..origin/main` from `hermes-agent/`).

## Patch 1 — Local commits and working tree

**File(s):** entire `hermes-agent/` tree  
**Type:** configuration change / fork alignment  
**What it does:** The vendored tree may contain **local commits** and **modified files** versus `origin/main` (see recent `git log` on the bundle host).  
**Why it exists:** ANIMUS ships a known-good agent + gateway snapshot with the chat UI.  
**Risk if removed:** Replacing the folder with a fresh upstream clone without re-running ANIMUS acceptance tests can break gateway/chat alignment, cron paths, or Cursor integrations.  
**Test to verify:**

```bash
cd hermes-agent
git status -sb
git log --oneline -20
git diff origin/main --stat
```

## Patch 2 — Cursor / IDE integrations

**File(s):** `gateway/platforms/api_server.py`, Cursor-related shims (see tree)  
**Type:** provider addition / IDE integration  
**What it does:** Upstream gateway and tooling reference Cursor-driven flows (for example subprocess shims such as `cursor-agent`, `CURSOR_API_KEY`, or logged-in Cursor CLI).  
**Why it exists:** ANIMUS users select Cursor-backed backends from the chat UI.  
**Risk if removed:** Cursor-backed chat and agent tooling stops working for installs that rely on this snapshot.  
**Test to verify:** In ANIMUS Settings, select the Cursor provider and send a test message. The response should arrive using Cursor's underlying model. The per-message provider badge should show `cursor` or the specific Cursor model name.

**ANIMUS rule:** do not re-implement these integrations from scratch; carry forward the same files and CLI behaviour as in the bundled agent, then re-verify after each merge from upstream.

## Patch 3 — Skills and cron CLI surface

**File(s):** `hermes-agent/tools/skills_tool.py`, `hermes-agent/cron/jobs.py`, `hermes-agent/cron/scheduler.py` (indirectly)  
**Type:** new feature (CLI + data layout)  
**What it does:** Hermes Agent exposes `hermes skills …` and `hermes cron …` subcommands. Job output is written under `~/.hermes/cron/output/<job_id>/<timestamp>.md` (see `cron/jobs.py`). ANIMUS routes (`skills_routes.py`, `cron_routes.py`) wrap the CLI and local stores so the browser never shells out.  
**Why it exists:** ANIMUS Settings, Skills, and Cron tabs depend on the same layout as the gateway.  
**Risk if removed:** ANIMUS cron log tail and skills install/update/remove will fail or drift from the gateway.  
**Test to verify:** `hermes skills list` and `hermes cron list` succeed on the host; ANIMUS Skills tab loads; create a cron job and confirm a file appears under `~/.hermes/cron/output/<job_id>/` after a run.

### Skill enable / disable (Phase 2 — Option C) + capabilities (Phase 3)

`GET /api/skills/capabilities` runs `hermes skills --help` / `hermes skill --help` and reports whether install / update checks / enable-disable verbs appear in help text. The UI hides enable/disable controls when `enable_disable_supported` is false.

- `POST /api/skills/enable/{id}` and `POST /api/skills/disable/{id}` return **HTTP 200** with `{ "ok": false, "error": "…Use \`hermes skills config\`…" }` when the CLI does not support toggles (not HTTP 501).
- Operators should use **`hermes skills config`** in a terminal until a future Hermes Agent adds scriptable toggles.

## Patch 4 — ANIMUS monorepo alignment (chat data dir)

**File(s):** `animus-chat/hermes_runner.py` (`chat_data_dir`), `animus-chat/server.py` (`DATA_DIR`), `animus-chat/setup_wizard/wizard_routes.py`  
**Type:** configuration change  
**What it does:** Wizard `config.json` and model cache paths use the same directory resolution as Hermes Chat conversations (`CHAT_DATA_DIR` / `HERMES_CHAT_DATA_DIR` / `~/.hermes/chat` default).  
**Why it exists:** Phase 2 stored wizard state under `./data` while chats lived under `~/.hermes/chat`, so `first_run` and wake-lock prefs could diverge.  
**Risk if removed:** Wizard may not reappear on first launch, or wake lock may not persist next to real chat data.  
**Test to verify:** With a clean `config.json` under the resolved chat data dir, open ANIMUS on port 3001 and confirm the wizard shows once; after completion, confirm `wake_lock` is present in the same `config.json`.

## Patch 5 — Known gaps (cron logs from ANIMUS host)

**File(s):** `animus-chat/cron_routes.py`  
**Type:** configuration change / documentation  
**What it does:** `GET /api/cron/logs/{id}` tries `hermes cron logs <id>`, then reads markdown under `cron/jobs.OUTPUT_DIR`. If neither yields content, the API returns `{ "lines": [], "error": "…" }` (no fake placeholder lines).  
**Why it exists:** Some builds or hosts do not expose log tail to the chat process; a clear error is preferable to fabricated log lines.  
**Risk if removed:** Users may see misleading placeholder “log” content.  
**Test to verify:** Open Cron → Logs on a job that has run; expect either real lines or the documented error string — never a fake success message.

## Maintenance

Before merging new upstream Hermes Agent commits into ANIMUS:

1. Re-run the diff commands in Patch 1.
2. Append a new `## Patch N` section for every behavioural change.
3. Re-run ANIMUS acceptance checks (installer, Docker, wizard, chat proxy).
