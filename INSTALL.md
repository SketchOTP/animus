# Installing ANIMUS

## Requirements

- Linux or macOS (Windows via WSL2 is untested but should work).
- Python **3.10+**, `pip`, and ~2GB disk for the bundled Hermes Agent source (excluding its `venv/`).
- **`sshpass`** (optional but recommended on Linux if you use **SSH password** auth in Settings): `install.sh` prompts to install it when missing; Docker image includes it. Key-based SSH does not need it.
- A running **Hermes gateway** (OpenAI-compatible) reachable at `HERMES_API_URL`, or install gateway from the bundled `hermes-agent/` per upstream docs.

## Automated install

```bash
./installer/preflight.sh
./installer/install.sh
```

**`animus.env`:** If the file is missing, **`preflight.sh`** and **`install.sh`** both copy **`animus.env.example`** → **`animus.env`** at the repo root. Set paths and provider keys via the wizard or by editing **`animus.env`**. **`HERMES_API_KEY`** is the **gateway** bearer (OpenAI-compatible endpoint at **`HERMES_API_URL`**): if your Hermes gateway uses **`API_SERVER_KEY`** in **`~/.hermes/.env`**, **`install.sh`** / **`preflight.sh`** run **`installer/merge-hermes-gateway-auth.py`** to copy it into **`HERMES_API_KEY`** when that line is still blank, and the running server also reads **`API_SERVER_KEY`** from that file at runtime when **`HERMES_API_KEY`** is unset. If the gateway has **no** API key configured, leave **`HERMES_API_KEY`** unset — ANIMUS still proxies chat (see **`animus.env.example`**).

**In-app updates:** Set **`ANIMUS_UPDATE_URL`** in **`animus.env`** to your update manifest URL (see **`animus.env.example`**). The app fetches that JSON and can download the release zip when you use **Check for updates** / **Apply update**. Sellers typically deploy the separate **`animus-site`** repo on **Vercel** (or self-host); see **`docs/GUMROAD.md`**. Buyer-facing help: **`docs/BUYER_UPDATES.md`**.

The installer can **pre-download** the same Piper voice bundle as the server (`installer/fetch-piper-voices.sh` when `curl` exists; six models, ~380 MB). The running ANIMUS server also **downloads those models automatically** when Piper is installed but no voices are on disk — see `docs/tts.md`. Skip both with `SKIP_ANIMUS_PIPER_VOICES=1`.

Default HTTP port is **3001** (`CHAT_PORT` in `animus.env.example`).

### Desktop shortcut (PC install)

`installer/install.sh` runs `installer/create-desktop-launcher.sh` after `animus.env` exists. On **Linux** with `DISPLAY` or `WAYLAND_DISPLAY`, it adds `~/.local/share/applications/animus.desktop` and copies to your **Desktop** when present (`xdg-open` → same URL as the app, so browser storage matches post-setup use). On **macOS**, it drops **`ANIMUS.webloc`** on the Desktop. The step is skipped in Docker, CI, headless Linux, and when `SKIP_ANIMUS_DESKTOP_LAUNCHER=1` is set in the environment.

After the in-app wizard finishes on a **desktop** browser, ANIMUS may offer a one-time download of the same shortcut (phones keep the usual **PWA install** path only). Optional: `GET /api/animus/desktop-launcher` (add `?fmt=webloc` on Mac).

## Manual install

1. Clone or unpack this repository.
2. `python3 -m venv animus-chat/.venv && animus-chat/.venv/bin/pip install -r animus-chat/requirements.txt`
3. `animus-chat/.venv/bin/pip install -e ./hermes-agent` (from repo root).
4. Copy `animus.env.example` → `animus.env` and set variables (skipped automatically if you already ran **`install.sh`**, which creates **`animus.env`** when missing).
5. `cd animus-chat && ../animus-chat/.venv/bin/python server.py`

## systemd

Templates live in `systemd/animus.service` and `systemd/animus-agent.service`. Copy into `~/.config/systemd/user/`, adjust `WorkingDirectory` / `ExecStart` to match your layout, then:

```bash
systemctl --user daemon-reload
systemctl --user enable --now animus.service
```

**Monorepo dev (single `~/animus` checkout):** from the repo root run `./scripts/sync-dev-systemd.sh` — installs `~/.config/systemd/user/animus.service` from `systemd/animus.service` (defaults to `%h/animus/animus-chat`), creates **`animus.env`** from **`animus.env.example`** if missing with **`HERMES_AGENT_DIR`** set to this repo’s **`hermes-agent/`**, appends **`INSTALL_DIR`** when needed, then `daemon-reload`. It also symlinks **`scripts/animus`** to **`~/.local/bin/animus`** so you can run **`animus start`**, **`animus stop`**, **`animus restart`**, or **`animus status`** (ensure **`~/.local/bin`** is on your **`PATH`**). Equivalent: **`systemctl --user restart animus.service`**. After editing chat code, `animus-chat/restart-after-code-change.sh` prefers **`animus.service`** over legacy **`hermes-chat.service`**.

## Environment variables

See `animus.env.example` at the repository root. Important keys:

| Variable | Purpose |
|----------|---------|
| `HERMES_API_URL` | Gateway base URL |
| `HERMES_API_KEY` | Gateway bearer token (omit if the gateway allows unauthenticated local access) |
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

The compose file should expose **3001** for ANIMUS chat (`CHAT_PORT`). The Docker image includes **`/app/animus.env`** copied from **`animus.env.example`** at build time so the app always has a starter env file; override with a bind mount or **`docker/.env`** (compose **`env_file`**) as needed. If `curl` fails, verify the gateway is reachable from the container and env vars match your setup.

## Troubleshooting

- **Chat shows “Invalid API key” (401 from gateway)** — Hermes and ANIMUS must use the **same** secret: the gateway reads **`API_SERVER_KEY`** in **`~/.hermes/.env`**; ANIMUS sends **`Authorization: Bearer`** from **`HERMES_API_KEY`** in **`animus.env`**. Current builds fill **`HERMES_API_KEY`** at install time when possible, and read **`API_SERVER_KEY`** at runtime when **`HERMES_API_KEY`** is blank. Diagnose: `curl -sS http://127.0.0.1:3001/api/version | jq .gateway_bearer_source,.gateway_openai_models_http,.gateway_openai_models_ok` — you want **`gateway_openai_models_ok`: true** and HTTP **200** (not **401**). If **`gateway_bearer_source`** is **`none`** but the gateway requires a key, set **`HERMES_API_KEY`** manually or run `python3 installer/merge-hermes-gateway-auth.py animus.env` from the unzip root.
- **`systemctl restart animus` fails (“Unit not found”)** — ANIMUS ships a **user** unit: use **`systemctl --user restart animus.service`** after **`daemon-reload`**, or run **`animus-chat/restart-after-code-change.sh`** from the repo.
- **“HERMES_API_KEY is not configured…” in chat** — That exact text only appears in **older** `animus-chat/server.py` builds. Confirm you are running current code: `curl -sS http://127.0.0.1:3001/api/version | jq .chat_server_rev,.chat_proxy_blocks_on_missing_hermes_api_key` — you should see a recent **`chat_server_rev`** string and **`chat_proxy_blocks_on_missing_hermes_api_key`: false**. If `chat_server_rev` is months old or `chat_proxy_blocks_on_missing_hermes_api_key` is missing/`null`, patch from a newer release zip (see below) or reinstall, then **restart** the chat process.
- **Patch `animus-chat/` from a newer `animus-vX.Y.Z.zip` without re-unzipping everything** — (1) Full tree ( **`installer/`** + **`animus-chat/`** next to **`VERSION`**): `chmod +x installer/sync-animus-chat-from-zip.sh` then `./installer/sync-animus-chat-from-zip.sh /path/to/animus-v1.0.5.zip` (optional second arg: target **`animus-chat`** dir). (2) **Only `animus-chat/`** on disk (no **`installer/`**): the script is **inside** the zip — extract it once, then run: `cd animus-chat && unzip -p /path/to/animus-v1.0.5.zip animus-chat/sync-from-release-zip.sh > sync-from-release-zip.sh && chmod +x sync-from-release-zip.sh && ./sync-from-release-zip.sh /path/to/animus-v1.0.5.zip`. Then restart the chat server.
- **In-app “Check for updates” fails** — Ensure **`ANIMUS_UPDATE_URL`** is set in **`animus.env`** and points at a reachable **`latest.json`** manifest. If the update server is down, the app still runs; try again later or reinstall from Gumroad — see **`docs/BUYER_UPDATES.md`**.
- **Port in use** — change `CHAT_PORT` in `animus.env`.
- **`hermes` not found** — ensure the venv where you installed Hermes Agent is on `PATH`, or set `HERMES_BIN`.
- **Empty model list** — call `POST /api/models/refresh` with a valid `HERMES_API_KEY`, or finish the setup wizard.
- **PWA shows an old name** — bump the service worker cache in `animus-chat/app/sw.js` (`animus-v1`) and hard-reload.
- **Hermes WhatsApp bridge** — release zips omit `hermes-agent/scripts/whatsapp-bridge/node_modules/` to save space. If you use the gateway WhatsApp integration, run once: `cd hermes-agent/scripts/whatsapp-bridge && npm ci` (or `npm install`) on the host, then restart the gateway.

## Tailscale

See `docs/tailscale.md`.
