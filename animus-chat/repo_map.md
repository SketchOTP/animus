# Repo map — `animus-chat/`

Python Starlette server (`server.py`) plus static PWA in `app/`.

| Path | Role |
|------|------|
| `server.py` | API routes, gateway proxy, workspace helpers, client-config + `check-updates` / `apply-update` (`ANIMUS_UPDATE_URL` manifest + zip extract) |
| `app/index.html` | Main PWA shell |
| `app/ghostonlyicon.png` | App icon + sidebar/header brand + empty chat + About + notifications (favicon / manifest / apple-touch) |
| `app/manifest.json` / `app/sw.js` | PWA manifest (icons → `ghostonlyicon.png`) and service worker (`animus-v2` cache) |
| `hermes_runner.py` | Subprocess wrapper for `hermes` CLI |
| `cron_routes.py` | `/api/cron/*` control-plane endpoints |
| `skills_routes.py` | `/api/skills/*` control-plane endpoints |
| `setup_wizard/wizard_routes.py` | `/api/setup/*` onboarding (providers, tailscale-check, check-path, provider-status; Codex async `codex-auth-start` + `codex-auth-status/{poll_id}` + `codex-auth-session`) |
| `requirements.txt` | Python dependencies |
| `restart.sh` | Restart user `animus.service` when present |
