# Project status (animus)

## Current state

**Dev host:** `scripts/sync-dev-systemd.sh` + fixed **`animus.env.example`** **`HERMES_HOME`** (absolute path for systemd); **`restart-after-code-change.sh`** targets **`animus.service`** first; **`scripts/animus`** → **`~/.local/bin/animus`** for **`animus start|stop|restart|status`**; Docker **`ENV HERMES_HOME=/root/...`** overrides example placeholder.
- **PWA / multi-device chats:** `index.html` init always applies **`GET /api/convs`** (removed wrong `serverConvs.length >= convs.length` gate); refetch on **`visibilitychange`** + **`pageshow` (bfcache)** so phone reflects desktop deletes; **`sw.js`** cache **`animus-v16`** (Cron: collapsible **overseer**, **timezone `<dialog>`** picker, accent **prompt optimizer** + load state; **project scope** / **`workdir`**, composed prompt, **optimize-prompt**, messaging **`cron_deliver_home_ready`** deliver list; Plan: clarification **modal**; draft row **HHMM MMDDYY + idea** + **✎▶−**; chat **ghost**: 2× sidebar + 2× empty state; **no** ghost on main top bar next to New chat); **default `general` project** bootstrap + session-scoped auto-open).

**Marketing site (`animus-site/` sibling):** product-led marketing + update API. **Buyer-facing URL:** **`https://animusai.vercel.app`** only (Vercel alias to Production) so **`/releases/*.zip`**, **`/api/latest.json`**, **`/seller-publish.html`**, and **`POST /api/admin/publish`** share one hostname. Re-run **`vercel alias set <new-deployment> animusai.vercel.app`** from **`animus-site/`** after each **`vercel --prod`**.

Phase **8** landed: **manifest + zip** in-app updates (**`ANIMUS_UPDATE_URL`**), no git in **`installer/install.sh`** or update APIs; launch banner + Settings flow; seller may use **`animus-site`** (Vercel + Redis, sibling repo) or self-hosted **`animus-update-server/`**. Phase **7** items remain underneath: **no Browse** on server path fields (hints + examples), **Slack** Settings + `integrations_slack.py` + `animus.env.example`, **SSH hosts** global (`ssh_routes.py`, `docs/ssh.md`, simplified remote project flow), **token tracker** server log + `by_source` UI + CSV `source`/`source_id`, **chat** + **cron** token recording, **`claude-code`** inference row + catalog (`auto` + Hermes anthropic list), **Copilot ACP** relabelled, **`tts_backend`** in client-config. Phase **6** items (model refresh, cron UI, Piper TTS, skills create, etc.) remain underneath.

**Hermes backend proxy (300426):** Cron CRUD uses gateway **`/api/jobs`** (bundled **`api_server`** accepts **`schedule_tz`** and **`workdir`** on create/PATCH; larger **`prompt`** cap for composed instructions). Optional **`HERMES_DASHBOARD_URL`** + **`HERMES_DASHBOARD_SESSION_TOKEN`** (`window.__HERMES_SESSION_TOKEN__` from `hermes dashboard`) for dashboard **`/api/gateway/restart`**, **`/api/skills`**, **`/api/skills/toggle`**, **`/api/analytics/usage`**, and model mirror **`PUT /api/config`** after **`/api/setup/sync-hermes-model`**. Settings → **Messaging** drives gateway platform setup in-app (**`POST /api/messaging/platform/{id}`** → **`~/.hermes/.env`** + **`config.yaml`**); restart gateway to reload env. Gateway restart tries dashboard → **`hermes gateway restart`** → systemd/env.

## Active goal

Ship ANIMUS v1.0.0 for Gumroad per `project_goal.md` once smoke + Docker are verified on a real host.

## Current priorities

1. Human run **Phase 3 smoke** (Task 7) using `scripts/phase3-smoke-checklist.md` with clean data dir + gateway.
2. Run **Docker** build/up/curl on a machine with Docker installed (Task 8).

## Recently completed work

- **Plan saved-draft row stamp:** **`planDraftStampLabel`** now **`HHMM MMDDYY`** (was day-first). **`sw.js`** **`animus-v25`** + **`CHAT_SERVER_REV`** bump.
- **Plan tab — stop while clarifying:** Full-screen clarification modal covered the toolbar **Stop**; modal footer now includes **Stop pipeline** (same **`requestPlanPipelineStop()`** as **`#planStopBtn`**). **`sw.js`** **`animus-v24`** + **`CHAT_SERVER_REV`** bump.
- **Settings persistence / PWA sync:** **`animus_ui_settings`** in **`config.json`** + **`GET/POST`** **`ui_settings`**; PWA and desktop share the same ANIMUS host prefs via debounced save + visibility refetch. **`sw.js`** **`animus-v22`** + **`CHAT_SERVER_REV`** bump.
- **Cron job rows:** Actions are **icon-only** (pencil, runner, pause vs play by state, minus delete, document logs last); **Scheduled Jobs** add control is purple bold **+** only (same **`.add-project-btn`** pattern as Projects). **`sw.js`** **`animus-v21`** + **`CHAT_SERVER_REV`** bump.
- **Help tab icon:** Rail SVGs use **`overflow: visible`**; Help glyph uses **Feather-style** circle **`r="9"`** + **`stroke-linecap/linejoin: round`** (no clipped **?**). **`sw.js`** **`animus-v20`** + **`CHAT_SERVER_REV`** bump.
- **Projects sidebar:** **Add project** **+** is a **bold accent-colored glyph** (no filled chip); **Projects** list **starts collapsed** (no pref); expand persists as **`'0'`** in **`hermes_sidebar_projects_collapsed_v1`**. **`sw.js`** **`animus-v19`** + **`CHAT_SERVER_REV`** bump.
- **Projects list:** Drag project rows (not the gear) to reorder; **⋮⋮** is a visual grip; order persists via **`projects.json`** (server merge preserves POST order); **`pullProjectsFromServer()`** on tab visibility + bfcache **`pageshow`** so PWA/desktop stay aligned. **`sw.js`** **`animus-v17`** + **`CHAT_SERVER_REV`**. Settings **Screen wake:** group shows title + **ⓘ** + toggle only (no duplicate label under the title).
- **Chat UI branding (corrected):** Sidebar **ANIMUS** row ghost **2×** (**`.brand-ghost--sidebar`**); main **`.header`** has **no** ghost (title only beside New chat); empty-state ghost stays **2×**. **`sw.js`** **`animus-v16`** + **`CHAT_SERVER_REV`** bump.
- **Default General project:** With **`projects_dir`** set, server ensures **`<dir>/general`** + **`projects.json`** registration; client opens that project once per browser session (`sessionStorage`). Wizard step 5 copy notes the folder.
- **Settings ↔ Hermes model:** `GET /api/setup/provider-status` includes Hermes `config.yaml` `model.provider` / `model.default` plus `hermes_active_animus_id` (slug maps **gemini→google**, **togetherai→together**; **claude-code→anthropic** for sync). `POST /api/setup/sync-hermes-model` updates Hermes via `_update_config_for_provider` + `_save_model_choice` for API keys, Codex, **cursor-agent**, **claude-code**, **copilot-acp** (with CLI/auth checks), plus URL fallbacks for mistral/groq/togetherai/cohere. Inference matrix + chat picker call sync when bound.
- **SSH password test fix:** **`ssh_routes._run_ssh_probe`** no longer forces **`BatchMode=yes`** for password auth (OpenSSH skips password login in batch mode); adds **`PubkeyAuthentication=no`** + **`PreferredAuthentications=password,keyboard-interactive`**; **`CHAT_SERVER_REV`** bump. **`docs/ssh.md`** + **`repo_map.md`**.
- **Buyer install — sshpass:** **`installer/ensure-sshpass.sh`** (prompted from **`install.sh`**) installs **`sshpass`** on Linux/macOS when missing so Settings → SSH Hosts password **Test** works; Docker image includes **`sshpass`**; **`INSTALL.md`**, **`START_HERE.txt`**, **`docs/ssh.md`**, **`animus.env.example`** (`SKIP_ANIMUS_SSHPASS`), **`preflight.sh`** note, **`build-release.sh`** checklist.
- **Chat UI:** Assistant reply footer (provider · model) now shows for every inference backend, not only Codex Auto (`index.html`: `buildAssistantInferenceLabel`, `inferenceFooterFromStoredMeta`).
- **Settings Codex:** Inference matrix uses delegated Sign in / Re-check + inline **`.inf-codex-status`** so sign-in feedback is visible and the button does not stay disabled after errors.
- **Chat model vs matrix:** **`effectiveChatModelId`** prefers **`inference_models`** over legacy **`animus_selected_model`** so footer/API match the Settings inference row; Active toggle syncs both.
- **Codex sign-in:** Hermes **`codex_device_oauth`** module shared with dashboard; ANIMUS wizard routes + PWA open browser verification URL (no subprocess `hermes auth add`).
- **Buyer hardening v1.0.6:** **`HERMES_API_KEY`** auto-filled from **`~/.hermes/.env`** **`API_SERVER_KEY`** at runtime (**`hermes_runner.gateway_api_bearer`**) and at install (**`installer/merge-hermes-gateway-auth.py`**); startup **`GET /v1/models`** probe + **`/api/version`** / **`/api/hermes-chat-meta`** fields **`gateway_bearer_source`**, **`gateway_openai_models_http`**, **`gateway_openai_models_ok`**; **`START_HERE.txt`** / **`INSTALL.md`** / **`systemd/animus.service`** clarify **`systemctl --user`**; **`CHAT_SERVER_REV`** bumped.
- **Release zip v1.0.5:** **`VERSION`** **1.0.5**; **`./build-release.sh`** → **`animus-v1.0.5.zip`**; **`animus-chat/sync-from-release-zip.sh`** patches **`animus-chat/`** when **`installer/`** is missing (partial tree); **`installer/sync-animus-chat-from-zip.sh`** is a wrapper. **`build-release.sh`** still rejects the obsolete chat gate string in **`server.py`**. **`GET /api/version`** fingerprint unchanged in purpose.
- **`seller-private/`:** repo-root folder for local seller secrets (e.g. Vercel **`ADMIN_TOKEN`**); gitignored except **`README.md`**; excluded from **`build-release.sh`** zip + leak check. See **`seller-private/README.md`** and **`docs/GUMROAD.md`**.
- **Seller release UX:** sibling **`animus-site`**: **`seller-publish.html`** (root static; **`/admin/release.html`** 308 → same) + **`js/release-admin.js`** + **`api/release_upload.js`** (Vercel Blob + HMAC challenge); **`docs.html`** links sellers. **`scripts/release-and-publish.sh`** in **`animus/`** copies zip to **`animus-site/releases/`** and runs **`vercel --prod`**. Docs: **`animus-site/README.md`**, **`releases/README.md`**, **`docs/GUMROAD.md`**. **`animus.env`:** **`preflight.sh`** copies example when missing; Docker **`Dockerfile`** bakes **`/app/animus.env`** from example.
- **Fresh install skills:** `animus-chat/server.py` runs `tools.skills_sync.sync_skills()` once at import so `HERMES_HOME/skills` is seeded from bundled `hermes-agent/skills/` (Hermes CLI did this only when `hermes` ran; ANIMUS-only starts skipped it → empty `/api/skills/list`). **`skills_routes`** repeats **`sync_skills`** on list + **Update All** when manifest is missing **or** manifest is **empty** with no `SKILL.md` on disk but bundled skills exist; wizard step 4 shows list API errors when the list response is not an array.
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
- **Ghost branding + PWA:** **`ghostonlyicon.png`** for sidebar + chat header, empty state, favicon, **`manifest.json`** icons, apple-touch, About + notifications; **`animus-v8`** SW cache; desktop launcher prefers this file for `Icon=`.
- **Desktop launcher:** `installer/create-desktop-launcher.sh` + hook from `install.sh`; `GET /api/animus/desktop-launcher` (+ `?fmt=webloc`); wizard one-time download on desktop after **Open ANIMUS** (phones unchanged for PWA). See `INSTALL.md`.
- **Sidebar UX:** Icon tabs for Chats / Skills / Cron / Plan / **Tokens** (usage + CSV) / Settings / **Help** (`?`). Settings use compact **grouped** blocks + **ⓘ** `title` tooltips; browser notifications and per-provider **Active** inference use toggle rows. **Check updates** → `POST /api/animus/check-updates` with manifest from **`ANIMUS_UPDATE_URL`** or default **`https://animusai.vercel.app/api/latest.json`**, then `confirm`/`alert` for apply + restart. Notification sidebar: per-thread unread + accent; badge + wake toggles unchanged in behavior.
- **TTS defaults:** Piper + **`en_GB-alan-medium`** when unset (localStorage + `config.json` without `tts_backend`); HF/install bundle downloads GB Alan first.
- **SSH Settings modal:** Add/edit host dialog — auth radio layout fixed (`#sshFormAuthRadios`); IdentitiesOnly and relax strict host key options use toggle-style rows (same ids for API payloads).
- Phase 3 code: `cron_routes.py` logs, `skills_routes.py` capabilities + detail/readme + updates shape, `server.py` client-config + `chat_data_dir` import, `hermes_runner.chat_data_dir`, `wizard_routes` paths, `app/index.html` skills UX + wake lock + wizard wake + token CSV/SSE, `docs/hermes-agent-patches.md` expansion, `INSTALL.md` Docker, `build-release.sh` patch count, smoke checklist script.
- Docs: `project_goal.md` Phase 3 Task 7 smoke setup/teardown uses **`CHAT_DATA_DIR`** + **`.venv/bin/python` / `python3`**; Phase 2 Docker acceptance + Phase 3 Task 8 curls use **`curl -sS` … `| python3 -m json.tool`**; Phase 4 Step 1 API-key reminder; Phase 4 Step 3 token stream check uses **`python3`** (not `grep`-only); wake lock acceptance text uses **`chat_data_dir()`** / `config.json`.

## In-progress work

- **Phase 3 smoke** in progress on host (Step 2 logged **PASS**); remaining steps + Docker curl evidence.
- **Owner re-check** after Phase 6: Settings model refresh, Cursor model row + Auto, cron dropdown + timezone persistence, create skill, read-aloud Piper (if installed), add-project goal copy — per `project_goal.md` Phase 6 table when present.

## Known issues

- **Gateway API key:** Chat and Help proxy omit `Authorization` when **`HERMES_API_KEY`** is unset (matches Hermes gateway “no key → allow local”). If the gateway is configured with a key, set **`HERMES_API_KEY`** in **`animus.env`** to the same value and restart the chat service.
- **Smoke test & Docker** not executed in the agent sandbox (no Docker; no live gateway/API key). Checklist and INSTALL commands are ready for the operator.
- **Token tracker:** PWA treats Hermes/OpenAI **explicit zero** `usage` objects as real (not `null`) so `msg.usage` matches the server JSONL; Tokens tab shows a **recent server log** when the 30-day chart is empty but rows exist (e.g. “Ready.” with 0 reported tokens). Gateway `_run_agent` maps streamed finish `usage` from `run_conversation` result totals. **OpenAI Codex:** `run_agent._run_codex_stream` merges **`usage`** from terminal Responses SSE events when `get_final_response()` omits it (fixes all-zero rows when the API did report usage). Chat SSE tail flush + server `_sse_last_usage_and_model` unchanged. Plan/skills still use `POST /api/tokens/record`; cron rows may stay null until the gateway exposes per-job usage.
- **Release zip:** v1.0 cap **≤55MB** — `build-release.sh` **fails** if over cap; trims omit Ghost3D, `hermes-agent/tests`, `hermes-agent/website`, WhatsApp bridge `node_modules` (see INSTALL).
- **Hermes / agent updates:** Wizard step 1 only reports reachability (no `hermes --version` dump). ANIMUS **does not** schedule background `hermes update`; monorepo file updates ship via **manifest + zip** in-app update or manual reinstall — see `docs/hermes-agent-patches.md`.

## Blockers

- None for code merge; **release** blocked on successful smoke + Docker on a real host.

## Validation status

- Run: `cd animus-chat && .venv/bin/python -c "import server"`
- Run: `./build-release.sh` from repo root
- Optional: `docker compose -f docker/docker-compose.yml build` (requires Docker)

## Last validation run

- `PYTHONPATH=hermes-agent` pytest: **`tests/cron/test_hermes_chat_delivery.py`** + **`tests/agent/test_project_workspace.py`** — **pass** (20 tests; run in a throwaway venv with pytest, not committed).
- **`hermes project --help`** — **pass** (subcommands listed after `main.py` wiring).
- **`hermes-gateway.service`** (user): **`scripts/sync-dev-systemd.sh`** + monorepo **`/home/sketch/animus/hermes-agent`** (**`venv`**, **`CHAT_DATA_DIR=/home/sketch/animus/animus-chat/data`**, **`HERMES_HOME=…/profiles/default`**). **`systemctl --user restart hermes-gateway.service`** — **active** (2026-04-30). No **`animus-fresh-install`** path in the unit — single repo only.
- **`systemctl --user restart animus.service`** + **`curl /api/version`** + isolated cron-delivery spot-check — **pass** (2026-04-30).
- `hermes update` (atlas `animus-fresh-install/animus-chat`): stash restore **conflicted** → **clean upstream tree**; stash ref preserved — **reapply + resolve** before assuming ANIMUS agent patches are present (see `project_knowledge.md`).
- `cd animus-chat && .venv/bin/python -c "import server"` — **pass** (2026-04-30 monorepo).
- `./build-release.sh` — **pass** (2026-04-30 monorepo; zip + greps; **6** `## Patch` sections in `hermes-agent-patches.md`).
- `cd animus-chat && .venv/bin/python -c "import server"` — **pass** (2026-04-30 api_version fingerprint + sync installer).
- `./build-release.sh` — **pass** (2026-04-30 v1.0.4 zip + gate-string regression check).
- `cd animus-chat && python3 -c "import server"` — **pass** (2026-04-30 Settings tabs + default update manifest URL).
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
| About + Check updates in Settings inference group | **PASS (static)** | `aboutAnimusBtn` + `checkAnimusUpdatesBtn` in `.settings-btn-row` (`index.html`). |
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
