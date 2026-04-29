# Installing ANIMUS

## Requirements

- Linux or macOS (Windows via WSL2 is untested but should work).
- Python **3.10+**, `pip`, and ~2GB disk for the bundled Hermes Agent source (excluding its `venv/`).
- A running **Hermes gateway** (OpenAI-compatible) reachable at `HERMES_API_URL`, or install gateway from the bundled `hermes-agent/` per upstream docs.

## Automated install

```bash
./installer/preflight.sh
./installer/install.sh
```

The installer can **pre-download** the same Piper voice bundle as the server (`installer/fetch-piper-voices.sh` when `curl` exists; six models, ~380 MB). The running ANIMUS server also **downloads those models automatically** when Piper is installed but no voices are on disk — see `docs/tts.md`. Skip both with `SKIP_ANIMUS_PIPER_VOICES=1`.

Default HTTP port is **3001** (`CHAT_PORT` in `animus.env.example`).

### Desktop shortcut (PC install)

`installer/install.sh` runs `installer/create-desktop-launcher.sh` after `animus.env` exists. On **Linux** with `DISPLAY` or `WAYLAND_DISPLAY`, it adds `~/.local/share/applications/animus.desktop` and copies to your **Desktop** when present (`xdg-open` → same URL as the app, so browser storage matches post-setup use). On **macOS**, it drops **`ANIMUS.webloc`** on the Desktop. The step is skipped in Docker, CI, headless Linux, and when `SKIP_ANIMUS_DESKTOP_LAUNCHER=1` is set in the environment.

After the in-app wizard finishes on a **desktop** browser, ANIMUS may offer a one-time download of the same shortcut (phones keep the usual **PWA install** path only). Optional: `GET /api/animus/desktop-launcher` (add `?fmt=webloc` on Mac).

## Manual install

1. Clone or unpack this repository.
2. `python3 -m venv animus-chat/.venv && animus-chat/.venv/bin/pip install -r animus-chat/requirements.txt`
3. `animus-chat/.venv/bin/pip install -e ./hermes-agent` (from repo root).
4. Copy `animus.env.example` → `animus.env` and set variables.
5. `cd animus-chat && ../animus-chat/.venv/bin/python server.py`

## systemd

Templates live in `systemd/animus.service` and `systemd/animus-agent.service`. Copy into `~/.config/systemd/user/`, adjust `WorkingDirectory` / `ExecStart` to match your layout, then:

```bash
systemctl --user daemon-reload
systemctl --user enable --now animus.service
```

## Environment variables

See `animus.env.example` at the repository root. Important keys:

| Variable | Purpose |
|----------|---------|
| `HERMES_API_URL` | Gateway base URL |
| `HERMES_API_KEY` | Gateway bearer token |
| `HERMES_AGENT_DIR` | Path to bundled `hermes-agent/` |
| `CHAT_HOST` / `CHAT_PORT` | Bind address / port (default port **3001**) |
| `CHAT_DATA_DIR` / `HERMES_CHAT_DATA_DIR` | Where conversations and `config.json` live (wizard + wake lock use the same directory) |
| `DATA_DIR` | Optional override read by some ANIMUS helpers; prefer `CHAT_DATA_DIR` for consistency |

## Docker

Build and smoke-check from the repository root (requires Docker):

```bash
cd docker
docker compose build
docker compose up -d
sleep 8
curl -sS http://127.0.0.1:3001/api/version | python3 -m json.tool
curl -sS http://127.0.0.1:3001/api/setup/hermes-check | python3 -m json.tool
docker compose down
```

The compose file should expose **3001** for ANIMUS chat (`CHAT_PORT`). If `curl` fails, verify `animus.env` is mounted and the gateway is reachable from the container.

## Troubleshooting

- **In-app “Check for updates” / git errors** — Updates compare your install to `origin/main`. You need a **git clone** (or an unpacked tree that still has commit history and a tracking `main` branch). A plain copy of the folder without `.git`, or `git init` with no commits, cannot receive updates through the UI; clone from GitHub or re-install from a release that sets up `git` as in `installer/install.sh`.
- **Port in use** — change `CHAT_PORT` in `animus.env`.
- **`hermes` not found** — ensure the venv where you installed Hermes Agent is on `PATH`, or set `HERMES_BIN`.
- **Empty model list** — call `POST /api/models/refresh` with a valid `HERMES_API_KEY`, or finish the setup wizard.
- **PWA shows an old name** — bump the service worker cache in `animus-chat/app/sw.js` (`animus-v1`) and hard-reload.

## Tailscale

See `docs/tailscale.md`.
