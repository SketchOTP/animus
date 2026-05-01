# Repo map — `animus-chat/`

Python Starlette server (`server.py`) plus static PWA in `app/`.

| Path | Role |
|------|------|
| `server.py` | API routes, gateway proxy (**`/api/chat`**, …); chat stream token log: allowlisted **`X-Animus-Client`** (**`chat`**, **`plan`**, … **`web`**) → **`record_token_usage(..., animus_client=slug)`**; else **`_infer_proxy_chat_provider_slug`** when **`hermes_provider`** absent → **`cursor-coding`** / **`unknown`** |
| `app/index.html` | Main PWA shell; **`animusClientFetchHeaders`** (**`X-Animus-Client`**) on **`/api/chat`** + **`/api/tokens/record`**; Tokens tab **`aggregateAnimusClientTotals`** / **`renderAnimusClientBreakdown`** (**`animus_client`** surface vs **By source (logging)**); project chat preflight + **`buildMessages`** / **`hermes.session`** SSE |
| `tests/test_token_usage_animus_client.py` | Unittest: **`ANIMUS_CLIENT_SLUGS`**, **`POST /api/tokens/record`**, Help / cron / **`optimize-prompt`**, **`GET ?full=1`**, static **`index.html`** CSV + client breakdown markers (**`CHAT_DATA_DIR`**) |
| `app/ghostonlyicon.png` | App icon + **sidebar** ANIMUS row (**2×** mark via **`.brand-ghost--sidebar`**) + empty chat + About + notifications (favicon / manifest / apple-touch); **no** ghost on main-column top bar (title text + New chat only) |
| `app/manifest.json` / `app/sw.js` | PWA manifest (icons → `ghostonlyicon.png`) and service worker (`animus-v57` cache) |
| `hermes_runner.py` | Subprocess wrapper for `hermes` CLI; **`gateway_api_bearer()`** / **`gateway_upstream_headers()`** / **`gateway_bearer_source()`** ( **`HERMES_API_KEY`** or **`API_SERVER_KEY`** from **`~/.hermes/.env`** ) |
| `token_usage.py` | **`token_usage.jsonl`**, **`ANIMUS_CLIENT_SLUGS`**, **`chat_usage_in_out`**, **`record_token_usage(..., animus_client=)`**, **`GET/POST /api/tokens/*`** |
| `cron_routes.py` | `/api/cron/*` — jobs CRUD + **`workdir`** forward + **`POST /api/cron/optimize-prompt`** |
| `messaging_routes.py` | `/api/messaging/*` — gateway health + overview (**`cron_deliver_home_ready`** per platform) + **POST /api/messaging/import-animus-slack** + **GET/POST** per-platform setup (Hermes **`~/.hermes/.env`** + **`config.yaml`**); legacy **`GET /api/integrations/hermes-gateway/*`** |
| `skills_routes.py` | `/api/skills/*` control-plane endpoints |
| `setup_wizard/wizard_routes.py` | `/api/setup/*` onboarding (providers, tailscale-check, check-path, provider-status; **`cursor-login-start`**, **`claude-code-login-start`** (spawn `claude setup-token` on host), Codex `codex-auth-start` + `codex-auth-status/{poll_id}` + `codex-auth-session`); after **`projects_dir`** **`save-config`** or **`/complete`**, calls **`server.ensure_animus_general_project()`** |
| `requirements.txt` | Python dependencies (**`python-multipart`**, **`faster-whisper`**, Starlette stack, etc.) |
| *(repo root)* `artifacts/hermes_project_session_priming_e2e.md` | Verification log: project chat system priming, gateway **`hermes.session`** SSE, pytest results |
| `restart.sh` | Restart user `animus.service` when present |
