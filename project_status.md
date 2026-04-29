# Project status (animus)

## Current state

Phase **5** wizard + Settings work landed in repo: **8-step wizard** (Welcome → Hermes → provider checklist/auth → default model scoped to configured providers → skills manager → projects folder path → Tailscale + wake lock → Done), **Settings inference matrix** (`/api/setup/provider-status`, per-provider models + keys + Codex/Cursor sign-in), **About ANIMUS** copy + separate **Check for updates** (`POST /api/animus/check-updates` / `apply-update`), **Plan tab** branding (ANIMUS not Hermes product name), **`build-release.sh`** Phase 5 greps, **`installer/install.sh`** optional `git remote add origin` for SketchOTP/animus.

## Active goal

Ship ANIMUS v1.0.0 for Gumroad per `project_goal.md` once smoke + Docker are verified on a real host.

## Current priorities

1. Human run **Phase 3 smoke** (Task 7) using `scripts/phase3-smoke-checklist.md` with clean data dir + gateway.
2. Run **Docker** build/up/curl on a machine with Docker installed (Task 8).

## Recently completed work

- Phase 3 code: `cron_routes.py` logs, `skills_routes.py` capabilities + detail/readme + updates shape, `server.py` client-config + `chat_data_dir` import, `hermes_runner.chat_data_dir`, `wizard_routes` paths, `app/index.html` skills UX + wake lock + wizard wake + token CSV/SSE, `docs/hermes-agent-patches.md` expansion, `INSTALL.md` Docker, `build-release.sh` patch count, smoke checklist script.
- Docs: `project_goal.md` Phase 3 Task 7 smoke setup/teardown uses **`CHAT_DATA_DIR`** + **`.venv/bin/python` / `python3`**; Phase 2 Docker acceptance + Phase 3 Task 8 curls use **`curl -sS` … `| python3 -m json.tool`**; Phase 4 Step 1 API-key reminder; Phase 4 Step 3 token stream check uses **`python3`** (not `grep`-only); wake lock acceptance text uses **`chat_data_dir()`** / `config.json`.

## In-progress work

- **Phase 3 smoke** in progress on host (Step 2 logged **PASS**); remaining steps + Docker curl evidence.
- **Phase 5 owner walkthrough** (wizard 3–8 + Settings Network for Codex) still needed to declare Phase 5 fully accepted per `project_goal.md`.

## Known issues

- **Smoke test & Docker** not executed in the agent sandbox (no Docker; no live gateway/API key). Checklist and INSTALL commands are ready for the operator.
- **Token tracker** still depends on the gateway including **usage** in streamed chat completions (`include_usage` is requested from the client).
- **Release zip** may exceed **50MB** (~51MB in one build) depending on vendored `hermes-agent/` size — trim or split ship tree if Gumroad requires hard cap.

## Blockers

- None for code merge; **release** blocked on successful smoke + Docker on a real host.

## Validation status

- Run: `cd animus-chat && .venv/bin/python -c "import server"`
- Run: `./build-release.sh` from repo root
- Optional: `docker compose -f docker/docker-compose.yml build` (requires Docker)

## Last validation run

- `./build-release.sh` — **pass** (after smoke venv removed from `animus-chat/`; see Phase 5 smoke notes); zip ~51MB.
- Phase 5 coder smoke (API + grep): see **Phase 5 acceptance smoke** table below.

## Next recommended actions

1. Execute `scripts/phase3-smoke-checklist.md` and paste results into **Phase 3 Smoke Test** below.
2. `cd docker && docker compose build && docker compose up -d && curl -sS http://127.0.0.1:3001/api/version`

---

## Phase 3 Smoke Test

| Step | Result | Notes |
|------|--------|-------|
| 1 | **Pending** | Requires clean `CHAT_DATA_DIR` / `config.json` with `first_run: true` |
| 2 | **PASS** | Hermes Agent check: **PASS**. v0.11.0 (2026.4.23), Python 3.11.15 |
| 3 | **Pending** | |
| 4 | **Pending** | |
| 5 | **Pending** | |
| 6 | **Pending** | |
| 7 | **Pending** | |
| 8 | **Pending** | |
| 9 | **Pending** | |
| 10 | **Pending** | |
| 11 | **Pending** | |
| 12 | **Pending** | |
| 13 | **Pending** | Depends on gateway usage in SSE |
| 14 | **Pending** | |
| 15 | **Pending** | |
| 16 | **Pending** | `./build-release.sh` |

---

## Phase 5 acceptance smoke (coder: API + static checks)

Server: `CHAT_DATA_DIR=/tmp/animus-smoke-*` + venv **outside** `animus-chat/` (or use existing `.venv`); a venv **inside** `animus-chat/.venv-*` trips `build-release.sh` sanitisation grep on pip vendor files.

| Criterion | Result | Evidence (one line) |
|-----------|--------|----------------------|
| Step 3 provider checklist + Continue / Skip all | **PASS (static)** | `index.html`: `wizSkipAll`, `wizProvContinue`, `wizard_selected_providers` payloads. |
| Test button not error-labelled empty | **PASS (static)** | No `Enter a key before testing` in `index.html`. |
| Cursor folded into Step 3 (no standalone Cursor step) | **PASS (static)** | Provider/auth blocks share step flow; `cursor-check` / auth inline in wizard strings. |
| Step 5 models scoped to wizard providers | **MANUAL** | Needs browser walk + `GET /api/setup/models` after auth; not exercised in this run. |
| Cursor + Codex in model picker when authed | **MANUAL** | Requires Hermes `model list` + live auth. |
| Skills step: list + controls | **PASS (API)** | `GET /api/skills/list` → JSON array length **79** on this host. |
| “No hub-installed skills…” not default | **MANUAL** | UI-only; not loaded in headless smoke. |
| Projects step between Skills and Tailscale | **PASS (static)** | Wizard HTML: “Projects folder” block precedes “Tailscale access” (`index.html` ~8447 / ~8523). |
| Projects path validation | **PASS (API)** | `GET /api/setup/check-path?path=/tmp` → `{"ok":true,"resolved":"/tmp"}`. |
| Tailscale toggle + hostname + port | **PASS (static)** | `wizTsEn`, hostname + port fields in wizard Tailscale block. |
| Tailscale Verify | **PASS (API)** | `GET .../tailscale-check?hostname=invalid.invalid.test` → `ok:false` + hint string. |
| Wake lock only in Tailscale step | **PASS (static)** | “Keep screen awake while ANIMUS is generating” in Tailscale wizard block (~8543); Done step (~8640) has no wake checkbox. |
| Done screen: no wake checkbox | **PASS (static)** | Final wizard pane: `You are all set` + `Open ANIMUS` only. |
| Wizard 8 steps (Welcome … Done) | **PASS (static)** | Step flow in `paint()` covers Hermes → providers → auth → models → skills → projects → Tailscale → done. |
| Plan tab: no bare “Hermes” product name | **PASS (static)** | Plan copy: “Each **ANIMUS** plan step…” (`index.html` ~1019); forbidden Plan-tab greps absent. |
| `build-release.sh` Phase 5 greps | **PASS** | Script exit 0; includes Hermes Plan check, `check-updates`, `projects_dir`. |
| Settings inference matrix | **MANUAL** | API `provider-status` exists; full matrix UX needs browser. |
| Add key / Sign in / model guardrails | **MANUAL** | Browser Settings. |
| About copy + separate Check for updates buttons | **PASS (static)** | `aboutAnimusBtn` + `checkAnimusUpdatesBtn` adjacent (`index.html` ~1138). |
| `POST /api/animus/check-updates` | **FAIL (this workspace)** | Returns `ok:false` — git repo has **no local HEAD** matching `origin/main` until user checks out tracking `main` (empty `git init` is insufficient). |
| Apply update + restart flow | **NOT RUN** | Blocked until check-updates succeeds. |
| `git remote get-url origin` | **PASS** | `https://github.com/SketchOTP/animus.git` after prescribed `remote add`. |
| `./build-release.sh` | **PASS** | Completed after removing `animus-chat/.venv-smoke`. |
| Zip ≤50MB | **FAIL (known)** | Build reports **51 MB** (existing acceptance note). |
| Codex: `codex-auth-start` instant | **PASS (API)** | `curl` `time_total≈0.003s`, body `{"ok":true,"status":"pending","poll_id":"…"}`. |
| Codex: status polls every 3s | **PASS (static)** | `runCodexAuthWithPoll`: `setTimeout(res, 3000)` before each `codex-auth-status` fetch (`index.html` ~2496–2497). |
| Codex: Network tab (browser) | **MANUAL** | Owner: DevTools open on “Sign in with Codex”; confirm start once + status ~3s apart. |

---

## v1.1 backlog (post–v1.0 Gumroad)

- **Hermes Agent upstream rebase:** Reconcile bundled `hermes-agent/` with newer upstream (e.g. 778+ commits drift as of smoke Step 2); use `docs/hermes-agent-patches.md` as merge checklist; full acceptance re-test.
- Windows `install.ps1` on real hardware.
- Skills enable/disable when Hermes bundles scriptable toggles (capabilities already gate the UI).
- Richer cron log tail (e.g. gateway log shipping) if product needs it.
- Auto-update / version ping for ANIMUS releases.
