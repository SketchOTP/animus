# Project status (animus)

## Current state

**Marketing site (`animus-site/` sibling):** product-led marketing + update API. **Buyer-facing URL:** **`https://animusai.vercel.app`** only (Vercel alias to Production) so **`/releases/*.zip`**, **`/api/latest.json`**, **`/seller-publish.html`**, and **`POST /api/admin/publish`** share one hostname. Re-run **`vercel alias set <new-deployment> animusai.vercel.app`** from **`animus-site/`** after each **`vercel --prod`**.

Phase **8** landed: **manifest + zip** in-app updates (**`ANIMUS_UPDATE_URL`**), no git in **`installer/install.sh`** or update APIs; launch banner + Settings flow; seller may use **`animus-site`** (Vercel + Redis, sibling repo) or self-hosted **`animus-update-server/`**. Phase **7** items remain underneath: **no Browse** on server path fields (hints + examples), **Slack** Settings + `integrations_slack.py` + `animus.env.example`, **SSH hosts** global (`ssh_routes.py`, `docs/ssh.md`, simplified remote project flow), **token tracker** server log + `by_source` UI + CSV `source`/`source_id`, **chat** + **cron** token recording, **`claude-code`** inference row + catalog (`auto` + Hermes anthropic list), **Copilot ACP** relabelled, **`tts_backend`** in client-config. Phase **6** items (model refresh, cron UI, Piper TTS, skills create, etc.) remain underneath.

## Active goal

Ship ANIMUS v1.0.0 for Gumroad per `project_goal.md` once smoke + Docker are verified on a real host.

## Current priorities

1. Human run **Phase 3 smoke** (Task 7) using `scripts/phase3-smoke-checklist.md` with clean data dir + gateway.
2. Run **Docker** build/up/curl on a machine with Docker installed (Task 8).

## Recently completed work

- **`seller-private/`:** repo-root folder for local seller secrets (e.g. Vercel **`ADMIN_TOKEN`**); gitignored except **`README.md`**; excluded from **`build-release.sh`** zip + leak check. See **`seller-private/README.md`** and **`docs/GUMROAD.md`**.
- **Seller release UX:** sibling **`animus-site`**: **`seller-publish.html`** (root static; **`/admin/release.html`** 308 → same) + **`js/release-admin.js`** + **`api/release_upload.js`** (Vercel Blob + HMAC challenge); **`docs.html`** links sellers. **`scripts/release-and-publish.sh`** in **`animus/`** copies zip to **`animus-site/releases/`** and runs **`vercel --prod`**. Docs: **`animus-site/README.md`**, **`releases/README.md`**, **`docs/GUMROAD.md`**. **`animus.env`:** **`preflight.sh`** copies example when missing; Docker **`Dockerfile`** bakes **`/app/animus.env`** from example.
- **Fresh install skills:** `animus-chat/server.py` runs `tools.skills_sync.sync_skills()` once at import so `HERMES_HOME/skills` is seeded from bundled `hermes-agent/skills/` (Hermes CLI did this only when `hermes` ran; ANIMUS-only starts skipped it → empty `/api/skills/list`).
- **animus-site Gumroad launch link:** all shared buy/Gumroad CTAs now point to **`https://sketcher571.gumroad.com/l/cxueq`**; deployed with `vercel --prod --yes` and re-aliased **`animusai.vercel.app`**.
- **animus-site product-led redesign:** replaced generic placeholder marketing with an ANIMUS-themed landing page using the PNG brand assets, mock app shell, actual feature copy, and stylized SVG previews for Chat, Wizard, Settings, and Cron; updated shared header/footer on docs + updates; deployed with `vercel --prod --yes` and re-aliased **`animusai.vercel.app`** to the redesigned deployment.
- **animus-site brand layout:** header brand marks now use **`ghostonlyicon.png`**; the large ANIMUS logo is centered above the homepage hero section below the header; deployed and re-aliased **`animusai.vercel.app`**.
- **Gumroad zip readiness:** regenerated **`animus-v1.0.0.zip`** after tightening `build-release.sh` to exclude **`hermes-agent/.env`**, **`hermes-agent/.envrc`**, and **`*.flock`**; archive is **28MB**, `unzip -tq` passes, and raw env/runtime/internal docs checks are clean.
- **animus-site copy cleanup:** adjusted homepage hero/workspace copy, removed internal explanatory paragraphs, removed the v1.0/3001/zip/SaaS stat bar and unused CSS, deployed and re-aliased **`animusai.vercel.app`**.
- **animus-site release notes fix:** `updates.html` now ships static v1.0.0 fallback content instead of "Loading..." and loads API enhancement from external **`js/updates.js`**; deployed and re-aliased **`animusai.vercel.app`** to the fixed deployment.
- **Phase 8 auto-updates:** **`ANIMUS_UPDATE_URL`** + httpx manifest **`check-updates`** / zip **`apply-update`** in **`server.py`** (zip-slip guard); no git in **`installer/install.sh`**; launch banner + Settings UX in **`index.html`**; **`docs/BUYER_UPDATES.md`**, **`INSTALL.md`**, **`GUMROAD.md`**, **`animus-user-guide.md`**, **`build-release.sh`** checks; sibling **`animus-update-server/`** (FastAPI, not in buyer zip).
- **Release zip v1.0 cap:** `build-release.sh` trims bloat + **internal dev docs** (`project_*.md`, `AGENTS.md`, `.cursor/`, `setup_repo.md`, `animus-chat` mirrors, etc.) from the buyer zip; **hard fail** if zip **>55MB**; typical artifact **~28MB**.
- **Release checklist automation:** **`build-release.sh`** post-zip leak check (no raw `animus.env`, `hermes-chat.env`, `hermes-agent/.env`, `.flock`, no `animus-chat/data/`); zip excludes **`animus-chat/animus.env`** + **`hermes-agent/.env`**; UI path examples use **`/home/you/projects`** (not owner home).
- **Gumroad packaging:** root **`START_HERE.txt`** for post-unzip buyers; **`docs/GUMROAD.md`** seller checklist + listing/thank-you copy; **`README.md`** download pointer; **`build-release.sh`** checklist lines.
- **First-run wizard:** `first_run` cleared when the **final “You are all set”** step is painted (not only on “Open ANIMUS”); `cfg_still_first_run()` normalizes string/number `first_run` values; `setup_completed_at` written on complete.
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
- **Release zip:** v1.0 cap **≤55MB** — `build-release.sh` **fails** if over cap; trims omit Ghost3D, `hermes-agent/tests`, `hermes-agent/website`, WhatsApp bridge `node_modules` (see INSTALL).
- **Hermes / agent updates:** Wizard step 1 only reports reachability (no `hermes --version` dump). ANIMUS **does not** schedule background `hermes update`; monorepo file updates ship via **manifest + zip** in-app update or manual reinstall — see `docs/hermes-agent-patches.md`.

## Blockers

- None for code merge; **release** blocked on successful smoke + Docker on a real host.

## Validation status

- Run: `cd animus-chat && .venv/bin/python -c "import server"`
- Run: `./build-release.sh` from repo root
- Optional: `docker compose -f docker/docker-compose.yml build` (requires Docker)

## Last validation run

- `node --check /home/sketch/animus-site/js/main.js` — **pass** (2026-04-29 Gumroad launch link).
- `vercel --prod --yes` from `/home/sketch/animus-site` after Gumroad launch link — **pass** (2026-04-29); deployment **`animus-site-isulmyvgv-sketchotp-3398s-projects.vercel.app`** re-aliased to **`animusai.vercel.app`**.
- Live link smoke: `curl -L -sS https://animusai.vercel.app/js/main.js` and Chromium DOM check for **`https://sketcher571.gumroad.com/l/cxueq`** — **pass**; header, hero, pricing, and footer CTAs render the real Gumroad URL.
- `vercel --prod --yes` from `/home/sketch/animus-site` — **pass** (2026-04-29); buyer checks use **`https://animusai.vercel.app`** only.
- `./build-release.sh` — **pass** (2026-04-29 Gumroad readiness check); regenerated **`animus-v1.0.0.zip`** at **28MB**; `unzip -tq` pass; no raw env, runtime data, lock files, `animus-update-server/`, or internal project docs found.
- `vercel --prod --yes` from `/home/sketch/animus-site` after brand layout change — **pass** (2026-04-29); deployment **`animus-site-dvolgn219-sketchotp-3398s-projects.vercel.app`** re-aliased to **`animusai.vercel.app`**; live greps confirm header **`ghostonlyicon.png`** and **`hero__section-logo`**.
- `vercel --prod --yes` from `/home/sketch/animus-site` after homepage copy cleanup — **pass** (2026-04-29); deployment **`animus-site-d0ylje2ua-sketchotp-3398s-projects.vercel.app`** re-aliased to **`animusai.vercel.app`**; live greps confirm new copy and removed phrases absent.
- `vercel --prod --yes` from `/home/sketch/animus-site` after release-notes fix — **pass** (2026-04-29); deployment **`animus-site-3d04sl1nv-sketchotp-3398s-projects.vercel.app`** re-aliased to **`animusai.vercel.app`**.
- Release notes smoke: `curl -L https://animusai.vercel.app/updates.html` and Chromium DOM check — **pass**; both latest and past releases render **v1.0.0 / Initial release** and no **Loading...** text remains.
- `vercel alias set animus-site-h1fn3n46l-sketchotp-3398s-projects.vercel.app animusai.vercel.app` — **pass** (2026-04-29); `curl https://animusai.vercel.app/` shows redesigned copy.
- Remote smoke: `curl -L -sS https://animusai.vercel.app/` greps for redesigned homepage copy; docs + updates greps — **pass**.
- Local smoke: `python3 -m py_compile /home/sketch/animus-site/api/*.py /home/sketch/animus-site/lib_redis.py`; HTML parser for `index.html`, `updates.html`, `docs.html`; Chromium screenshots at 1440px + 390px — **pass**.
- `./build-release.sh` — **pass** (2026-04-29 Phase 8); zip **~28MB**; adds **`ANIMUS_UPDATE_URL`** / no-git / **`httpx`** checks.
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
| `POST /api/animus/check-updates` | **MANUAL** | Needs **`ANIMUS_UPDATE_URL`** + live manifest; empty URL → `ok:false` with configure message. |
| Apply update + restart flow | **MANUAL** | Zip download + extract + **`POST /api/restart/chat`**; exercise on non-production install. |
| Git-based buyer updates | **Removed** | Phase 8: manifest + zip only; no **`origin`** / installer git. |
| `./build-release.sh` | **PASS** | Completed after removing `animus-chat/.venv-smoke`. |
| Zip ≤55MB (v1.0) | **PASS** | `./build-release.sh` — **~28MB** typical after ship trims; script **exits 1** if over 55MB. |
| Codex: `codex-auth-start` instant | **PASS (API)** | `curl` `time_total≈0.003s`, body `{"ok":true,"status":"pending","poll_id":"…"}`. |
| Codex: status polls every 3s | **PASS (static)** | `runCodexAuthWithPoll`: `setTimeout(res, 3000)` before each `codex-auth-status` fetch (`index.html` ~2496–2497). |
| Codex: Network tab (browser) | **MANUAL** | Owner: DevTools open on “Sign in with Codex”; confirm start once + status ~3s apart. |

---

## v1.1 backlog (post–v1.0 Gumroad)

- **Further trim** (optional): only if the zip grows again toward 55MB after new bundled assets.
- **Hermes Agent upstream rebase:** Reconcile bundled `hermes-agent/` with newer upstream (e.g. 778+ commits drift as of smoke Step 2); use `docs/hermes-agent-patches.md` as merge checklist; full acceptance re-test.
- Windows `install.ps1` on real hardware.
- Skills enable/disable when Hermes bundles scriptable toggles (capabilities already gate the UI).
- Richer cron log tail (e.g. gateway log shipping) if product needs it.
- Auto-update / version ping for ANIMUS releases.
- **Auto-mount sshfs** when a remote project is opened (operator still runs `sshfs` manually for v1.0; see `docs/ssh.md`).
