# Project knowledge (animus)

Durable lessons for future agents. Not a backlog or duplicate of `project_history.md`.

---

## Release zip (290426)

- **`build-release.sh`** excludes **`animus-chat/animus.env`** (root `animus.env` was already excluded), **`hermes-agent/.env`**, **`hermes-agent/.envrc`**, **`*.flock`**, **`./animus-update-server/*`**, and **repo-root `./scripts/*`** only (not **`hermes-agent/.../scripts/`**). After zipping, the script **fails** if the archive lists a raw `animus.env`, raw `hermes-chat.env`, raw **`hermes-agent/.env`**, **`*.flock`**, **`animus-chat/data/`**, or any path **`animus-update-server/`**. `.gitignore` lists **`animus-chat/animus.env`** and **`hermes-agent/.env`** so they are less likely to be committed.
- **`animus-site/`** (sibling repo, not in buyer zip): Vercel **`vercel.json` `version`: 2** uses **`builds`**: **`@vercel/static`** (HTML + **`css/**`**, **`js/**`**, **`assets/**`** so CSS is not dropped) + **`@vercel/python`** for **`api/*.py`**; **`routes`** map **`/api/latest.json`**, **`/updates/latest.json`**, **`/api/admin/*`**, **`/api/history`**. No **`runtime.txt`** (Vercel used Python **3.12** in build logs). **Upstash Redis:** Vercel often sets **`REDIS_URL`** only — wire password **≠** REST token; **`lib_redis.py`** uses **`redis`** TCP (**`Redis.from_url`**) for **`REDIS_URL`**. If **`UPSTASH_REDIS_REST_URL`** + **`UPSTASH_REDIS_REST_TOKEN`** (or **`KV_REST_API_*`**) exist, **`upstash_redis`** REST is used instead. **`/api/latest`** uses short CDN **`Cache-Control`** so manifests are not stuck at **`0.0.0`**. Set **`ANIMUS_UPDATE_URL`** in **`animus.env.example`** to **`https://<project>.vercel.app/api/latest.json`** after deploy.
- **animus-site design source of truth (290426):** Use **`animus-chat/app/index.html`** and **`docs/animus-user-guide.md`** for marketing claims; the actual product surfaces are Chats / Skills / Cron / Plan / Settings, first-run wizard, provider matrix, Projects, SSH/Slack, token usage, Piper/browser TTS, Tailscale PWA, and manifest zip updates. Preview art lives in **`/home/sketch/animus-site/assets/screenshots/{chat,wizard,settings,cron}.svg`** and should stay aligned with those real surfaces rather than generic placeholders.
- **animus-site release notes (290426):** Keep **`updates.html`** with static fallback release content so buyers never see permanent **Loading...** if browser fetches fail; live API enhancement lives in external **`js/updates.js`** (external scripts were confirmed to run where the inline release fetch could leave the DOM unchanged). Validate with `curl -L https://animusai.vercel.app/updates.html | rg "Loading|v1.0.0"` and Chromium `--dump-dom`.
- **Publish buyer updates (290426):** After **`./build-release.sh`**, copy the zip into **`animus-site/releases/`** and **`vercel --prod`**. Publish with **`./scripts/publish-animus-manifest.sh`** (after **`vercel env pull .env.production.local --environment production`** + **`set -a && source …`**). **`ADMIN_TOKEN`**: if pull leaves it empty, it was **sensitive** — use **`vercel env add ADMIN_TOKEN production --yes --no-sensitive --value '…'`** (or dashboard) and **redeploy**. **`animusai.vercel.app`** must **alias** this project’s Production (e.g. from **`animus-site/`**: **`vercel alias set animus-site-ruddy.vercel.app animusai.vercel.app`**) or **`/releases/*`** and **`POST /api/admin/publish`** can 404/403 while **`/api/latest.json`** still looks correct (shared Redis, wrong static host).

- **animus-site deploy vs hostname (290426):** Customer-facing URL is **`https://animusai.vercel.app`**. After `vercel --prod`, the CLI may only auto-alias a project URL such as **`animus-site-ruddy.vercel.app`**; explicitly run `vercel alias set <new-deployment>.vercel.app animusai.vercel.app` when needed. Quick check: `curl -L https://animusai.vercel.app/` should show **`Self-hosted AI command center`** / **`Buy the v1 bundle`**, not the older **`Your personal AI command center`** copy. **`/api/latest.json`** can still be correct while homepage HTML is stale — routes differ.
- **≤55MB cap:** the script **exits 1** if the zip exceeds **55MB**. Trims from the zip (not from your working tree): **`Ghost3D/*`**, **`hermes-agent/tests/*`**, **`hermes-agent/website/*`**, **`hermes-agent/scripts/whatsapp-bridge/node_modules/*`**, **`hermes-agent/.cursor/*`**. WhatsApp bridge: **`INSTALL.md`** → run `npm ci` in `hermes-agent/scripts/whatsapp-bridge/` when using that feature.
- **No public repo link in PWA:** About ANIMUS points to **Settings → HELP** only. **Updates:** **`ANIMUS_UPDATE_URL`** in **`animus.env`** → JSON manifest (`version`, `download_url`, `notes`); **`POST /api/animus/check-updates`** / **`apply-update`** use **httpx** (no git). Seller runs separate **`animus-update-server`** (FastAPI) to serve **`/latest.json`** and **`POST /admin/publish`**; bake the real manifest URL into **`animus.env.example`** before **`./build-release.sh`**. Zip extract uses a **zip-slip** path check in **`server.py`**.
- **Buyer zip:** omits **ANIMUS internal continuity** (`project_*.md`, `repo_map.md`, `AGENTS.md`, `CLAUDE.md`, `.cursorrules`, `.cursor/`, `setup_repo.md`, `animus-chat/repo_map.md`, `animus-chat/project_history.md`, `animus-chat/setup_repo.md`) and **`hermes-agent/AGENTS.md`** + **`hermes-agent/.cursor/`**. **Clone the repo** for continuity files; the UI still refers to per-project **`project_goal.md`** files on disk, not the monorepo north-star file.

## Gumroad zip (290426)

- **Buyers:** point to root **`START_HERE.txt`** then **`INSTALL.md`**. Release artifact remains **`./build-release.sh`** → `animus-v$(cat VERSION | tr -d '[:space:]').zip`.
- **Sellers:** **`docs/GUMROAD.md`** — pre-upload checklist, suggested bullets, thank-you email snippet.
- **Gumroad ≠ auto-push:** Uploading a new product file does **not** download to buyers’ disks; they re-download from Library / receipt link; seller email helps.

## First-run wizard (290426)

- **`/api/setup/status`** and **`GET /api/animus/client-config`** use **`cfg_still_first_run()`** in `setup_wizard/wizard_routes.py` so `"false"` / `0` in `config.json` do not keep re-opening the wizard.
- **`POST /api/setup/complete`** sets `first_run: false` plus **`setup_completed_at`** (UTC). The PWA also calls complete when the **final wizard summary** is shown so refresh before “Open ANIMUS” does not loop the wizard.

## Skills list empty on fresh ANIMUS (290426)

- **`GET /api/skills/list`** uses in-process **`tools.skills_tool._find_all_skills`**, which scans **`HERMES_HOME/skills`** (and `config.yaml` **`skills.external_dirs`** only). Bundled catalog lives under **`hermes-agent/skills/`** until **`tools.skills_sync.sync_skills()`** copies them into **`HERMES_HOME/skills`**.
- The **Hermes CLI** runs **`sync_skills(quiet=True)`** on every **`hermes`** launch (`hermes_cli/main.py`). **ANIMUS** is often started only via **`animus-chat/server.py`**, so new profiles stayed empty until **`server.py`** was taught to call **`sync_skills`** once at import (after **`HERMES_AGENT`** is on **`sys.path`**).

## Chat UI assets (290426)

- **`ghostonlyicon.png`:** Served as **`/ghostonlyicon.png`** from `animus-chat/app/`. Used for empty chat, sidebar + main header brand, favicon, `manifest.json` icons, apple-touch-icon, About modal, notification icon/badge, and Linux `.desktop` icon preference (`server.py` desktop launcher + `installer/create-desktop-launcher.sh` try this file before `icon-192.png`). Service worker cache key **`animus-v2`** (was `animus-v1`) so installs pick up icon changes.

## Conventions

- **Session start:** Read `AGENTS.md` then `project_goal.md`, `project_status.md`, `project_history.md`, this file, and `repo_map.md` before code edits.
- **Session end:** Append `project_history.md`; update this file with new lessons or a no-new-knowledge note; refresh `project_status.md` / `repo_map.md` when state or layout changes.

---

## Stack and validation

- **Python venv:** `cd animus-chat && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt` then `.venv/bin/python -c "import server"`.
- **Release:** `./build-release.sh` (requires `rg`; scans `animus-chat`, `hermes-agent`, `installer`, `docker`, `systemd` only — root `project_goal.md` may still mention example paths). Phase 2 greps **`animus-chat/app/index.html`** (not `static/index.html`) for legacy API paths and checks `server.py` subprocess lines are tagged `# exempt:`.
- **Default port:** `CHAT_PORT` / `PORT` default **3001** in `server.py`; live Hermes on 3000 stays untouched.

---

## 290426 — Initial repo

- Repository was empty before continuity docs; there is no `package.json` / `Cargo.toml` / etc. until added.

## Bootstrap (`setup_repo.md`)

- **`setup_repo.md`** holds full steps and Appendix A (complete `AGENTS.md` body with `[repo]` placeholder) so another repo can mirror this structure. Policy edits should stay in sync across `AGENTS.md`, `.cursorrules`, `CLAUDE.md`, and `.cursor/rules/operating_rules.md` (use `cmp` to verify).

## Desktop launcher (290426)

- **`installer/create-desktop-launcher.sh`:** Linux GUI → `~/.local/share/applications/animus.desktop` + Desktop copy (`xdg-open` URL from `HERMES_CHAT_PUBLIC_URL` or `http://CHAT_HOST:CHAT_PORT/`). macOS → `~/Desktop/ANIMUS.webloc`. Skips Docker (`/.dockerenv`), `CI`/`GITHUB_ACTIONS`, `SKIP_ANIMUS_DESKTOP_LAUNCHER=1`, non-Linux/Darwin, Linux without `DISPLAY`/`WAYLAND_DISPLAY`.
- **Wizard:** `wizPhoneLike()` gates the optional download; `localStorage.animus_desktop_launcher_offered_v1` prevents repeats.
- **API:** `GET /api/animus/desktop-launcher` uses `HERMES_CHAT_PUBLIC_URL` when set, else `X-Forwarded-*` / `Host` / `127.0.0.1:CHAT_PORT`.

## Token and navigation (290426)

- **`repo_map.md` first:** Small tree here—open listed paths only; when code lands, keep the map current so agents avoid whole-repo walks.
- **`project_history.md`:** Append new entries at EOF; do not load the full log just to add a line. Skim recent entries for context.
- **Mirrors:** After editing `AGENTS.md`, run `cmp` copies: `cp AGENTS.md .cursorrules CLAUDE.md .cursor/rules/operating_rules.md` (adjust paths); one source of truth.
- **`setup_repo.md`:** Appendix A must stay aligned with `AGENTS.md` (same policy body; `[repo]` vs real name is the only intentional difference).

---

## 290426 — ANIMUS bootstrap

- **`hermes skills` not `hermes skill`:** route modules call `hermes skills …` per current CLI.
- **`build-release.sh` password grep:** use word boundary (`\b5206\b`) so `uv.lock` numeric hashes do not false-positive.
- **Skills enable/disable (Option C):** `POST /api/skills/enable|disable/{id}` returns **200** with `{ ok: false, error: "…hermes skills config…" }`; UI hides toggles. Do not reintroduce 501 for these routes.

## 290426 — Phase 2 UI / wizard

- **Primary UI file:** `animus-chat/app/index.html` (single-file PWA). Wizard + tooltips live here; acceptance greps target this path.
- **Cron manual run:** UI uses `POST /api/cron/run/{id}` (alias of trigger). List uses `GET /api/cron/list`.

## 290426 — Settings HELP row (`index.html`)

- **Token usage → HELP:** Divider `<hr>` between **Open token usage tracker** and **HELP**; HELP is **centered** in the settings column (`display:flex; justify-content:center`); no caption span beside the button.

## 290426 — HELP bot (`help_routes.py` + `docs/animus-user-guide.md`)

- **`GET /api/help/guide`** — returns **`topics_markdown`** (guide with FAQ block removed), **`faq_markdown`** (body under `## Frequently asked questions`), **`topics`** `[{id,title}]` (slug ids aligned to `##` order in `topics_markdown`), plus **`markdown`** / **`full_markdown`** for backward compatibility. Help center UI: Home, Topics (nav + article), FAQ, Ask tabs.
- **`POST /api/help/ask`** — body: `question`, `model`, `hermes_provider`, optional `hermes_base_url`; non-streaming gateway completion with strict system prompt + full guide in user message; tokens logged with **`source: "help"`**. OpenAI Codex **`auto`** is rewritten to **`gpt-5.2-codex`** for this path only.
- **UI:** Settings → **HELP** opens modal; **Ask ANIMUS** uses `effectiveChatModelId()` + `chatBackendPayload()` (same active model as chat). Reusable pattern for other surfaces later.

## 290426 — Project notification unread (`index.html`)

- Per-thread read watermarks: **`hermes_notif_conv_read_counts_v1`** (`convId` → last-read message count). Replaces legacy project-aggregate **`hermes_notif_read_msg_counts_v1`** badge math.
- Unread notification rows: class **`notif-item-unread`** (accent background, white text). Opening a thread or expanding the Notifications section marks read.

## 290426 — Settings SSH host modal (`index.html`)

- **Auth radios:** `.field input{width:100%}` stretches `<input type="radio">`. Fix with a wrapper id (e.g. `#sshFormAuthRadios`) and scoped overrides like `#ttsBackendRadios` (width auto, label `display:flex`, option text in `<span>`).
- **Toggles:** Keep the same checkbox ids (`sshFormIdentitiesOnly`, `sshFormStrictOff`) for save/test JSON; style as switches with a row `<label class="ssh-toggle-row">` so the label text is clickable. Place toggle blocks outside a `.field` wrapper if checkboxes would inherit `.field input{width:100%}`.

## 290426 — Phase 3 alignment

- **`chat_data_dir()`** in `hermes_runner.py` matches `server.DATA_DIR` (CHAT_DATA_DIR / ~/.hermes/.env / default `~/.hermes/chat`). Wizard `config.json` + model cache use it — avoids wizard living in `./data` while chats live under `~/.hermes/chat`.
- **Wake lock:** persisted via `GET/POST /api/animus/client-config` and wizard `save-config` `wake_lock`; client loads on init after wizard.
- **Skills toggles:** `GET /api/skills/capabilities` drives `#skills-container[data-enable-toggle]`; CSS hides `.skill-enable-toggle` when false.
- **Smoke doc:** `scripts/phase3-smoke-checklist.md` — run on a host with Docker + gateway; update `project_status.md` table with results.
- **Smoke setup:** there is often **no** `animus-chat/data/`; wizard + chats use **`chat_data_dir()`** (`CHAT_DATA_DIR` → `~/.hermes/.env` → `~/.hermes/chat`). Use `CHAT_DATA_DIR=/tmp/...` for a clean wizard without touching your real `~/.hermes/chat`.
- **Support / “where did my data go?”** Ask which resolution step applies: `CHAT_DATA_DIR` env, `HERMES_CHAT_DATA_DIR`, keys in `~/.hermes/.env`, or default `~/.hermes/chat`. **`CHAT_DATA_DIR`** is the clean escape hatch for smoke tests and for users who want a dedicated folder.
- **Docs / examples:** Prefer **`python3`** or **`animus-chat/.venv/bin/python`** in shell snippets — `python` alone is often missing on Debian/Ubuntu.

## Hermes Agent bundle vs upstream

- **Smoke Step 2 (host):** bundled **v0.11.0 (2026.4.23)**, Python 3.11.15; upstream was **778 commits ahead** at that check — not a v1.0 blocker (shipped snapshot is intentional).
- **Operators:** Do **not** run **`hermes update`** inside ANIMUS expecting to keep patch alignment; see top of **`docs/hermes-agent-patches.md`**.
- **v1.1+:** Rebasing ANIMUS patches onto newer upstream Hermes Agent is a scheduled merge/re-test effort; the patch audit doc is the merge checklist.

## 290426 — Phase 7 (Slack/SSH, token audit, Claude Code, PWA paths)

- **`build-release.sh`:** Phase 7 greps — `SLACK_WEBHOOK_URL` in `animus.env.example`, `api/ssh/hosts` + `"source"` strings in `server.py` (module docstring), no `Browse` / “not available in the PWA” in `app/index.html`.
- **Token usage:** `animus-chat/token_usage.py` + `GET /api/tokens/usage?days=&source=`; chat route appends on SSE completion; cron `trigger` logs `source=cron`. UI merges local conv `usage` with server JSONL.
- **Slack / SSH:** `integrations_slack.py` and `ssh_routes.py` mounted from `server.py`; Settings panels open modals; Slack save merges keys into repo-root `animus.env` (preserve other lines).
- **Claude Code:** UI `claude-code` preset + matrix row; catalog from `_claude_code_catalog_rows()` (Hermes `_PROVIDER_MODELS["anthropic"]` + `auto`). Wizard `provider-status` probes `agent.anthropic_adapter` for Claude Code OAuth.
- **Remote projects:** local path auto `/<projects_sync_root>/_ssh_mounts/<alias><remote_abs_path>`; user must still `sshfs` if they want `fs/validate` to pass before mount exists.

## 290426 — Plan tab + manual token usage

- **`POST /api/tokens/record`** (`token_usage.py`): append-only JSONL; body uses **`provider`**, **`model`**, **`input_tokens`**, **`output_tokens`**, **`source`**, **`source_id`**.
- **Plan:** `planHermesChat` parses non-stream chat JSON and returns **`usage`** when present; **`planRunStage`** calls **`recordTokenUsageManualIfPresent`** with **`source: plan`** and **`source_id`** = pipeline stage id. Frontend skips the POST when **`usage`** lacks finite **`prompt_tokens`** / **`completion_tokens`** (avoids null-only client rows).
- **Skills UI:** same helper after successful install/create/update/toggle/wizard **update-all** when response JSON includes **`usage`** (currently unused until an API adds it).

## Settings form CSS gotcha

- **`.field input { width:100% }`** applies to **radio** inputs unless overridden (see **`.chat-backend-field`** and **`#ttsBackendRadios input[type="radio"]`**). Without that, radios stretch full width and label text collapses to a narrow column.

## 290426 — Splash / startup image

- First-paint splash in **`animus-chat/app/index.html`** (`#splash-screen`) uses **`/ANIMUSLOGO.png`** from **`animus-chat/app/ANIMUSLOGO.png`** (keep in sync with repo-root **`ANIMUSLOGO.png`** when the brand asset changes).
- Setup wizard step 0 (Welcome) uses **`/ANIMUSLOGOICON.png`** from **`animus-chat/app/ANIMUSLOGOICON.png`** (sync from repo-root **`ANIMUSLOGOICON.png`** when the icon changes).

## Hermes upstream drift vs ANIMUS

- **`hermes --version`** may print “commits behind — run `hermes update`”. That is Hermes CLI behaviour, not ANIMUS auto-updating the tree.
- **Do not** add a server or UI feature that periodically runs **`hermes update`** against the ANIMUS-bundled `hermes-agent/` without a controlled rebase + full acceptance test — **`docs/hermes-agent-patches.md`** (banner) forbids it; it can remove Cursor/skills/cron/chat alignment patches.
- **Wizard step 1** is titled **Agent check**: only shows reachable vs failed (no full `hermes --version` dump in the UI); `/api/setup/hermes-check` still returns `version` for debugging if needed later.

## 290426 — Phase 6 (models, cron, skills create, Piper TTS)

- **`POST /api/models/refresh`:** Rebuilds local `hermes_models_cache.json` from bundled Hermes `_PROVIDER_MODELS` + **`list_cursor_cli_models()`** when `cursor whoami` succeeds — **no `HERMES_API_KEY`**. `GET /api/models` without `?gateway=1` serves this list for the UI.
- **Cron UI:** `populateCronProjectDropdown()` → `GET /api/projects/list-simple`; timezone suggestions → **`GET /api/system/timezones`** (async `fillCronTimezoneDatalist`); saving a job persists **`cron_timezone`** via `POST /api/animus/client-config`.
- **Piper:** `animus-chat/tts_routes.py` — optional `piper` on PATH or **`PIPER_BIN`**; voices from **`PIPER_VOICES_DIR`** or `~/.local/share/piper`, `~/.piper/voices`, etc. Operator doc: **`docs/tts.md`**.
- **Piper default voices:** **`tts_routes.py`** auto-downloads six models (~380 MB), **first** `en_GB-alan-medium` (product default for Read aloud + Settings), same order as **`installer/fetch-piper-voices.sh`**, when **`piper`** is on PATH/`PIPER_BIN` but no `.onnx` files exist. API **`fetching`** + UI poll; **`SKIP_ANIMUS_PIPER_VOICES=1`** disables.
- **TTS defaults:** `GET /api/animus/client-config` uses **`tts_backend` `piper`** when the key is absent (`server.py`); client **`DEFAULT_PIPER_VOICE_ID`** in `app/index.html` matches **`en_GB-alan-medium`**. UI still falls back to browser if Piper is not installed.
- **Skills create:** `POST /api/skills/create` writes `SKILL.md` under `~/.hermes/skills/<name>/` (validated id pattern).

## 290426 — Phase 5 (wizard + settings + updates)

- **Wizard flow:** Step order is 0 Welcome → 1 **Agent check** (Hermes CLI reachable; no `hermes --version` wall in UI) → 2 provider checklist + inline auth (no standalone Cursor step) → 3 default model (uses `wizard_ready_providers` / `wizard_selected_providers` from `GET /api/animus/client-config` to filter; refresh models after Cursor when needed) → 4 skills manager (`/api/skills/list` + enable/disable when capabilities allow) → 5 projects folder (`GET /api/setup/check-path`, saves `projects_dir`) → 6 Tailscale (`GET /api/setup/tailscale-check`) + wake lock only when Tailscale enabled → 7 Done (no wake checkbox).
- **Settings inference:** `GET /api/setup/provider-status` drives the matrix; `POST /api/setup/test-key` + `save-config` keys update env; Codex: `POST /api/setup/codex-auth-start` spawns background `hermes auth add openai-codex` and returns `poll_id` — UI polls `GET /api/setup/codex-auth-status/{poll_id}` every 3s (180s client timeout); session probe is `GET /api/setup/codex-auth-session`. Cursor: `POST /api/setup/cursor-login-start` + re-check.
- **Updates (Phase 8):** `POST /api/animus/check-updates` / `apply-update` read **`ANIMUS_UPDATE_URL`**, compare manifest **`version`** to repo **`VERSION`**, download **`download_url`** zip, **`extractall`** with path validation. **`installer/install.sh`** does not touch git.
- **animus-update-server:** Run **`<that-dir>/.venv/bin/uvicorn`** (or systemd **`ExecStart`** pointing at that binary). A global **`~/.local/bin/uvicorn`** has no **fastapi** → `ModuleNotFoundError: fastapi`. **`[Errno 98]` on 9977** (default in unit): stop duplicate **`animus-updates`** / old uvicorn (see **`ss -tlnp`** / **`lsof -i :9977`**) or change **`--port`**. User unit lives in **`~/.config/systemd/user/animus-updates.service`** — **`cp`** from repo **`systemd/`** after edits. **`EnvironmentFile=-/path/.env`** makes **`.env`** optional; create **`.env`** from **`.env.example`** and set **`ADMIN_TOKEN`** for admin routes. **Tailscale:** uvicorn is **HTTP** only; TLS is at Tailscale. **`tailscale serve --https=443 /updates/ http://127.0.0.1:9977`** → buyer **`ANIMUS_UPDATE_URL`** = **`https://<machine>.ts.net/updates/latest.json`**. **`StaticFiles`:** mount **`/updates/releases`** (full path) **and** **`/releases`** (Tailscale often strips **`/updates`** on the proxied path); register mounts **after** API routes. Zips live in **`releases/zips/`**.
- **Never create a venv inside `animus-chat/`** (for agent smoke / extra envs): `build-release.sh` walks that directory and pip’s vendored files cause **sanitisation grep false positives**. Use **repo-root `.venv`** or a path **outside** `animus-chat/`. Exception: **`install.sh`** creates `animus-chat/.venv/` by design; that tree is excluded from the zip and is the supported layout for end users.
- **Release checks:** `build-release.sh` greps Plan-tab strings `Each Hermes step|Hermes step is|Hermes chat`, asserts `check-updates` in `server.py`, and `projects_dir` in `wizard_routes.py`.
- **`GET /api/version`:** includes `python` short version for About modal.

## Go-live smoke (operator)

- **Before step 1:** Open **`animus.env`** and/or **`~/.hermes/.env`** and confirm at least one **real** provider key (not placeholder / not expired). Wizard may proceed without it, but **step 3 (key test)** and **step 9 (chat)** give misleading results if the key is bad.
- **During step 9:** Watch **browser Network** (SSE) or **server stdout**. The first assistant stream chunk that includes a **`usage`** block means the **token tracker** can populate once you open it — you may see proof before opening Settings → Token tracker.
- **Screenshots (Gumroad):** Capture **during** the smoke run (wizard welcome, chat with badge, cron list) while **`CHAT_DATA_DIR`** still shows first-run UI. After teardown + return to normal data, the wizard is gone unless you reset **`config.json`** or start another throwaway **`CHAT_DATA_DIR`** session.
- **Step 16 (`./build-release.sh`):** Run **last**, from **repo root**, in a **clean shell** — **`unset CHAT_DATA_DIR`** after smoke teardown so the release build is not tied to the temp tree. The script does not need smoke data, but avoiding a stray env var avoids confusion.

## No-new-knowledge template

When a session adds nothing durable, append:

```text
DDMMYY — No new durable knowledge (routine doc-only / trivial change).
```

290426 — No new durable knowledge (animus-site copy cleanup only).
290426 — No new durable knowledge (animus-site visual brand/layout tweak only).
290426 — No new durable knowledge (animus-site Gumroad URL swap only).
