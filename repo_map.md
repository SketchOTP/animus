# Repo map (animus)

Quick navigation for agents. Update when layout, entrypoints, or roles change.

## Repository root

| Path | Purpose |
|------|---------|
| `README.md` | Product overview and quick start |
| `INSTALL.md` | Manual install, systemd, troubleshooting |
| `VERSION` | Semver exposed via `GET /api/version` |
| `animus.env.example` | Environment template (copy to `animus.env`) |
| `build-release.sh` | Sanitisation checks + release zip + `## Patch` count in `docs/hermes-agent-patches.md` |
| `scripts/phase3-smoke-checklist.md` | Phase 3 manual smoke steps + **Practical tips** (keys, SSE usage, screenshots, `build-release.sh` shell hygiene) |
| `project_goal.md` | North star / build directive |
| `project_status.md` | Current snapshot |
| `project_history.md` | Session log |
| `project_knowledge.md` | Lessons and validation tips |
| `repo_map.md` | This map |
| `AGENTS.md` | Agent workflow rules |

## Application

| Path | Purpose |
|------|---------|
| `animus-chat/server.py` | Starlette app: gateway proxy, workspace APIs, static PWA, `GET/POST /api/animus/client-config` (wake lock, `projects_dir`, `inference_models`, **`tts_backend`**, **`cron_timezone`**, Tailscale fields, wizard provider lists ↔ `config.json`), **`GET /api/animus/desktop-launcher`** (download `.desktop` or `?fmt=webloc` for macOS), **`POST /api/models/refresh`** (local Hermes curated catalog + Cursor CLI models when `cursor whoami` succeeds — **no `HERMES_API_KEY`**), **`claude-code`** model rows from Hermes anthropic catalog + `auto`, chat SSE **token usage** logging via `token_usage.record_token_usage`, `GET /api/projects/list-simple`, `GET /api/system/timezones`, `POST /api/animus/check-updates`, `POST /api/animus/apply-update`, `projects_sync_root()` reads `projects_dir` from config |
| `animus-chat/token_usage.py` | `record_token_usage`, `GET /api/tokens/usage`, `POST /api/tokens/record` → `token_usage.jsonl` under `chat_data_dir()` |
| `animus-chat/integrations_slack.py` | `GET/POST /api/integrations/slack/{status,save,test}` — reads/writes repo-root `animus.env` for `SLACK_*` |
| `animus-chat/ssh_routes.py` | `GET/POST/PUT/DELETE /api/ssh/hosts`, `POST /api/ssh/test` — `ssh_hosts.json` + `SSH_PASSWORD_*` in `animus.env` |
| `animus-chat/help_routes.py` | **`GET /api/help/guide`** — `topics_markdown`, `faq_markdown`, `topics[]` (+ full `markdown`); **`POST /api/help/ask`** — guide-grounded Help bot (non-stream; `source: "help"` in token log) |
| `animus-chat/tts_routes.py` | `GET /api/tts/backends`, `GET /api/tts/piper/voices` (+ **`fetching`** / **`fetch_error`**), `POST /api/tts/piper/speak` (WAV); **background HF download** of default Piper voices (**first:** `en_GB-alan-medium`) when binary present and no `.onnx` models; `PIPER_VOICES_DIR` / `~/.local/share/piper` |
| `animus-chat/app/` | PWA (`index.html` includes Phase 2 wizard + tooltips + cron/model wiring, wizard **desktop launcher** one-time download on non-phone after **Open ANIMUS**, Plan tab **`recordTokenUsageManualIfPresent`** after Hermes JSON completions, stacked TTS Settings blocks, **SSH host modal** (`#sshHostModalBackdrop`), **HELP** modal (`#helpGuideBackdrop` → `/api/help/*`), Settings **toggle rows** (reuse `ssh-toggle-row` for unread badges + wake lock), **notification thread unread** (`notif-item-unread` + `hermes_notif_conv_read_counts_v1`), startup splash **`ANIMUSLOGO.png`** (`#splash-screen`), wizard welcome **`ANIMUSLOGOICON.png`**, branding + empty chat + favicon/PWA/notifications via **`ghostonlyicon.png`** (`manifest.json` icons, `sw.js` cache **`animus-v2`**), wizard **Agent check** (reachable only, no version dump), `manifest.json`, `sw.js`; legacy **`icon.svg`** / **`icon-192.png`** / **`icon-512.png`** still on disk for reference or fallbacks) |
| `animus-chat/hermes_runner.py` | `hermes` CLI subprocess helper; `chat_data_dir()` matches chat `DATA_DIR` |
| `animus-chat/cron_routes.py` | `/api/cron/*` control plane |
| `animus-chat/skills_routes.py` | `/api/skills/*` control plane including **`POST /api/skills/create`** (writes `SKILL.md` under Hermes user skills dir) |
| `animus-chat/setup_wizard/wizard_routes.py` | `/api/setup/*` onboarding: provider checklist + auth, `tailscale-check`, `check-path`, `provider-status`, `cursor-login-start`, `codex-auth-start` (async) + `codex-auth-status/{poll_id}` + `codex-auth-session`, `save-config` (`projects_dir`, Tailscale, wizard provider lists) |
| `animus-chat/requirements.txt` | Python deps; use `animus-chat/.venv/` |

## Hermes Agent bundle

| Path | Purpose |
|------|---------|
| `hermes-agent/` | Full Hermes Agent source used by gateway + CLI |

## Packaging

| Path | Purpose |
|------|---------|
| `installer/install.sh` | End-user install (venv + editable agent; runs **`installer/create-desktop-launcher.sh`** on Linux/macOS GUI hosts; optional Piper voice bundle via **`installer/fetch-piper-voices.sh`** when `curl` present) |
| `installer/create-desktop-launcher.sh` | Post-`animus.env`: Linux `.desktop` (menu + Desktop) / macOS `.webloc`; honors `HERMES_CHAT_PUBLIC_URL`, `SKIP_ANIMUS_DESKTOP_LAUNCHER`, Docker/CI/headless skip |
| `installer/fetch-piper-voices.sh` | Downloads six default Piper `.onnx` + `.json` models (EN US/GB + `de_DE-thorsten`) into `~/.local/share/piper` or **`PIPER_VOICES_DIR`** |
| `installer/preflight.sh` | Environment checks |
| `docker/` | Dockerfile + compose for container runs |
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

## Tests

- **None yet** for ANIMUS wiring; validate with `./animus-chat/.venv/bin/python -c "import server"` and `./build-release.sh`.

## Generated / runtime

| Path | Purpose |
|------|---------|
| `animus-chat/data/` | `DATA_DIR` default; chats, `config.json`, caches (gitignored) |
| `animus-chat/.venv/` | Local venv (gitignored) |
