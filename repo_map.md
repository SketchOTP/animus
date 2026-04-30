# Repo map (animus)

Quick navigation for agents. Update when layout, entrypoints, or roles change.

## Repository root

| Path | Purpose |
|------|---------|
| `README.md` | Product overview and quick start |
| `START_HERE.txt` | Buyer-facing first steps after unzipping the release zip (Gumroad / direct download) |
| `docs/GUMROAD.md` | Seller checklist, suggested listing copy, post-purchase blurb for Gumroad |
| `docs/BUYER_UPDATES.md` | Buyer guide: manifest-based in-app updates + Gumroad re-download |
| `INSTALL.md` | Manual install, systemd, troubleshooting |
| `VERSION` | Semver exposed via `GET /api/version` |
| `animus.env.example` | Environment template; **`install.sh`** / **`preflight.sh`** copy to **`animus.env`** when missing; **`HERMES_HOME`** must be an **absolute** path when using systemd **`EnvironmentFile`** (not `${HOME}`) |
| `seller-private/` | **Seller-only:** local secrets (e.g. Vercel **`ADMIN_TOKEN`**); **gitignored** except **`README.md`**; **excluded** from **`build-release.sh`** zip + leak check |
| `Ghost3D/` | Optional GLB assets (not loaded by the PWA today); **excluded from release zip** |
| `build-release.sh` | Sanitisation checks + release zip (**≤55MB** hard cap) + ship trims (size + **internal dev**: `project_*.md`, `repo_map.md`, `AGENTS.md`, `CLAUDE.md`, `.cursorrules`, `.cursor/`, `setup_repo.md`, `animus-chat/{repo_map,project_history,setup_repo}.md`, `hermes-agent/AGENTS.md`, `Ghost3D/`, agent `tests/` / `website/` / WhatsApp `node_modules` / `hermes-agent/.cursor/`, **`hermes-agent/.env`**, **`hermes-agent/.envrc`**, **`*.flock`**, **`animus-update-server/`**, **repo-root `scripts/`**) + post-zip **leak check** (no raw env, lock files, runtime data, or `animus-update-server/` in zip) + `## Patch` count in `docs/hermes-agent-patches.md` |
| `scripts/phase3-smoke-checklist.md` | Phase 3 manual smoke steps + **Practical tips** (keys, SSE usage, screenshots, `build-release.sh` shell hygiene); **`scripts/`** omitted from **buyer zip** — clone repo for these |
| `scripts/publish-animus-manifest.sh` | Seller helper: `POST` JSON to **`animus-site`** **`/api/admin/publish`** (`ADMIN_TOKEN`, `DOWNLOAD_URL`, optional `ANIMUS_RELEASE_NOTES` / `ANIMUS_PUBLISH_URL`); zip must be at **`download_url`** (Blob URL or **`/releases/…`**) |
| `scripts/release-and-publish.sh` | Seller helper: copy **`animus-v$(VERSION).zip`** to sibling **`animus-site/releases/`** and run **`vercel --prod`** (optional **`ANIMUS_SITE_DIR`**) |
| `scripts/sync-dev-systemd.sh` | Dev host: install **`~/.config/systemd/user/animus.service`** + **`hermes-gateway.service`** (gateway **`WorkingDirectory`** / **`ExecStart`** = this repo’s **`hermes-agent/`** + **`venv`**, **`CHAT_DATA_DIR`** = **`animus-chat/data`**, **`HERMES_HOME`** = **`$HOME/.hermes/profiles/default`**), create/fix **`animus.env`** (absolute **`HERMES_AGENT_DIR`** / **`HERMES_HOME`**, **`INSTALL_DIR`**), **`daemon-reload`**, symlink **`scripts/animus`** → **`~/.local/bin/animus`** (`animus start|stop|restart|status`); warns if **`:3001`** busy (omit from buyer zip — **`scripts/`** excluded) |
| `scripts/animus` | Bash CLI: **`animus start`**, **`stop`**, **`restart`**, **`status`** → **`systemctl --user`** on **`animus.service`** (override with **`ANIMUS_SYSTEMD_UNIT`**) |
| `project_goal.md` | North star / build directive |
| `project_status.md` | Current snapshot |
| `project_history.md` | Session log |
| `project_knowledge.md` | Lessons and validation tips |
| `repo_map.md` | This map |
| `AGENTS.md` | Agent workflow rules |

**Sibling repo (not inside this tree):** **`animus-site/`** — Vercel deployment: product-led marketing **`index.html`** (ghost header mark, centered hero logo, app shell, real ANIMUS feature copy, pricing/FAQ), **`updates.html`** (static v1.0.0 fallback + **`js/updates.js`** API enhancer), **`docs.html`** (links sellers to **`seller-publish.html`**), **`seller-publish.html`** (Blob upload + publish UI), **`css/main.css`**, **`js/main.js`**, **`js/release-admin.js`**, **`api/release_upload.js`** (Node **`@vercel/blob`** **`handleUpload`** + HMAC challenge), PNG logos under **`assets/`**, stylized product preview SVGs under **`assets/screenshots/`**, plus **`/api/latest.json`** for **`ANIMUS_UPDATE_URL`**. **Buyer-facing hostname:** **`https://animusai.vercel.app`** only (alias after each **`vercel --prod`**). Clone/deploy separately; see **`animus-site/README.md`** next to this repo (or your fork’s layout).

## Application

| Path | Purpose |
|------|---------|
| `animus-chat/server.py` | Starlette app: on import (after ``HERMES_AGENT`` on ``sys.path``), calls ``tools.skills_sync.sync_skills()`` once so bundled ``hermes-agent/skills/`` seed into ``HERMES_HOME/skills`` (CLI did this on every ``hermes`` launch; ANIMUS-only starts left the dir empty); gateway proxy (optional **`HERMES_API_KEY`** via ``hermes_runner.gateway_upstream_headers``), workspace APIs, static PWA, **`GET /api/version`** includes **`chat_server_rev`** + **`chat_proxy_blocks_on_missing_hermes_api_key`**, `GET/POST /api/animus/client-config` (wake lock, `projects_dir`, `inference_models`, **`tts_backend`**, **`cron_timezone`**, **`cron_overseer_prompt`**, Tailscale fields, wizard provider lists ↔ `config.json`), **`GET /api/animus/desktop-launcher`**, **`POST /api/models/refresh`** (curated + gateway **`/v1/models`** merge + provider alias normalize), **`claude-code`** model rows, chat SSE token logging via `token_usage.record_token_usage`, **`POST /api/animus/check-updates`** / **`apply-update`**, `projects_sync_root()` reads `projects_dir` from config |
| `animus-chat/token_usage.py` | `record_token_usage`, `GET /api/tokens/usage` merges Hermes dashboard **`GET /api/analytics/usage`** as **`hermes_analytics`** when token set; `POST /api/tokens/record` → `token_usage.jsonl` |
| `animus-chat/integrations_slack.py` | `GET/POST /api/integrations/slack/{status,save,test}` — reads/writes repo-root `animus.env` for `SLACK_*` |
| `animus-chat/ssh_routes.py` | `GET/POST/PUT/DELETE /api/ssh/hosts`, `POST /api/ssh/test` — `ssh_hosts.json` + `SSH_PASSWORD_*` in `animus.env`; password probe uses **`BatchMode=no`**, **`PubkeyAuthentication=no`**, **`PreferredAuthentications=password,keyboard-interactive`** ( **`BatchMode=yes`** breaks **`sshpass`** ) |
| `animus-chat/help_routes.py` | **`GET /api/help/guide`** — `topics_markdown`, `faq_markdown`, `topics[]` (+ full `markdown`); **`POST /api/help/ask`** — guide-grounded Help bot (non-stream; `source: "help"` in token log) |
| `animus-chat/tts_routes.py` | `GET /api/tts/backends`, `GET /api/tts/piper/voices` (+ **`fetching`** / **`fetch_error`**), `POST /api/tts/piper/speak` (WAV); **background HF download** of default Piper voices (**first:** `en_GB-alan-medium`) when binary present and no `.onnx` models; `PIPER_VOICES_DIR` / `~/.local/share/piper` |
| `animus-chat/app/` | PWA (`index.html`): sidebar **icon tabs** Chats / Skills / Cron (**collapsible overseer**; job row **SVG icon** actions + purple **+** add; **project scope** + composed prompt; accent **prompt optimizer** + load state; **timezone `<dialog>`** picker; deliver list from messaging **`cron_deliver_home_ready`**) / Plan (**play/stop**; saved plan row **stamp + idea summary** + **✎ / ▶ / −**; clarification **modal** per-question answers + **Stop pipeline** / Submit / Cancel — **`requestPlanPipelineStop()`** shared with toolbar) / **Tokens** / **Settings** (collapsible **Notifications** + **Read aloud** + **Inference** + **Messaging**; **SSH host** modal; **Screen wake** row: title + **ⓘ** + toggle only) / **Help**; wizard, TTS, cron, **`sw.js`** **`animus-v25`**; **Projects** list **drag rows** reorder (persisted in **`projects.json`**); **`visibilitychange`** refetch **projects** + convs + **`client-config`** (**`ui_settings`** prefs sync); sidebar ANIMUS **ghost** 2×; main top bar **no** ghost; empty-state ghost 2×; init opens **`general`** project once per browser session when present; assistant **`.msg-inference-footer`** |
| `animus-chat/hermes_runner.py` | `hermes` CLI subprocess helper; `chat_data_dir()` matches chat `DATA_DIR`; **`gateway_api_bearer()`** / **`gateway_upstream_headers()`** / **`gateway_bearer_source()`** — proxy auth: **`HERMES_API_KEY`** else **`API_SERVER_KEY`** from **`~/.hermes/.env`** (mtime-cached); omit `Authorization` only when both absent (gateway no-key mode) |
| `animus-chat/cron_routes.py` | `/api/cron/*` → Hermes gateway HTTP **`/api/jobs`** (Bearer via ``hermes_runner``); forwards **`workdir`**; **`POST /api/cron/optimize-prompt`** (non-stream chat rewrite); in-process **``cron.jobs``** fallback when gateway unreachable; status still **``hermes cron status``** |
| `animus-chat/hermes_service_client.py` | httpx to **`HERMES_API_URL`** + optional **`HERMES_DASHBOARD_URL`** with **`HERMES_DASHBOARD_SESSION_TOKEN`** (**`X-Hermes-Session-Token`**) for dashboard REST |
| `animus-chat/messaging_routes.py` | **`GET /api/messaging/gateway-status`**, **`/api/messaging/overview`** (rows include **`cron_deliver_home_ready`** when platform enabled+connected+home channel), **`POST /api/messaging/import-animus-slack`** (copy **`SLACK_BOT_TOKEN`** / optional **`SLACK_DEFAULT_CHANNEL`** from repo **`animus.env`** into **`~/.hermes/.env`** + enable Slack in **`config.yaml`** when Hermes has no bot token yet), **`GET/POST /api/messaging/platform/{id}`**; legacy **`GET /api/integrations/hermes-gateway/{status,platforms}`** aliases |
| `animus-chat/skills_routes.py` | `/api/skills/*`; list tries Hermes dashboard **`GET /api/skills`** when session token set; enable/disable uses **`PUT /api/skills/toggle`** or in-process **`hermes_cli.skills_config`**; **`POST /api/skills/create`** writes `SKILL.md`; **Update All** + **`sync_skills`** as before |
| `animus-chat/setup_wizard/wizard_routes.py` | `/api/setup/*` onboarding: **`cfg_still_first_run()`** for status + client-config alignment, `POST /complete` sets `first_run: false` + **`setup_completed_at`**; provider checklist + auth, `tailscale-check`, `check-path`, **`provider-status`** (includes Hermes **`hermes_active_provider`** / **`hermes_default_model`** / **`hermes_active_animus_id`** from `~/.hermes/config.yaml`), **`POST /sync-hermes-model`** (Hermes `config.yaml`: API-key providers + Codex + **cursor-agent** / **claude-code** (→anthropic) / **copilot-acp** with CLI checks; URL fallbacks for mistral/groq/togetherai/cohere; missing base **422**), `cursor-login-start`, **`claude-code-login-start`** (spawn **`claude setup-token`** on host), **Codex OAuth** via **`hermes_cli.codex_device_oauth`** (`codex-auth-start` / `codex-auth-status/{poll_id}` — same device flow as Hermes dashboard, not `hermes auth` subprocess) + `codex-auth-session`, `save-config` (`projects_dir`, Tailscale, wizard provider lists) |
| `animus-chat/requirements.txt` | Python deps; use `animus-chat/.venv/` |

## Hermes Agent bundle

| Path | Purpose |
|------|---------|
| `hermes-agent/` | Full Hermes Agent source used by gateway + CLI; **`gateway/platforms/api_server.py`** `_run_agent` builds streamed finish `usage` from **`run_conversation`** result token fields; **`/api/jobs`** passes **`workdir`** + larger **`prompt`** cap; **`run_agent.py`** Codex **`responses.stream()`** merges terminal SSE **`usage`** when **`get_final_response()`** omits it; **`cron/hermes_chat_delivery.py`** appends cron output into Hermes Chat threads; **`agent/project_workspace.py`** resolves chat data dirs + workspace markdown; **`hermes_cli/main.py`** registers **`hermes project`** (init / history-append / repo-map-refresh / repo-maps-refresh-all / show / write) → **`hermes_cli/project_workspace_cmd.py`**; **`hermes_cli/codex_device_oauth.py`** OpenAI Codex device OAuth (shared by **`hermes_cli/web_server.py`** dashboard routes and ANIMUS **`setup_wizard/wizard_routes.py`** Codex start/poll — no FastAPI required for ANIMUS import) |

## Packaging

| Path | Purpose |
|------|---------|
| `installer/install.sh` | End-user install (venv + editable agent); runs **`installer/ensure-sshpass.sh`** (interactive prompt: **`sshpass`** for Settings → SSH password test); runs **`installer/create-desktop-launcher.sh`** on Linux/macOS GUI hosts; optional Piper voice bundle via **`installer/fetch-piper-voices.sh`** when `curl` present; runs **`installer/merge-hermes-gateway-auth.py`** so **`HERMES_API_KEY`** is filled from **`~/.hermes/.env`** **`API_SERVER_KEY`** when blank |
| `installer/ensure-sshpass.sh` | Buyer helper: if **`sshpass`** missing on Linux/macOS, prompts to install via apt/dnf/pacman/zypper or **Homebrew**; non-interactive shells print one-line install hints; skip with **`SKIP_ANIMUS_SSHPASS=1`** |
| `installer/merge-hermes-gateway-auth.py` | Buyer helper: if **`animus.env`** has empty **`HERMES_API_KEY`** and **`~/.hermes/.env`** has **`API_SERVER_KEY`**, copy into **`animus.env`** (keeps systemd **`EnvironmentFile`** self-contained) |
| `installer/sync-animus-chat-from-zip.sh` | Wrapper that runs **`animus-chat/sync-from-release-zip.sh`**; use from unzip root when **`installer/`** exists |
| `animus-chat/sync-from-release-zip.sh` | **Buyer zip:** patch this **`animus-chat/`** tree from **`animus-vX.Y.Z.zip`** (no **`installer/`** required — run **inside** **`animus-chat/`**); auto-finds zip in parent dir, **`../animus`**, or **`~/animus`** if no arg; see **`START_HERE.txt`** |
| `installer/create-desktop-launcher.sh` | Post-`animus.env`: Linux `.desktop` (menu + Desktop) / macOS `.webloc`; honors `HERMES_CHAT_PUBLIC_URL`, `SKIP_ANIMUS_DESKTOP_LAUNCHER`, Docker/CI/headless skip |
| `installer/fetch-piper-voices.sh` | Downloads six default Piper `.onnx` + `.json` models (EN US/GB + `de_DE-thorsten`) into `~/.local/share/piper` or **`PIPER_VOICES_DIR`** |
| `installer/preflight.sh` | Environment checks; creates **`animus.env`** from **`animus.env.example`** when missing (same as **`install.sh`**) |
| `docker/` | Dockerfile + compose for container runs; image includes **`/app/animus.env`** copied from **`animus.env.example`** at build time |
| `systemd/` | `animus.service` / `animus-agent.service` templates |

## Docs

| Path | Purpose |
|------|---------|
| `docs/hermes-agent-patches.md` | Upstream diff / patch notes; **top banner** — bundled Hermes version, upstream drift, no `hermes update` inside ANIMUS |
| `docs/models.md` | Model cache and providers |
| `docs/tailscale.md` | Remote access |
| `docs/tts.md` | Piper + browser TTS setup, voice dirs, troubleshooting |
| `docs/animus-user-guide.md` | In-app **HELP** content and sole knowledge source for **`/api/help/ask`** |
| `docs/ssh.md` | SSH hosts, keys vs passwords, remote project path / `_ssh_mounts` convention, troubleshooting |
| `docs/GUMROAD.md` | Gumroad packaging checklist, listing copy, buyer zip expectations |
| `docs/BUYER_UPDATES.md` | In-app git updates, private GitHub, SSH / PAT, Gumroad-only path |

## Tests

- **None yet** for ANIMUS wiring; validate with `./animus-chat/.venv/bin/python -c "import server"` and `./build-release.sh`.

## Generated / runtime

| Path | Purpose |
|------|---------|
| `animus-chat/data/` | `DATA_DIR` default; chats, `config.json`, caches (gitignored) |
| `animus-chat/.venv/` | Local venv (gitignored) |
