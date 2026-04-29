# Project status (animus)

## Current state

Phase **7** landed: **no Browse** on server path fields (hints + examples), **Slack** Settings + `integrations_slack.py` + `animus.env.example`, **SSH hosts** global (`ssh_routes.py`, `docs/ssh.md`, simplified remote project flow), **token tracker** server log + `by_source` UI + CSV `source`/`source_id`, **chat** + **cron** token recording, **`claude-code`** inference row + catalog (`auto` + Hermes anthropic list), **Copilot ACP** relabelled, **`tts_backend`** in client-config. Phase **6** items (model refresh, cron UI, Piper TTS, skills create, etc.) remain underneath.

## Active goal

Ship ANIMUS v1.0.0 for Gumroad per `project_goal.md` once smoke + Docker are verified on a real host.

## Current priorities

1. Human run **Phase 3 smoke** (Task 7) using `scripts/phase3-smoke-checklist.md` with clean data dir + gateway.
2. Run **Docker** build/up/curl on a machine with Docker installed (Task 8).

## Recently completed work

- **Ghost branding + PWA:** **`ghostonlyicon.png`** for sidebar + chat header, empty state, favicon, **`manifest.json`** icons, apple-touch, About + notifications; **`animus-v2`** SW cache; desktop launcher prefers this file for `Icon=`.
- **Desktop launcher:** `installer/create-desktop-launcher.sh` + hook from `install.sh`; `GET /api/animus/desktop-launcher` (+ `?fmt=webloc`); wizard one-time download on desktop after **Open ANIMUS** (phones unchanged for PWA). See `INSTALL.md`.
- **HELP:** Settings **HELP** opens a **tabbed help center** (Home, Topics with section nav, FAQ, Ask ANIMUS); `GET /api/help/guide` returns structured fields + expanded **FAQ** in `docs/animus-user-guide.md`. Notification sidebar: per-thread unread + accent; Settings toggles for badges + wake lock.
- **TTS defaults:** Piper + **`en_GB-alan-medium`** when unset (localStorage + `config.json` without `tts_backend`); HF/install bundle downloads GB Alan first.
- **SSH Settings modal:** Add/edit host dialog — auth radio layout fixed (`#sshFormAuthRadios`); IdentitiesOnly and relax strict host key options use toggle-style rows (same ids for API payloads).
- Phase 3 code: `cron_routes.py` logs, `skills_routes.py` capabilities + detail/readme + updates shape, `server.py` client-config + `chat_data_dir` import, `hermes_runner.chat_data_dir`, `wizard_routes` paths, `app/index.html` skills UX + wake lock + wizard wake + token CSV/SSE, `docs/hermes-agent-patches.md` expansion, `INSTALL.md` Docker, `build-release.sh` patch count, smoke checklist script.
- Docs: `project_goal.md` Phase 3 Task 7 smoke setup/teardown uses **`CHAT_DATA_DIR`** + **`.venv/bin/python` / `python3`**; Phase 2 Docker acceptance + Phase 3 Task 8 curls use **`curl -sS` … `| python3 -m json.tool`**; Phase 4 Step 1 API-key reminder; Phase 4 Step 3 token stream check uses **`python3`** (not `grep`-only); wake lock acceptance text uses **`chat_data_dir()`** / `config.json`.

## In-progress work

- **Phase 3 smoke** in progress on host (Step 2 logged **PASS**); remaining steps + Docker curl evidence.
- **Owner re-check** after Phase 6: Settings model refresh, Cursor model row + Auto, cron dropdown + timezone persistence, create skill, read-aloud Piper (if installed), add-project goal copy — per `project_goal.md` Phase 6 table when present.

## Known issues

- **Smoke test & Docker** not executed in the agent sandbox (no Docker; no live gateway/API key). Checklist and INSTALL commands are ready for the operator.
- **Token tracker:** server also logs usage from the chat proxy when the gateway emits `usage` on SSE; Plan steps and skill APIs can append via `POST /api/tokens/record` when responses include `usage`; cron manual runs log rows with null token counts until gateway exposes usage per job.
- **Release zip:** v1.0 acceptance cap **≤55MB** (~51MB typical). `build-release.sh` warns only if over **55MB**.
- **Hermes / agent updates:** Wizard step 1 only reports reachability (no `hermes --version` dump). ANIMUS **does not** schedule background `hermes update`; bundled agent changes ship with **git pull** / **Apply update** on the ANIMUS monorepo — see `docs/hermes-agent-patches.md`.

## Blockers

- None for code merge; **release** blocked on successful smoke + Docker on a real host.

## Validation status

- Run: `cd animus-chat && .venv/bin/python -c "import server"`
- Run: `./build-release.sh` from repo root
- Optional: `docker compose -f docker/docker-compose.yml build` (requires Docker)

## Last validation run

- `./build-release.sh` — **pass** (2026-04-29: Plan token record + TTS layout + docs); zip ~51MB.
- `cd animus-chat && .venv/bin/python -c "import server"` — **pass**.
- Phase 5 coder smoke (API + grep): see **Phase 5 acceptance smoke** table below.

## Next recommended actions

1. Execute `scripts/phase3-smoke-checklist.md` and paste results into **Phase 3 Smoke Test** below.
2. `cd docker && docker compose build && docker compose up -d && curl -sS http://127.0.0.1:3001/api/version`

---

## Phase 3 Smoke Test

| Step | Result | Notes |
|------|--------|-------|
| 1 | **Pending** | Requires clean `CHAT_DATA_DIR` / `config.json` with `first_run: true` |
| 2 | **PASS** | Wizard **Agent check** / `GET /api/setup/hermes-check`: **PASS** (CLI reachable; v0.11.0 etc. from host `hermes --version`, not shown in wizard UI) |
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
| `POST /api/animus/check-updates` | **PASS (API)** | No `HEAD`: `ok:false` with INSTALL.md clone message (not raw git stderr); valid clone: fetch + `rev-list` → up-to-date or commits-behind. |
| Apply update + restart flow | **PARTIAL** | Same `HEAD` guard as check-updates; full pull UX **MANUAL** after updates available. |
| `git remote get-url origin` | **PASS** | `https://github.com/SketchOTP/animus.git` after prescribed `remote add`. |
| `./build-release.sh` | **PASS** | Completed after removing `animus-chat/.venv-smoke`. |
| Zip ≤55MB (v1.0) | **PASS** | `./build-release.sh` — **51 MB** under 55MB cap; NOTE only if over 55MB. |
| Codex: `codex-auth-start` instant | **PASS (API)** | `curl` `time_total≈0.003s`, body `{"ok":true,"status":"pending","poll_id":"…"}`. |
| Codex: status polls every 3s | **PASS (static)** | `runCodexAuthWithPoll`: `setTimeout(res, 3000)` before each `codex-auth-status` fetch (`index.html` ~2496–2497). |
| Codex: Network tab (browser) | **MANUAL** | Owner: DevTools open on “Sign in with Codex”; confirm start once + status ~3s apart. |

---

## v1.1 backlog (post–v1.0 Gumroad)

- **Trim release zip** toward 50MB or smaller if desired (v1.0 cap is 55MB).
- **Hermes Agent upstream rebase:** Reconcile bundled `hermes-agent/` with newer upstream (e.g. 778+ commits drift as of smoke Step 2); use `docs/hermes-agent-patches.md` as merge checklist; full acceptance re-test.
- Windows `install.ps1` on real hardware.
- Skills enable/disable when Hermes bundles scriptable toggles (capabilities already gate the UI).
- Richer cron log tail (e.g. gateway log shipping) if product needs it.
- Auto-update / version ping for ANIMUS releases.
- **Auto-mount sshfs** when a remote project is opened (operator still runs `sshfs` manually for v1.0; see `docs/ssh.md`).
