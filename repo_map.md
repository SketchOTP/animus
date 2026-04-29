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
| `animus-chat/server.py` | Starlette app: gateway proxy, workspace APIs, static PWA, `GET/POST /api/animus/client-config` (wake lock, `projects_dir`, `inference_models`, Tailscale fields, wizard provider lists ↔ `config.json`), `POST /api/animus/check-updates`, `POST /api/animus/apply-update`, `projects_sync_root()` reads `projects_dir` from config |
| `animus-chat/app/` | PWA (`index.html` includes Phase 2 wizard + tooltips + cron/model wiring, `manifest.json`, `sw.js`, icons) |
| `animus-chat/hermes_runner.py` | `hermes` CLI subprocess helper; `chat_data_dir()` matches chat `DATA_DIR` |
| `animus-chat/cron_routes.py` | `/api/cron/*` control plane |
| `animus-chat/skills_routes.py` | `/api/skills/*` control plane |
| `animus-chat/setup_wizard/wizard_routes.py` | `/api/setup/*` onboarding: provider checklist + auth, `tailscale-check`, `check-path`, `provider-status`, `cursor-login-start`, `codex-auth-start` (async) + `codex-auth-status/{poll_id}` + `codex-auth-session`, `save-config` (`projects_dir`, Tailscale, wizard provider lists) |
| `animus-chat/requirements.txt` | Python deps; use `animus-chat/.venv/` |

## Hermes Agent bundle

| Path | Purpose |
|------|---------|
| `hermes-agent/` | Full Hermes Agent source used by gateway + CLI |

## Packaging

| Path | Purpose |
|------|---------|
| `installer/install.sh` | End-user install (venv + editable agent) |
| `installer/preflight.sh` | Environment checks |
| `docker/` | Dockerfile + compose for container runs |
| `systemd/` | `animus.service` / `animus-agent.service` templates |

## Docs

| Path | Purpose |
|------|---------|
| `docs/hermes-agent-patches.md` | Upstream diff / patch notes; **top banner** — bundled Hermes version, upstream drift, no `hermes update` inside ANIMUS |
| `docs/models.md` | Model cache and providers |
| `docs/tailscale.md` | Remote access |

## Tests

- **None yet** for ANIMUS wiring; validate with `./animus-chat/.venv/bin/python -c "import server"` and `./build-release.sh`.

## Generated / runtime

| Path | Purpose |
|------|---------|
| `animus-chat/data/` | `DATA_DIR` default; chats, `config.json`, caches (gitignored) |
| `animus-chat/.venv/` | Local venv (gitignored) |
