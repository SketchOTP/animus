# Project goal (animus)

## What we are building

## Directive Navigation Index

- Primary directive and constraints: `## ANIMUS — Distributable Product Build Directive`, `## ⚠️ CRITICAL — READ BEFORE TOUCHING ANYTHING`
- Build spec: sections `## 0` through `## 20`
- Execution waves: `## ANIMUS — Phase 2 Build Directive` through `## ANIMUS — Phase 5 Build Directive`
- Go-live operations: `## ANIMUS — Phase 4: Go-Live Directive` and launch checklist
- Usage tip: prefer heading search + bounded section reads; avoid full-file scans unless required

## ANIMUS — Distributable Product Build Directive

**Product Name:** ANIMUS
**Codename:** `animus`
**Target Audience:** AI coder executing a full project build
**Goal:** Create a clean, distributable, self-contained product named **ANIMUS** — derived from a private Hermes Chat instance — that any user can install, configure, and run, bundled together with the Hermes Agent CLI, and sold via Gumroad.

---

## ⚠️ CRITICAL — READ BEFORE TOUCHING ANYTHING

### Both live instances are off-limits. Do not touch either of them.

The owner runs two **personal, production systems** that must not be modified, restarted, stopped, or read from as live systems in any way:

| Live system | Exact path | Service unit | Port |
|---|---|---|---|
| Hermes Chat (UI) | `/home/sketch/hermes/hermes-chat` | `hermes-chat.service` | 3000 |
| Hermes Agent (CLI) | `/home/sketch/hermes/hermes-agent` | check with `systemctl list-units \| grep hermes` | varies |

Both paths are known and confirmed. Both systems are fine-tuned and actively used daily. **Do not guess, explore, or probe — the paths are above. Copy them and stop.**

The product you are building is called **ANIMUS**. It is a copy of both live systems, cleaned, renamed, and extended into a single unified repository. You are not editing either live system. You are working entirely on copies.

### Why Both Must Be Copied

Custom work done on the owner's instance — the Cursor CLI model provider patch, cron integration behaviour, skill management, model enumeration, reconnect logic, and other features — may have required changes to **Hermes Agent** and not just Hermes Chat. If ANIMUS ships with a clean public Hermes Agent and only a patched chat UI, those Agent-side customisations will be absent and features will silently break for customers. Bundling the owner's actual Hermes Agent copy alongside the chat UI ensures the full feature set is preserved exactly.

### What you MUST NOT do

| Action | Why it is forbidden |
|---|---|
| `sudo systemctl stop hermes-chat` | Kills the owner's live chat UI |
| `sudo systemctl restart hermes-chat` | Same |
| Stop, restart, or interact with any hermes agent service unit | Kills the owner's live AI backend |
| Edit any file inside `/home/sketch/hermes/hermes-chat/` | That is the live chat instance |
| Edit any file inside `/home/sketch/hermes/hermes-agent/` | That is the live agent instance |
| Run `restart-after-code-change.sh` from the source directory | Restarts the live server |
| Write to `/home/sketch/hermes/hermes-chat/hermes-chat.env` | Overwrites live secrets |
| Write to `/home/sketch/hermes/hermes-chat/data/` | Corrupts live chat history |
| Write to `/home/sketch/hermes/hermes-agent/data/` | Corrupts live agent data |
| Run any command that binds to port 3000 | Port conflict — crashes the live service |
| Copy either source and then edit files in or adjacent to `/home/sketch/hermes/` | Keep the working copy fully isolated at `/home/sketch/animus/` |

### What you MUST do instead

**Step 1 — Copy both into a single new repo. This is your first and only write action.**

Both paths are confirmed. Run exactly these commands:

```bash
mkdir -p /home/sketch/animus
cp -r /home/sketch/hermes/hermes-chat  /home/sketch/animus/animus-chat
cp -r /home/sketch/hermes/hermes-agent /home/sketch/animus/hermes-agent
```

Verify the copy completed:
```bash
ls /home/sketch/animus/
# Must show: animus-chat  hermes-agent
du -sh /home/sketch/animus/animus-chat
du -sh /home/sketch/animus/hermes-agent
```

All subsequent work happens inside `/home/sketch/animus/` only. Never `cd` into `/home/sketch/hermes/` for any reason.

**Step 2 — Diff Hermes Agent against upstream before touching anything.**

Before making any changes to the copied Hermes Agent, produce a diff to find exactly what the owner has customised:

```bash
cd /home/sketch/animus/hermes-agent
git log --oneline -20          # check for local commits
git diff origin/main           # diff against upstream if remote exists
git status                     # check for uncommitted changes
```

If it is not a git repo, clone the public upstream version elsewhere and diff manually:
```bash
# Example — adjust to actual upstream source:
git clone <upstream-hermes-agent-repo> /tmp/hermes-agent-upstream
diff -rq /home/sketch/animus/hermes-agent /tmp/hermes-agent-upstream \
  --exclude="*.pyc" --exclude="__pycache__" --exclude="data" --exclude="*.env"
```

**Document every difference found in `docs/hermes-agent-patches.md`** before proceeding. This is mandatory — it is your change record and the maintenance guide for all future ANIMUS releases.

**Step 3 — Use a different port.**

The live instance owns port 3000. Run your ANIMUS development copy on port **3001**. Set this as the default in `animus.env.example` with a clear comment.

**Step 4 — Verify isolation before every session.**

Before doing any work in any session, confirm:
```bash
pwd  # Must show /home/sketch/animus/... 
     # If it shows /home/sketch/hermes/... — stop immediately
```

**Step 5 — Never reference the live service units.**

Create new service files named `animus.service` and `animus-agent.service`. Never modify or symlink to `hermes-chat.service` or any existing hermes service unit.

### Summary

```
LIVE SYSTEMS — DO NOT TOUCH              ANIMUS WORKING COPY — ALL WORK HERE
/home/sketch/hermes/hermes-chat/         /home/sketch/animus/animus-chat/
/home/sketch/hermes/hermes-agent/        /home/sketch/animus/hermes-agent/
port 3000                                port 3001
hermes-chat.service                      animus.service (new)
<hermes agent service unit>              animus-agent.service (new)
```

If you are ever unsure whether an action affects either live system — **stop and ask** before proceeding.

---

## 0. Summary of What You Are Building

You are creating **ANIMUS** — a self-contained, zero-personal-data product bundle derived from a private Hermes Chat instance. The final product must:

1. Be named **ANIMUS** everywhere: UI, manifest, service files, env files, docs, zip name.
2. Include **Hermes Agent CLI** and the **ANIMUS** app as a single unified install.
3. Walk any new user through full setup via a **first-run onboarding wizard** inside the app itself.
4. Expose **all AI model choices** that Hermes Agent supports (not just a hardcoded short list).
5. Be **fully dockerised and script-installable** so users can be running in under 10 minutes.
6. Contain **zero personal data, zero private keys, zero hardcoded hostnames or user-specific paths** from the original install.
7. Ship as a downloadable zip/tarball suitable for Gumroad distribution.

Do NOT modify the running live instance. Work only on the copy as described in the Critical section above.

---

## 1. Repository Structure to Create

The ANIMUS repo is a **monorepo** containing both the chat UI and the Hermes Agent, copied from the owner's live systems. The structure must be:

```
animus/                              ← root of the ANIMUS monorepo
├── README.md                        ← User-facing quick start
├── INSTALL.md                       ← Detailed install guide
├── LICENSE
├── VERSION                          ← e.g. 1.0.0
├── .gitignore
│
├── animus-chat/                     ← Copied + cleaned from live hermes-chat
│   ├── server.py                    ← Starlette API proxy (cleaned, renamed)
│   ├── static/
│   │   ├── index.html               ← Single-page ANIMUS PWA
│   │   ├── manifest.json            ← name/short_name = ANIMUS
│   │   ├── sw.js                    ← cache = animus-v1
│   │   ├── icon.svg
│   │   ├── icon-192.png
│   │   └── icon-512.png
│   ├── cron_routes.py               ← NEW: cron API layer (§18)
│   ├── skills_routes.py             ← NEW: skills API layer (§19)
│   ├── hermes_runner.py             ← NEW: shared subprocess utility (§19.3)
│   ├── setup_wizard/
│   │   └── wizard_routes.py         ← NEW: first-run wizard routes (§4)
│   ├── generate-icons.py
│   ├── animus.env.example
│   └── requirements.txt
│
├── hermes-agent/                    ← Copied from owner's live Hermes Agent install
│   ├── (full Hermes Agent source)   ← Do NOT strip or modify structure
│   ├── providers/
│   │   └── cursor/                  ← Owner's Cursor CLI patch lives here (§17)
│   └── ...
│
├── systemd/
│   ├── animus.service               ← Chat UI service unit
│   └── animus-agent.service         ← Agent service unit (if applicable)
│
├── installer/
│   ├── install.sh                   ← Installs both agent + chat
│   ├── install.ps1
│   └── preflight.sh
│
├── docker/
│   ├── Dockerfile
│   ├── docker-compose.yml           ← Runs both agent + chat
│   └── .env.example
│
└── docs/
    ├── tailscale.md
    ├── models.md
    ├── hermes-agent-patches.md      ← NEW: diff record of owner's agent customisations
    └── screenshots/
```

### Key structural rules

- `animus-chat/` and `hermes-agent/` are peers at the repo root — neither is nested inside the other.
- `hermes-agent/` is a **complete copy** of the owner's live agent, including all customisations. Do not cherry-pick files — copy the whole thing so nothing is accidentally left behind.
- The Cursor CLI patch (§17) must stay in its location within `hermes-agent/` wherever it currently lives in the owner's install. Do not move it.
- `hermes_runner.py`, `cron_routes.py`, and `skills_routes.py` are new files created in `animus-chat/` — they do not come from the source copy.
- `docs/hermes-agent-patches.md` must be written before any other work begins (see Critical §, Step 3).

---

## 2. Sanitisation & Renaming Requirements (Critical — Do These First)

Before writing any feature code, audit every file in the copied directory for the following and remove or replace all instances. **Renaming to ANIMUS is part of sanitisation — do both together.**

### 2.1 Personal Data to Remove

| What to find | What to do |
|---|---|
| Any hardcoded IP addresses or hostnames (e.g. `atlas.tail1a5964.ts.net`) | Replace with `${HOST}` placeholder or env var |
| Any real API keys or tokens | Remove entirely; document via `animus.env.example` |
| The sudo password `5206` or any other credential | Remove — it must not exist anywhere in the codebase |
| Any reference to `/home/sketch/hermes/hermes-chat/` | Replace with `${INSTALL_DIR}` or relative paths |
| Any reference to `/home/sketch/hermes/hermes-agent/` | Replace with `${INSTALL_DIR}` or relative paths |
| Any reference to `/home/sketch/` anywhere | Replace with `${INSTALL_DIR}` or relative paths |
| Any personal Slack workspace IDs, webhook URLs, or project names | Remove entirely |
| Project history entries from the source | Wipe; start a fresh `project_history.md` |
| Any reference to the original developer's identity | Remove |
| Any cron jobs or scheduled tasks that reference personal projects | Remove; the user creates their own |
| The `repo_map.md` from the source | Regenerate for the new ANIMUS structure |
| PWA cache bucket name `hermes-chat-v50` | Reset to `animus-v1` |

### 2.2 Renaming — "Hermes Chat" → "ANIMUS"

Every occurrence of the old product name must be replaced. The table below is exhaustive — do not leave any instance of the old name in the product the customer receives.

| Location | Old value | New value |
|---|---|---|
| `app/static/index.html` — page `<title>` | `Hermes Chat` / `ANIMUS` (source used both) | `ANIMUS` |
| `app/static/index.html` — all visible UI text | Any instance of "Hermes Chat" | `ANIMUS` |
| `app/static/manifest.json` — `name` field | `Hermes Chat` | `ANIMUS` |
| `app/static/manifest.json` — `short_name` field | `Hermes` | `ANIMUS` |
| `app/static/sw.js` — cache bucket name | `hermes-chat-v50` (or any variant) | `animus-v1` |
| `systemd/animus.service` — `Description=` | `Hermes Chat` | `ANIMUS` |
| `README.md` — product name throughout | `Hermes Chat` | `ANIMUS` |
| `INSTALL.md` — product name throughout | `Hermes Chat` | `ANIMUS` |
| `installer/install.sh` — banner and messages | `Hermes Chat Installer` | `ANIMUS Installer` |
| `animus.env.example` — comments | `Hermes Chat` | `ANIMUS` |
| `docker-compose.yml` — service name | `hermes-chat` | `animus` |
| `Dockerfile` — labels/comments | `Hermes Chat` | `ANIMUS` |
| `build-release.sh` — zip filename | `hermes-chat-vX.Y.Z.zip` | `animus-vX.Y.Z.zip` |
| Release checklist — env file reference | `hermes-chat.env` | `animus.env` |
| Wizard Step 1 — welcome text | any "Hermes Chat" | `ANIMUS` |
| About modal — app name | any "Hermes Chat" | `ANIMUS` |
| All `console.log`, error messages, log output | any "hermes-chat" | `animus` |
| Python log prefixes in `server.py` | `[hermes-chat]` | `[animus]` |

### 2.3 File and Directory Renaming

| Old name | New name |
|---|---|
| `hermes-chat.env` | `animus.env` |
| `hermes-chat.env.example` | `animus.env.example` |
| `hermes-chat.service` (distro copy) | `animus.service` |
| `restart-after-code-change.sh` | `restart.sh` (update internals to reference ANIMUS paths) |

Note: the original live instance files keep their original names — you are renaming only the files in your working copy.

Replace every user-specific string with a clearly documented environment variable. No exceptions.

---

## 3. Hermes Agent — Full Source Copy

### 3.1 Why a Full Copy, Not a Download

As noted in the Critical section, the owner's Hermes Agent installation may contain customisations — the Cursor CLI patch (§17) being the confirmed example, and potentially others for cron, skills, model enumeration, or streaming behaviour. Shipping ANIMUS with a clean public Hermes Agent would silently break these features for customers.

The `hermes-agent/` directory in the ANIMUS repo **is** the Hermes Agent — copied from the owner's live install, not downloaded from upstream. The installer builds and installs from this copy.

### 3.2 What the Installer Must Do

The `installer/install.sh` must install Hermes Agent **from the bundled `hermes-agent/` directory**, not from pip, npm, or any external registry:

```bash
echo "[ANIMUS] Installing Hermes Agent from bundle..."
cd "$INSTALL_ROOT/hermes-agent"

# If it's a Python package:
pip install --break-system-packages -e .

# If it's a different build system, use whatever is appropriate
# (check for setup.py, pyproject.toml, Makefile, package.json, etc.)
```

After install, always verify:
```bash
hermes --version || { echo "[ANIMUS] ERROR: hermes binary not found after install"; exit 1; }
```

### 3.3 Model Cache Seeding

After Hermes Agent is installed, seed the model cache:
```bash
hermes model list > "$INSTALL_ROOT/animus-chat/data/hermes_models_cache.json" 2>/dev/null \
  || echo "[ANIMUS] Warning: could not seed model cache. Will retry on first launch."
```

This cache is used by the Settings model selector (§5). The app must handle a missing cache gracefully on first launch and re-fetch via `POST /api/models/refresh`.

### 3.4 Keeping `hermes-agent/` Patched

Any future changes to Hermes Agent needed for ANIMUS features (new providers, cron daemon changes, skills system changes) must be made inside `hermes-agent/` in this repo and documented in `docs/hermes-agent-patches.md`. Never modify a customer's separately-installed Hermes Agent at runtime.

---

## 4. First-Run Onboarding Wizard

This is a new feature. When the app is launched and no configuration exists (no `animus.env` with real values, or a `first_run: true` flag in `data/config.json`), the app must redirect the user to a full-screen onboarding wizard before showing the main UI.

### Wizard Steps (implement as a multi-step flow in `app/static/index.html`)

**Step 1 — Welcome**
- Show the **ANIMUS** name, logo, and a one-paragraph description of what ANIMUS is.
- Button: "Get Started"

**Step 2 — Hermes Agent Check**
- The wizard calls a new backend endpoint `GET /api/setup/hermes-check`.
- The server runs `hermes --version` and returns `{ ok: true, version: "x.y.z" }` or `{ ok: false, error: "..." }`.
- If OK: show green checkmark + version, continue.
- If not found: show instructions for installing Hermes Agent, with a "Re-check" button. Block progression until it passes.

**Step 3 — AI Provider API Keys**
- Show a form with a field for each supported provider (OpenAI, Anthropic, Google, etc.).
- Each field has a "Test" button that calls `POST /api/setup/test-key` with `{ provider, key }`. The server attempts a minimal API call and returns pass/fail.
- All fields are optional — the user can skip providers they don't use.
- Keys are written to `hermes-chat.env` on save.

**Step 4 — Model Selection**
- Call `GET /api/setup/models` which returns the parsed `hermes_models_cache.json`.
- Let the user choose their default model from a searchable list grouped by provider.
- Save selection to config.

**Step 5 — Tailscale / Remote Access (Optional)**
- Explain what Tailscale is and why it's useful for mobile access.
- Show a "Skip" option prominently.
- If the user wants to set it up, link to `docs/tailscale.md` (open in new tab).
- Checkbox: "I've set up Tailscale" — saves a flag, does not block.

**Step 6 — Wake Lock (PWA Mobile)**
- Explain the screen wake lock feature.
- Toggle: on/off (default on).
- Saves to config.

**Step 7 — Done**
- Summary of what was configured.
- "Open Hermes Chat" button.
- Sets `first_run: false` in `data/config.json`.

### Wizard Backend Endpoints (add to `setup_wizard/wizard_routes.py`)

```
GET  /api/setup/status          → { first_run: bool }
GET  /api/setup/hermes-check    → { ok: bool, version: str?, error: str? }
POST /api/setup/test-key        → { provider: str, key: str } → { ok: bool, error: str? }
GET  /api/setup/models          → [ { provider, model_id, display_name, description } ]
POST /api/setup/save-config     → { keys: {}, default_model: str, wake_lock: bool } → { ok: bool }
POST /api/setup/complete        → {} → { ok: bool }
```

Mount these routes in `server.py` before the main app routes.

---

## 5. Settings Panel — Full Model Catalogue

### Current Problem (in the source app)
The Settings model selector shows a hardcoded short list: `OpenAI Codex`, `Claude`, `Cursor CLI`. This must be completely replaced.

### New Behaviour

The model selector in Settings must:

1. On first load, fetch `GET /api/models` which returns the full model list from `hermes_models_cache.json`.
2. Display models **grouped by provider** in a searchable dropdown or card list.
3. Show for each model: display name, provider badge, model ID, and (if available from the cache) a short description or context window size.
4. Include a **"Refresh model list"** button that calls `POST /api/models/refresh` — the server runs `hermes model list` again, updates the cache, and returns the new list.
5. For the **Auto** option per provider (already implemented in source): keep this behaviour. When Auto is selected, the chat server picks the best model dynamically. Show "Auto" as the first option in each provider group.
6. When a model is selected and used, show the actual model that ran in the per-message provider badge (already implemented in source — preserve this).

### Backend Endpoints Required

```
GET  /api/models               → full model list from cache
POST /api/models/refresh       → re-runs hermes model list, updates cache, returns new list
```

### `hermes model list` Output Parsing

The server must parse whatever format `hermes model list` outputs. If it outputs a table, parse it into structured JSON:

```json
[
  {
    "provider": "openai",
    "model_id": "gpt-4o",
    "display_name": "GPT-4o",
    "description": "...",
    "context_window": 128000
  }
]
```

Write a robust parser function `parse_hermes_model_list(raw: str) -> list[dict]` that handles the actual output format. If the format is unknown at build time, write the parser to handle both JSON and table formats gracefully, logging a warning if parsing fails.

---

## 6. Environment Variables — Complete Reference

Create `animus.env.example` with every supported variable documented:

```bash
# === ANIMUS Configuration ===
# Copy this file to animus.env and fill in your values.
# Never commit animus.env to git.

# --- Server ---
HOST=0.0.0.0
PORT=3000

# --- Hermes Agent ---
# Path to the hermes binary (leave blank to auto-detect via PATH)
HERMES_BIN=

# --- AI Provider Keys ---
# Add the keys for providers you want to use. Others can be left blank.
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
GOOGLE_API_KEY=
MISTRAL_API_KEY=
GROQ_API_KEY=
COHERE_API_KEY=
TOGETHER_API_KEY=
XAI_API_KEY=
DEEPSEEK_API_KEY=

# --- Defaults ---
DEFAULT_MODEL_PROVIDER=openai
DEFAULT_MODEL_ID=auto

# --- Features ---
WAKE_LOCK_DEFAULT=true
TOKEN_TRACKING_ENABLED=true

# --- Data Storage ---
# Where Hermes Chat stores chats, configs, project data
DATA_DIR=./data
```

All values read from environment must have safe defaults coded into `server.py`. The app must never crash on a missing optional key — it must degrade gracefully and show a warning in the UI.

---

## 7. Docker Support

Create a fully working Docker setup so users can run without touching Python at all.

### `docker/Dockerfile`

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl git build-essential && \
    rm -rf /var/lib/apt/lists/*

# Install Hermes Agent
# TODO: Replace with the correct install command for Hermes Agent
RUN pip install --no-cache-dir hermes-agent  # or COPY + build

# Install Python deps for hermes-chat
COPY hermes-chat/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app source
COPY hermes-chat/ /app/

# Data volume mount point
RUN mkdir -p /data
VOLUME ["/data"]

EXPOSE 3000

ENV DATA_DIR=/data

CMD ["python", "server.py"]
```

### `docker/docker-compose.yml`

```yaml
version: "3.9"

services:
  animus:
    build:
      context: ..
      dockerfile: docker/Dockerfile
    ports:
      - "3000:3000"
    volumes:
      - ./data:/data
    env_file:
      - .env
    restart: unless-stopped
```

### `docker/.env.example`

Copy of the root `.env.example` with Docker-specific notes.

---

## 8. Installer Scripts

### `installer/install.sh` (Linux/macOS)

Must do the following in order:

1. Print a banner: "ANIMUS Installer"
2. Run `installer/preflight.sh` — check for Python 3.10+, pip, git. Exit with clear error if any check fails.
3. Create a `data/` directory.
4. If `animus.env` does not exist, copy `animus.env.example` to `animus.env` and prompt the user to open it or run the in-app wizard.
5. Install Python dependencies: `pip install -r app/requirements.txt`
6. Install Hermes Agent (correct command TBD based on package availability).
7. Run `hermes model list` and save to `app/data/hermes_models_cache.json`.
8. Optionally: offer to install the systemd service (`systemd/animus.service`) — ask yes/no.
9. Start the server: `python app/server.py &`
10. Print the URL: `http://localhost:3001` and instruct user to open it.
11. Print a reminder: "First-run setup wizard will open automatically."

### `installer/preflight.sh`

Check:
- Python 3.10 or later (`python3 --version`)
- pip available
- git available (optional but recommended)
- Port 3000 not already in use (`lsof -i :3000` or `ss -lntp`)
- At least 500MB disk free

Print a clean pass/fail table, exit 1 on any required check failure.

### `systemd/hermes-chat.service`

Generic unit file — no hardcoded paths. Use `%h` for home dir or document that the user must edit `WorkingDirectory` and `ExecStart`:

```ini
[Unit]
Description=ANIMUS
After=network.target

[Service]
Type=simple
WorkingDirectory=%h/animus/app
ExecStart=/usr/bin/python3 server.py
EnvironmentFile=%h/animus/animus.env
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
```

---

## 9. `server.py` — Required Changes from Source

The following changes are mandatory beyond sanitisation:

### 9.1 Mount Setup Wizard Routes
```python
from setup_wizard.wizard_routes import setup_router
app.mount("/api/setup", setup_router)
```

### 9.2 First-Run Redirect
On `GET /`, if `data/config.json` does not exist or contains `"first_run": true`, redirect to `/setup` (a wizard page served from `app/setup.html` or handled as a route in `index.html`).

### 9.3 Model List Endpoint
Add `GET /api/models` and `POST /api/models/refresh` as described in §5.

### 9.4 Dynamic Config Loading
Replace all hardcoded config with `os.getenv()` calls with fallback defaults. Load `animus.env` at startup using `python-dotenv`.

### 9.5 Hermes Binary Resolution
```python
import shutil, os

def get_hermes_bin() -> str:
    env_bin = os.getenv("HERMES_BIN", "").strip()
    if env_bin:
        return env_bin
    found = shutil.which("hermes")
    if found:
        return found
    raise RuntimeError("hermes binary not found. Install Hermes Agent or set HERMES_BIN.")
```

### 9.6 Data Directory
All file I/O (chats, configs, project data, model cache) must use a `DATA_DIR` base path:
```python
DATA_DIR = Path(os.getenv("DATA_DIR", "./data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)
```

### 9.7 Remove All Source-Specific Routes
Audit every route in the source `server.py` for any that reference specific project names, user paths, or personal integrations. Remove or generalise them.

---

## 10. `app/index.html` — Required UI Changes

### 10.1 Remove All Personal References and Apply ANIMUS Branding
- Remove or replace any hardcoded project names, user names, or workspace references.
- The app name is **ANIMUS** everywhere — title bar, headings, splash screen, toast messages, loading states, error messages.
- The source app used "ANIMUS" in some places and "Hermes Chat" in others — standardise all of it to **ANIMUS**.
- Reset the PWA cache bucket: `animus-v1`.

### 10.2 App Name Configurable from Settings
Add a "Display Name" field in Settings → Appearance so users can personalise their instance (e.g. rename it to their own brand). Persist to `localStorage` and `data/config.json`. Use this name in the title bar and manifest (via a dynamic manifest endpoint). Default value must be **ANIMUS**.

### 10.3 Model Selector Rewrite
As described in §5 — remove hardcoded model list. Replace with dynamic fetch from `/api/models`. Show a loading state while fetching. Show an error state with a "Retry" button if the fetch fails.

### 10.4 First-Run Wizard
Implement the wizard as a full-screen overlay in `index.html` (not a separate page) triggered when `first_run` is true. All wizard steps are in-app — no external navigation.

### 10.5 Onboarding Tooltip Layer
After the wizard completes, on the user's first visit to each main section (Chat, Workspace, Plan, Settings), show a one-time dismissable tooltip explaining what that section does. Store dismissed state in `localStorage`.

### 10.6 "About ANIMUS" Modal
Add a small info button (or entry in Settings) that opens an About modal showing:
- **ANIMUS** version (from `VERSION` file, exposed at `GET /api/version`)
- Hermes Agent version (from `hermes --version`)
- Link to docs
- A "Check for updates" hint (link to their Gumroad page)

---

## 11. PWA & Manifest

### `app/static/manifest.json`
```json
{
  "name": "ANIMUS",
  "short_name": "ANIMUS",
  "description": "Your personal AI command center, powered by Hermes Agent.",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#1a1a2e",
  "theme_color": "#6c63ff",
  "icons": [
    { "src": "/icon-192.png", "sizes": "192x192", "type": "image/png" },
    { "src": "/icon-512.png", "sizes": "512x512", "type": "image/png" }
  ]
}
```

### `app/static/sw.js`
- Cache name must be `animus-v1`.
- Remove any personal asset URLs.
- Ensure the service worker correctly handles `/api/*` by passing through to network (not caching API responses).

---

## 12. Documentation to Write

### `README.md`
Must contain:
1. What **ANIMUS** is (2–3 sentences).
2. Screenshot or GIF (placeholder `docs/screenshots/` reference).
3. Prerequisites list.
4. Quick start: `./installer/install.sh` → open `http://localhost:3001`.
5. Docker alternative: `docker compose up`.
6. Link to `INSTALL.md` for full details.
7. Feature list (bullet points).
8. Link to docs directory.

### `INSTALL.md`
Must contain:
1. System requirements (OS, Python version, disk space, ports).
2. Full manual install steps.
3. Systemd setup (`animus.service`).
4. Tailscale/remote access setup.
5. Environment variable reference (all vars from §6, referencing `animus.env`).
6. Troubleshooting section covering:
   - Port conflict with an existing service
   - `hermes` binary not found
   - API key test fails
   - PWA icon not updating (cache busting steps for `animus-v1`)
   - Models list empty

### `docs/hermes-agent-patches.md`
This is the most important doc to write **first**, before any code changes. It records exactly what the owner's Hermes Agent differs from upstream. Format:

```markdown
# Hermes Agent — ANIMUS Patch Record

## How to read this doc
Each section is one change from upstream Hermes Agent. For each: what file was changed,
what the change does, and why it exists.

## Patch 1 — Cursor CLI provider
File(s): providers/cursor/...
What it does: Adds Cursor CLI as a model provider using cursor login for auth.
Why: Allows ANIMUS users with Cursor installed to use it as an AI backend without an API key.

## Patch 2 — (discovered during diff)
...
```

This document is the maintenance guide for future ANIMUS updates. Without it, the next developer has no idea what they're inheriting.

### `docs/models.md`
Explain:
- How Hermes Agent model providers work.
- How to add a new provider API key.
- What "Auto" model selection does.
- How to refresh the model cache.

### `docs/tailscale.md`
(Can be adapted from the source `TAILSCALE-SERVE.md` with personal references removed.)

---

## 13. Gumroad Delivery Package

After all code is complete and tested, create the deliverable:

### `build-release.sh`
A script that:
1. Runs a final sanitisation check (grep for known personal strings — fail if found).
2. Also checks that no instance of "Hermes Chat" (the old product name) appears in any user-facing file — fail if found.
3. Verifies the installer runs cleanly in a temporary directory.
4. Generates the release zip: `animus-vX.Y.Z.zip` containing everything in `animus/` excluding `.git/`, `__pycache__/`, `*.pyc`, `data/`, and `animus.env`.
5. Prints a release checklist.

### Release Checklist (print at end of build script)
```
ANIMUS release checklist:
[ ] animus.env is NOT in the zip
[ ] data/ directory is NOT in the zip
[ ] No personal API keys in any file
[ ] No personal hostnames or IPs in any file
[ ] No "Hermes Chat" in any user-facing file (grep -r "Hermes Chat" app/)
[ ] installer/install.sh is executable (chmod +x)
[ ] README.md references correct version
[ ] VERSION file updated
[ ] Screenshots in docs/screenshots/ are current
[ ] Tested on clean machine or VM
[ ] Docker build passes
[ ] PWA installs on Android Chrome and shows "ANIMUS" as app name
```

---

## 14. Version File

Create `VERSION` at the repo root:
```
1.0.0
```

Expose via server:
```python
@app.get("/api/version")
async def get_version():
    version = Path("../VERSION").read_text().strip()
    hermes_ver = subprocess.check_output([get_hermes_bin(), "--version"]).decode().strip()
    return {"app": version, "hermes": hermes_ver}
```

---

## 17. Cursor CLI — Model Provider Patch for Hermes Agent

### 17.1 Background

The owner has developed a custom patch to Hermes Agent that adds **Cursor CLI** as a model provider. This means users who have Cursor installed and authenticated can use Cursor's underlying AI models through ANIMUS without needing a separate API key — authentication is handled entirely via `cursor login`. This patch must be carried forward into the ANIMUS bundle.

### 17.2 What the Patch Does

The Cursor CLI provider works as follows:

1. **Authentication** — Uses `cursor login` (the Cursor CLI auth command) instead of an API key. The patch checks whether the user is authenticated by running `cursor whoami` (or equivalent) and inspecting the exit code and output. There is no API key to store in `animus.env`.
2. **Inference** — Sends prompts to Cursor's underlying model by invoking the Cursor CLI in a subprocess with the appropriate flags, capturing stdout as the model response.
3. **Model listing** — Exposes available Cursor models (whatever `cursor model list` or equivalent returns) so they appear in ANIMUS's model selector alongside other providers.
4. **Streaming** — If the Cursor CLI supports streaming output (e.g. `--stream` flag), the patch pipes stdout line-by-line back to the ANIMUS streaming response. If not, it returns the full response as a single block.

### 17.3 Finding the Patch in the Source

Before writing anything, locate the patch in the live instance source. Look in:

- `server.py` — for any route, function, or subprocess call referencing `cursor`
- Any utility or helper module in the repo that imports or wraps CLI calls
- The Hermes Agent installation itself (check `hermes agent list` or the Hermes Agent plugin/provider directory) for a Cursor provider file

**Do not guess the implementation.** Read the actual patch code from the source first. Note exactly:
- How it invokes the Cursor CLI (the exact command, flags, env vars)
- How it handles auth failure (user not logged in)
- How it maps Cursor model names to the ANIMUS model selector display names
- How streaming is handled (or whether it falls back to blocking)
- Any error handling for when the Cursor binary is not installed

### 17.4 Carrying the Patch Forward

Once you have read and understood the patch from the source:

1. **Copy the patch files** into the ANIMUS bundle. If it lives inside the Hermes Agent installation, document clearly where it must be placed after Hermes Agent is installed on a new machine.
2. **Add a Cursor CLI check to the installer** (`installer/install.sh`). This check is informational only — Cursor is optional, so do not block installation if it is absent. Print a notice:
   ```
   [optional] Cursor CLI not found. If you want to use Cursor as a model provider,
   install Cursor from https://cursor.sh and run 'cursor login'.
   ```
3. **Add a Cursor section to the onboarding wizard** (Step 3, alongside the API key fields). It should:
   - Call `GET /api/setup/cursor-check` which runs `cursor whoami` server-side.
   - If authenticated: show a green checkmark and the logged-in account name.
   - If not installed: show a grey "Not installed" badge with a link to cursor.sh.
   - If installed but not logged in: show a yellow "Not logged in" badge with a "Login" button that instructs the user to run `cursor login` in their terminal, and a "Re-check" button to re-run the check.
   - The Cursor section has a "Skip" option — it is never required.
4. **Add `GET /api/setup/cursor-check` backend endpoint** to `setup_wizard/wizard_routes.py`:
   ```python
   @router.get("/cursor-check")
   async def cursor_check():
       cursor_bin = shutil.which("cursor")
       if not cursor_bin:
           return {"status": "not_installed"}
       try:
           result = subprocess.run(
               [cursor_bin, "whoami"],  # adjust to actual auth check command
               capture_output=True, text=True, timeout=10
           )
           if result.returncode == 0:
               account = result.stdout.strip()
               return {"status": "authenticated", "account": account}
           else:
               return {"status": "not_logged_in"}
       except subprocess.TimeoutExpired:
           return {"status": "timeout"}
   ```
   Adjust the exact command based on what you find in the actual patch.
5. **Surface Cursor in the model selector** — Cursor models must appear in the ANIMUS model dropdown grouped under a "Cursor" provider section, with a lock/auth indicator if the user is not logged in.
6. **Add to `docs/models.md`** — a Cursor section explaining: what Cursor CLI is, how to install it, how to run `cursor login`, and how to verify it's working in ANIMUS.

### 17.5 Patch Integrity Rule

The Cursor CLI patch must behave identically in ANIMUS to how it behaves in the live instance. Do not simplify, re-implement from scratch, or change the invocation method. Copy the working code, adapt paths and naming to ANIMUS conventions, and verify it still works end-to-end.

---

## 18. Cron Tab — Hardened Integration with Hermes Agent Cron

### 18.1 Current State (What Exists)

The ANIMUS Cron tab shows scheduled jobs and allows users to create, edit, and delete them. In the current live instance, this integration has known fragility — cron jobs created via the UI don't always register correctly with the Hermes Agent cron system, and updates made outside the UI aren't reliably reflected back.

### 18.2 Hardening Requirements

The Cron tab in ANIMUS must be the **single authoritative interface** for Hermes Agent cron jobs. All reads and writes must go through Hermes Agent's cron commands — never by directly editing crontab files or any intermediate file that Hermes Agent also writes. The integration must be hardened as follows:

### 18.3 Backend — Cron API Layer (`app/cron_routes.py`)

Create a dedicated cron route module and mount it at `/api/cron`. All cron operations must go through this layer. Never call cron commands directly from `index.html` JavaScript.

**Required endpoints:**

```
GET  /api/cron/list          → Run: hermes cron list --format json
                               Returns: [ { id, name, schedule, command, last_run, next_run, status } ]

POST /api/cron/create        → Body: { name, schedule, command, project? }
                               Run: hermes cron add <args>
                               Returns: { ok: bool, id: str, error: str? }

PUT  /api/cron/update/{id}   → Body: { name?, schedule?, command?, enabled? }
                               Run: hermes cron update <id> <args>
                               Returns: { ok: bool, error: str? }

DELETE /api/cron/delete/{id} → Run: hermes cron remove <id>
                               Returns: { ok: bool, error: str? }

POST /api/cron/run/{id}      → Run: hermes cron run <id> (manual trigger)
                               Returns: { ok: bool, output: str, error: str? }

GET  /api/cron/logs/{id}     → Run: hermes cron logs <id> --lines 50
                               Returns: { lines: [ { timestamp, message, level } ] }

GET  /api/cron/status        → Run: hermes cron status (daemon health check)
                               Returns: { running: bool, job_count: int, next_run: str? }
```

**Implementation rules for every endpoint:**

- Always use `subprocess.run()` with `capture_output=True`, a timeout (default 30s), and explicit error handling.
- Parse the Hermes Agent command output — never assume success based on exit code alone. Check both exit code AND stdout/stderr content.
- If a command times out, return `{ ok: false, error: "Command timed out" }` — never leave the request hanging.
- Log every cron operation (create/update/delete/run) to `data/cron_audit.log` with timestamp, operation, job id, and result.
- Never write directly to the system crontab. All operations go through `hermes cron` commands only.

**Subprocess pattern to use for all cron commands:**
```python
import subprocess, shutil, logging
from pathlib import Path

AUDIT_LOG = Path(os.getenv("DATA_DIR", "./data")) / "cron_audit.log"

def run_hermes_cron(args: list[str], timeout: int = 30) -> dict:
    hermes = get_hermes_bin()
    cmd = [hermes, "cron"] + args
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        success = result.returncode == 0
        return {
            "ok": success,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
            "returncode": result.returncode
        }
    except subprocess.TimeoutExpired:
        logging.error(f"hermes cron {args} timed out after {timeout}s")
        return {"ok": False, "stdout": "", "stderr": "Timed out", "returncode": -1}
    except FileNotFoundError:
        return {"ok": False, "stdout": "", "stderr": "hermes binary not found", "returncode": -1}
```

### 18.4 Frontend — Cron Tab Hardening

The Cron tab UI must reflect the following contract with the backend:

**Reading state:**
- On tab open and on every manual refresh, call `GET /api/cron/list` and render from that response. Never use locally cached job state as the source of truth — always re-fetch from Hermes Agent.
- Call `GET /api/cron/status` on tab open and show a visible daemon health indicator (green "Running" / red "Stopped") at the top of the tab.
- If `status.running` is false, show a warning banner: "Hermes Agent cron daemon is not running. Jobs will not execute." with a button to attempt a restart via `POST /api/hermes/restart-cron` (add this endpoint to restart the cron daemon).
- Auto-refresh the job list every 60 seconds while the Cron tab is active. Stop the refresh timer when the user navigates away.

**Creating a job:**
- The create form must validate the cron schedule string before submitting (client-side cron expression validation — use a small JS library or a simple regex validator, no external CDN required, inline it).
- After `POST /api/cron/create` returns `{ ok: true }`, immediately call `GET /api/cron/list` to refresh — do not optimistically add the job to the local list.
- If the create call returns `{ ok: false }`, show the exact error from Hermes Agent in a visible error state on the form.

**Editing a job:**
- Send a `PUT /api/cron/update/{id}` with only the changed fields.
- On success, refresh the full list via `GET /api/cron/list`.
- On failure, show the error and do not update the local display.

**Deleting a job:**
- Show a confirmation dialog before calling `DELETE /api/cron/delete/{id}`.
- On success, refresh the full list.

**Running a job manually:**
- Call `POST /api/cron/run/{id}`.
- Show a loading state on the job row while running.
- When the response arrives, show a toast with the output or error.
- Show a log viewer panel that calls `GET /api/cron/logs/{id}` and displays the last 50 lines.

**Cron output routing (history):**
- Cron job outputs that are posted back to ANIMUS (as new chats under their project) must continue to work. Audit how this is implemented in the source and ensure the route it posts to (`/api/chats` or similar) is preserved in the ANIMUS backend.
- If cron jobs were previously routing to a personal Slack instead of ANIMUS, fix this in the ANIMUS copy so all cron output goes to ANIMUS chat history only.

### 18.5 Cron Audit Log

Every mutating cron operation must be logged to `data/cron_audit.log`:
```
2026-04-29T14:32:01Z CREATE  job_id=abc123  name="Daily summary"  schedule="0 9 * * *"  result=ok
2026-04-29T14:35:10Z RUN     job_id=abc123  triggered_by=manual   result=ok  duration=4.2s
2026-04-29T15:00:00Z RUN     job_id=abc123  triggered_by=schedule  result=error  error="Command exited 1"
2026-04-29T16:10:44Z DELETE  job_id=abc123  result=ok
```

Expose recent audit log entries via `GET /api/cron/audit?limit=100` so the UI can display them in a log panel.

---

## 19. Skills Tab — Hardened Integration with Hermes Agent

### 19.1 Current State (What Exists)

The ANIMUS Skills tab shows installed skills and allows the user to manage them. In the live instance, skill operations (install, update, remove) may call Hermes Agent commands but without consistent error handling, status feedback, or sync verification.

### 19.2 Hardening Requirements

The Skills tab in ANIMUS must be the **single authoritative interface** for managing Hermes Agent skills. Every skill operation — list, install, update, remove, enable, disable — must go through Hermes Agent CLI commands. ANIMUS must never directly manipulate skill files on disk; it must always delegate to Hermes Agent and verify the result.

### 19.3 Backend — Skills API Layer (`app/skills_routes.py`)

Create a dedicated skills route module and mount it at `/api/skills`. 

**Required endpoints:**

```
GET  /api/skills/list           → Run: hermes skill list --format json
                                  Returns: [ { id, name, version, description, enabled, source, last_updated } ]

GET  /api/skills/detail/{id}    → Run: hermes skill info <id>
                                  Returns: { id, name, version, description, enabled, source,
                                             config_schema, last_updated, readme? }

POST /api/skills/install        → Body: { source: str }  (URL, path, or registry name)
                                  Run: hermes skill install <source>
                                  Returns: { ok: bool, id: str?, error: str? }

POST /api/skills/update/{id}    → Run: hermes skill update <id>
                                  Returns: { ok: bool, version_before: str, version_after: str, error: str? }

POST /api/skills/update-all     → Run: hermes skill update --all
                                  Returns: { ok: bool, updated: [ {id, version_before, version_after} ], errors: [] }

DELETE /api/skills/remove/{id}  → Run: hermes skill remove <id>
                                  Returns: { ok: bool, error: str? }

POST /api/skills/enable/{id}    → Run: hermes skill enable <id>
                                  Returns: { ok: bool, error: str? }

POST /api/skills/disable/{id}   → Run: hermes skill disable <id>
                                  Returns: { ok: bool, error: str? }

GET  /api/skills/updates-available → Run: hermes skill check-updates
                                      Returns: [ { id, name, current_version, latest_version } ]
```

**Implementation rules for every endpoint:**

- Use the same `run_hermes_cron` pattern from §18.3 but adapted for skills commands. Extract a shared `run_hermes(subcommand: str, args: list[str], timeout: int)` helper used by both cron and skills routes.
- Parse structured output from Hermes Agent where possible (`--format json` flag). If Hermes Agent doesn't support JSON output for a command, parse the text output into structured data — write a dedicated parser function for each command, not ad-hoc string splitting inline.
- All install, update, and remove operations must run with a longer timeout (120s) since they may involve network operations.
- Log all mutating operations to `data/skills_audit.log` in the same format as the cron audit log.

**Shared Hermes runner utility (`app/hermes_runner.py`):**

Extract the shared subprocess pattern into its own module since both cron and skills (and potentially other future features) need it:

```python
import subprocess, shutil, os, logging
from pathlib import Path

def get_hermes_bin() -> str:
    env_bin = os.getenv("HERMES_BIN", "").strip()
    if env_bin:
        return env_bin
    found = shutil.which("hermes")
    if found:
        return found
    raise RuntimeError("hermes binary not found. Set HERMES_BIN or ensure hermes is in PATH.")

def run_hermes(args: list[str], timeout: int = 30) -> dict:
    """Run a hermes CLI command and return structured result."""
    try:
        result = subprocess.run(
            [get_hermes_bin()] + args,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return {
            "ok": result.returncode == 0,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
            "returncode": result.returncode
        }
    except subprocess.TimeoutExpired:
        logging.error(f"hermes {args} timed out after {timeout}s")
        return {"ok": False, "stdout": "", "stderr": f"Timed out after {timeout}s", "returncode": -1}
    except FileNotFoundError:
        return {"ok": False, "stdout": "", "stderr": "hermes binary not found", "returncode": -1}
    except Exception as e:
        return {"ok": False, "stdout": "", "stderr": str(e), "returncode": -1}
```

Import `run_hermes` and `get_hermes_bin` from `hermes_runner` in all route modules. Never duplicate this logic.

### 19.4 Frontend — Skills Tab Hardening

**Listing skills:**
- On tab open, call `GET /api/skills/list` and render from the response.
- Group skills visually by `enabled` status: active skills at the top, disabled below.
- Show for each skill: name, version, description (truncated to 2 lines), enabled/disabled badge, source (URL or registry), last updated date.
- Show a "Check for updates" button at the top that calls `GET /api/skills/updates-available` and badges any skills with available updates.

**Installing a skill:**
- Provide an "Install Skill" button that opens a modal with a single text field: source URL, local path, or registry name.
- Call `POST /api/skills/install` and show a progress indicator — skill install may take time.
- On success: refresh the full list via `GET /api/skills/list`. Show a success toast with the installed skill name and version.
- On failure: show the exact error from Hermes Agent in the modal.

**Updating a skill:**
- Each skill row has an "Update" button (highlighted if an update is available).
- Call `POST /api/skills/update/{id}`.
- On success: show before/after version in a toast. Refresh the list.
- "Update All" button calls `POST /api/skills/update-all` and shows a summary of what was updated and any errors.

**Enabling / Disabling:**
- Each skill row has a toggle. Toggle state changes call `POST /api/skills/enable/{id}` or `POST /api/skills/disable/{id}`.
- On failure, revert the toggle and show an error toast.
- Never optimistically change the toggle — wait for the API to confirm before updating the UI.

**Removing a skill:**
- Show a confirmation dialog with the skill name before calling `DELETE /api/skills/remove/{id}`.
- On success, refresh the full list.

**Skill detail panel:**
- Clicking a skill opens a side panel or modal showing full details from `GET /api/skills/detail/{id}`.
- If the skill has a `readme` field, render it as markdown in the detail panel.
- If the skill has a `config_schema`, show the configuration fields (future enhancement — at minimum show the schema as formatted JSON).

### 19.5 Onboarding Wizard — Skills Step

Add a Skills step to the onboarding wizard (after model selection, before Tailscale):

**Step 4.5 — Skills**
- Call `GET /api/skills/list` and show installed skills count.
- If zero skills are installed: show a message explaining what skills do and suggesting the user visit the Skills tab after setup to install some.
- If skills are installed: show a list of installed skill names and a "All up to date" / "Updates available" status from `GET /api/skills/updates-available`.
- Button: "Continue" (this step is informational — no action required to proceed).

### 19.6 Skills Audit Log

Log all mutating skill operations to `data/skills_audit.log`:
```
2026-04-29T14:32:01Z INSTALL  source="https://..."  skill_id=my-skill  version=1.2.0  result=ok  duration=8.4s
2026-04-29T15:10:00Z UPDATE   skill_id=my-skill  version_before=1.2.0  version_after=1.3.0  result=ok
2026-04-29T16:00:00Z DISABLE  skill_id=my-skill  result=ok
2026-04-29T17:00:00Z REMOVE   skill_id=my-skill  result=ok
```

Expose via `GET /api/skills/audit?limit=100`.

---

## 20. General Integration Principles — ANIMUS as the Control Plane

Sections 17, 18, and 19 implement the same core principle: **ANIMUS is the single control plane for everything Hermes Agent does.** Users should never need to open a terminal to manage their AI system after initial setup.

The following rules apply across all integrations:

**1. All Hermes Agent operations go through the ANIMUS backend.**
The browser never calls Hermes Agent directly. The `index.html` frontend calls ANIMUS API endpoints. The ANIMUS server calls Hermes Agent via subprocess. This is the only permitted call chain:
```
User (browser) → ANIMUS /api/... → hermes CLI → result → ANIMUS → browser
```

**2. Every operation has explicit error handling visible to the user.**
No silent failures. If a Hermes Agent command fails, the user must see: what failed, why it failed (exact error from Hermes Agent), and what they can do about it.

**3. State is always read from Hermes Agent, never from ANIMUS's local cache as truth.**
ANIMUS may cache data for performance (e.g. model list), but for operational state (cron jobs, skill list, Cursor auth) the source of truth is always a live query to Hermes Agent. Stale UI state must not persist across page loads.

**4. Audit logs exist for all mutating operations.**
Cron (§18.5), skills (§19.6), and any future operational feature must write to an audit log. These logs must be readable from within ANIMUS (Settings → Logs or similar).

**5. The `hermes_runner.py` module is the only place subprocess calls to Hermes Agent are made.**
All routes import from it. This makes it trivial to add logging, timeouts, or retry logic in one place.

---

## 15. Acceptance Criteria (Updated)

The build is complete when ALL of the following pass:

**Monorepo integrity:**
- [ ] `hermes-agent/` directory exists in the repo and contains a complete copy of the owner's live Hermes Agent.
- [ ] `docs/hermes-agent-patches.md` exists and documents at minimum the Cursor CLI patch.
- [ ] `installer/install.sh` installs Hermes Agent from `hermes-agent/` in the bundle — not from an external registry.
- [ ] After running the installer, `hermes --version` matches the version in the bundled `hermes-agent/`.
- [ ] The Cursor CLI patch is present and functional in the installed `hermes-agent/`.

**Core:**
- [ ] `./installer/install.sh` runs to completion on a clean Ubuntu 22.04 or macOS 14 machine with no prior Hermes install.
- [ ] Opening `http://localhost:3001` on a fresh install shows the ANIMUS onboarding wizard.
- [ ] Completing the wizard results in a fully functional chat interface branded **ANIMUS**.
- [ ] The browser tab, PWA install prompt, and app title all read **ANIMUS**.
- [ ] `docker compose up` starts the app successfully.
- [ ] The PWA installs on Android Chrome and shows **ANIMUS** as the app name.

**Sanitisation:**
- [ ] `grep -r "Hermes Chat" app/static/` returns no results.
- [ ] `grep -r "5206" .` returns no results.
- [ ] `grep -r "tail1a5964" .` returns no results.
- [ ] `grep -r "/home/sketch/hermes/hermes-chat" .` returns no results in the release zip.
- [ ] `grep -r "/home/sketch/hermes/hermes-agent" .` returns no results in the release zip.
- [ ] `grep -r "/home/sketch" .` returns no results in the release zip.
- [ ] `grep -r "hermes-chat-v" app/static/sw.js` returns `animus-v1` only.

**Model selection:**
- [ ] The Settings model selector shows the full list from `hermes model list` grouped by provider.
- [ ] Cursor CLI appears as a provider in the model selector if Cursor is installed and authenticated.
- [ ] If Cursor is not installed, the model selector shows a "Not installed" state for the Cursor section rather than crashing.
- [ ] The onboarding wizard Cursor check correctly detects: not installed / installed but not logged in / authenticated.
- [ ] Selecting a Cursor model and sending a chat message returns a valid response (requires Cursor to be installed and authenticated on the test machine).

**Cron tab:**
- [ ] `GET /api/cron/list` returns the current job list from Hermes Agent.
- [ ] Creating a job via the ANIMUS UI causes the job to appear in `hermes cron list` in the terminal.
- [ ] Updating a job via the UI causes the change to be reflected in `hermes cron list`.
- [ ] Deleting a job via the UI removes it from `hermes cron list`.
- [ ] Manually running a job via the UI returns output.
- [ ] The cron daemon health indicator correctly shows "Running" / "Stopped".
- [ ] If `hermes cron` commands fail, the UI shows the error — it does not crash or silently fail.
- [ ] `data/cron_audit.log` is written to on every create/update/delete/run operation.

**Skills tab:**
- [ ] `GET /api/skills/list` returns the current skill list from Hermes Agent.
- [ ] Installing a skill via the ANIMUS UI causes it to appear in `hermes skill list` in the terminal.
- [ ] Updating a skill via the UI updates its version in `hermes skill list`.
- [ ] Removing a skill via the UI removes it from `hermes skill list`.
- [ ] Enabling/disabling a skill via the UI toggle is reflected in `hermes skill list`.
- [ ] If `hermes skill` commands fail, the UI shows the error.
- [ ] `data/skills_audit.log` is written to on every install/update/remove/enable/disable operation.

**Integration principle:**
- [ ] No ANIMUS frontend code calls Hermes Agent directly — all calls go through ANIMUS `/api/` endpoints.
- [ ] `hermes_runner.py` is the only file that imports `subprocess` and calls the hermes binary.
- [ ] `build-release.sh` completes without errors and produces `animus-v1.0.0.zip`.
- [ ] The zip is under 50MB.

---

## 16. Implementation Order (Updated)

Execute in this order to avoid rework:

1. **Copy both live sources into the monorepo** — run the exact commands in the Critical section. Both paths are confirmed: `hermes-chat` from `/home/sketch/hermes/hermes-chat`, Hermes Agent from `/home/sketch/hermes/hermes-agent`. Verify the copy with `ls` and `du` before proceeding.
2. **Diff Hermes Agent against upstream** — document all customisations in `docs/hermes-agent-patches.md` (Critical §, Step 2). Do not skip this — it is your change record.
4. **Locate the Cursor CLI patch** within `hermes-agent/` and read it fully before writing anything (§17.3).
5. **Run sanitisation + rename pass** on `animus-chat/` — remove all personal data, rename "Hermes Chat" to "ANIMUS" throughout (§2).
6. **Write `hermes_runner.py`** shared utility in `animus-chat/` (§19.3) — everything else depends on this.
7. **Write `animus.env.example`** and config loading in `server.py` (§6, §9.4).
8. **Update the model list** — wire up `hermes model list` parsing from the bundled agent (§3.3, §5 backend).
9. **Write `cron_routes.py`** and mount in `server.py` (§18.3).
10. **Write `skills_routes.py`** and mount in `server.py` (§19.3).
11. **Carry forward the Cursor CLI patch** — ensure it works from `hermes-agent/`, add `cursor-check` wizard endpoint (§17.4).
12. **Write setup wizard backend routes** including Cursor and skills steps (§4, §17.4, §19.5).
13. **Write remaining `server.py` changes** (§9).
14. **Build the UI** — ANIMUS branding, model selector rewrite, hardened cron tab, hardened skills tab, first-run wizard, onboarding tooltips (§2.2, §5, §10, §18.4, §19.4).
15. **Write installer scripts** — install both agent and chat from the monorepo (§8, §3.2).
16. **Write Docker setup** — both services in docker-compose (§7).
17. **Write all documentation** — including `docs/hermes-agent-patches.md`, Cursor section, models, Tailscale (§12).
18. **Write `build-release.sh`** and run all acceptance criteria (§13, §15).

---

*End of directive. All sections are required. Do not skip sanitisation, integration hardening, or acceptance criteria.*
When the north star changes (product, audience, or definition of success), update this file before deep implementation continues.



## ANIMUS — Phase 2 Build Directive

**Follows from:** Phase 1 (monorepo scaffolding, backend API modules, branding pass)
**Working directory:** `/home/sketch/animus/` — all work stays here, live instances untouched
**Port:** ANIMUS runs on 3001. Live hermes-chat owns 3000. Do not touch it.

---

## Status Coming In

Phase 1 delivered:
- Monorepo with `animus-chat/` + `hermes-agent/` copied in
- New backend modules: `hermes_runner.py`, `cron_routes.py`, `skills_routes.py`, `wizard_routes.py` — all mounted in `server.py`
- Branding pass: `animus-v1` cache, "ANIMUS" in index.html, env files cleaned
- Release zip builds at ~50MB

**What is not done and must be completed in this phase:**

| Area | Gap |
|---|---|
| UI | Wizard overlay, model selector, cron tab, skills tab still call legacy API paths |
| Backend | `server.py` still uses raw `subprocess` outside of the new route files |
| Skills | `enable`/`disable` endpoints return 501 |
| Cron | `POST /api/hermes/restart-cron` does not exist |
| Docker | Added but never built or verified |
| `server.py` legacy paths | `/api/chat-models`, `/api/cron/jobs`, `/api/skills` still exist alongside new routes — must be removed or redirected |

Work in this phase in the order listed below. Do not skip ahead.

---

## Phase 2 — Task 1: Migrate `server.py` subprocess calls to `hermes_runner.py`

### Why first
Every other task depends on the backend being consistent. The §20 rule — "hermes_runner.py is the only file that calls subprocess on the hermes binary" — must be true before UI work begins, otherwise you end up with two code paths doing the same thing and errors from one path don't surface in the audit logs from the other.

### What to do

1. Open `server.py`. Find every `subprocess.run`, `subprocess.Popen`, `subprocess.call`, or `os.system` call that invokes the `hermes` binary.
2. For each one, replace it with a call to `run_hermes()` from `hermes_runner.py`.
3. The only `subprocess` calls permitted to remain in `server.py` after this task are ones that call something **other than hermes** (e.g. system utilities). Add a comment above each remaining one explaining why it doesn't go through `hermes_runner`.
4. Verify: `grep -n "subprocess" animus-chat/server.py` should return zero lines calling hermes, or lines with the exemption comment.
5. Run `cd animus-chat && .venv/bin/python -c "import server"` — must still succeed.

### Subprocess wrapper reminder

```python
# hermes_runner.py — already exists, use it exactly as written
from hermes_runner import run_hermes, get_hermes_bin
```

Do not add a second copy of the runner logic anywhere. Import it.

---

## Phase 2 — Task 2: Remove Legacy API Routes

### What to do

The following legacy routes exist in `server.py` from the original hermes-chat code. They must be **removed** (not redirected — removed) because the new typed route files replace them and having both active causes confusion about which path the UI is actually hitting:

- `GET /api/chat-models` → replaced by `GET /api/models`
- `GET /api/cron/jobs` → replaced by `GET /api/cron/list`
- Any legacy `/api/skills` routes that predate `skills_routes.py`
- Any legacy `/api/setup` routes that predate `wizard_routes.py`

**Process for each legacy route:**
1. Confirm the new equivalent endpoint exists and returns equivalent data.
2. Search `animus-chat/static/index.html` for every fetch/call to the legacy path.
3. Update the frontend call to use the new path (Task 3 will do this comprehensively — flag the path now, fix it in Task 3).
4. Delete the legacy route from `server.py`.
5. Re-run `cd animus-chat && .venv/bin/python -c "import server"` (or `python3 -c "import server"`) after each deletion.

Do not leave commented-out legacy routes in the file — delete them cleanly.

---

## Phase 2 — Task 3: Wire the UI to the New API Paths

This is the largest task. Every data fetch in `animus-chat/static/index.html` must call the correct new API path. Go through the file systematically — search for every `fetch(` call and every `api/` string.

### 3.1 Model Selector

**Current state:** Settings model selector calls `/api/chat-models` (legacy) and renders a hardcoded short list.

**Required state:**

```javascript
// On Settings tab open AND on "Refresh" button click:
async function loadModelList() {
  const res = await fetch('/api/models');
  const models = await res.json();   // [ { provider, model_id, display_name, description } ]
  renderModelSelector(models);
}

function renderModelSelector(models) {
  // Group by provider
  const byProvider = {};
  for (const m of models) {
    if (!byProvider[m.provider]) byProvider[m.provider] = [];
    byProvider[m.provider].push(m);
  }
  // Render a <optgroup label="provider"> per provider
  // with an "Auto" option as the first item in each group
  // Show model_id as value, display_name as label
  // If description exists, show it as a title tooltip on the option
}
```

- Show a loading spinner while the fetch is in-flight.
- Show an error state with a "Retry" button if the fetch fails or returns non-200.
- Add a "Refresh model list" button near the selector. On click: call `POST /api/models/refresh`, then call `GET /api/models`, then re-render.
- When a model is selected and saved, persist to `localStorage` key `animus_selected_model` as `{ provider, model_id }`.
- When sending a chat message, read from `localStorage` and send the selected model to the backend.
- The per-message provider badge at the bottom of each assistant message must show the model that actually ran — read this from the response metadata, not from the selection.

### 3.2 Cron Tab

**Current state:** Cron tab calls `/api/cron/jobs` (legacy).

**Required state — replace every cron fetch with the new paths:**

| Action | Old path | New path |
|---|---|---|
| List jobs | `/api/cron/jobs` | `GET /api/cron/list` |
| Create job | `/api/cron/create` (if existed) | `POST /api/cron/create` |
| Update job | any legacy path | `PUT /api/cron/update/{id}` |
| Delete job | any legacy path | `DELETE /api/cron/delete/{id}` |
| Run manually | any legacy path | `POST /api/cron/run/{id}` |
| View logs | (may not have existed) | `GET /api/cron/logs/{id}` |
| Daemon status | (may not have existed) | `GET /api/cron/status` |

**UI hardening to add (these are new behaviours, not just path changes):**

- On Cron tab open: call `GET /api/cron/status` first. If `status.running` is false, show a red banner: "Cron daemon is not running — scheduled jobs will not execute." with a "Restart" button that calls `POST /api/hermes/restart-cron` (add this endpoint — Task 4).
- Call `GET /api/cron/list` on tab open and every 60 seconds while the tab is active. Stop polling when the user leaves the tab.
- After every create/update/delete, call `GET /api/cron/list` to refresh — never optimistically update local state.
- Cron schedule field: add inline client-side cron expression validation. A valid cron expression has 5 space-separated fields. Reject on submit if invalid and show: "Invalid schedule — expected format: minute hour day month weekday (e.g. 0 9 * * 1)".
- Each job row: show a "Logs" button that opens a panel fetching `GET /api/cron/logs/{id}` and displaying the last 50 lines in a scrollable pre-formatted block.
- Manual run button: show a spinner on the row while `POST /api/cron/run/{id}` is in-flight. On response, show a toast with the first 200 chars of output or the error.

### 3.3 Skills Tab

**Current state:** Skills tab calls legacy paths. Enable/disable calls return 501.

**Required state — replace every skills fetch:**

| Action | New path |
|---|---|
| List skills | `GET /api/skills/list` |
| Install skill | `POST /api/skills/install` |
| Update one skill | `POST /api/skills/update/{id}` |
| Update all skills | `POST /api/skills/update-all` |
| Remove skill | `DELETE /api/skills/remove/{id}` |
| Check for updates | `GET /api/skills/updates-available` |
| Skill detail | `GET /api/skills/detail/{id}` |

**Enable/disable (fix the 501):**

The Phase 1 report notes that this Hermes build exposes skill toggling only via interactive `hermes skills config`. Before the 501 can be resolved, determine how toggle state is actually stored:

1. Run `hermes skill list` in the terminal and look at the output format — does it include an `enabled` field?
2. Run `hermes skill info <any-skill-id>` and inspect the output.
3. Check whether there is a `hermes skill enable <id>` / `hermes skill disable <id>` command — run `hermes skill --help`.
4. If no enable/disable command exists, check whether the skill config file (wherever Hermes Agent stores skill configs) has an `enabled` key that can be set directly.

Based on what you find, implement one of these approaches:

**Option A** — enable/disable command exists:
```python
@router.post("/enable/{skill_id}")
async def enable_skill(skill_id: str):
    result = run_hermes(["skill", "enable", skill_id], timeout=15)
    return {"ok": result["ok"], "error": result["stderr"] if not result["ok"] else None}
```

**Option B** — no command, but a config file:
```python
@router.post("/enable/{skill_id}")
async def enable_skill(skill_id: str):
    # Read skill config path from hermes skill info output
    # Set enabled: true in the config file
    # Verify with hermes skill list that the change took effect
    ...
```

**Option C** — truly no mechanism exists in this Hermes build:
- Change the 501 response body to explain this clearly: `{ "ok": false, "error": "Skill enable/disable is not supported by this version of Hermes Agent. Use 'hermes skills config' in a terminal." }`
- In the UI, hide the enable/disable toggle entirely for now (do not show a control that always fails — that is worse than no control). Add a `// TODO: enable when Hermes Agent supports enable/disable` comment.
- Document this limitation in `docs/hermes-agent-patches.md` as a known gap.

Whichever option applies, the 501 must not remain as-is.

**UI hardening to add:**

- "Check for updates" button calls `GET /api/skills/updates-available` and badges skills with pending updates.
- Install form: single text field (URL, path, or name). Show a progress indicator during install (this can take 30+ seconds). On success, refresh the list.
- Remove: always show a confirmation dialog with the skill name before calling the delete endpoint.
- Never optimistically update the list — always re-fetch after every mutating operation.
- Clicking a skill row opens a detail panel showing the output of `GET /api/skills/detail/{id}`. If `readme` is present, render it as basic markdown (bold, italic, code blocks, lists — no full markdown library needed, a small inline renderer is fine).

---

## Phase 2 — Task 4: New Backend Endpoints Required by the UI

These endpoints are called by the UI changes above and do not yet exist.

### `POST /api/hermes/restart-cron`

Add to `server.py` (this is a system operation, not a hermes CLI call):

```python
@app.post("/api/hermes/restart-cron")
async def restart_cron_daemon():
    """Attempt to restart the Hermes Agent cron daemon."""
    result = run_hermes(["cron", "restart"], timeout=15)
    if result["ok"]:
        return {"ok": True}
    # Some builds may not have 'cron restart' — try stop+start
    run_hermes(["cron", "stop"], timeout=10)
    import asyncio
    await asyncio.sleep(1)
    result2 = run_hermes(["cron", "start"], timeout=10)
    return {"ok": result2["ok"], "error": result2["stderr"] if not result2["ok"] else None}
```

### `GET /api/cron/status`

If not already fully implemented in `cron_routes.py`, verify it returns:
```json
{ "running": true, "job_count": 4, "next_run": "2026-04-29T15:00:00Z" }
```

The `running` field must be determined by actually checking the daemon state — not assumed to always be true. Use `run_hermes(["cron", "status"])` and parse the output.

### `GET /api/skills/updates-available`

If not already implemented, run `hermes skill check-updates` (or equivalent — check `hermes skill --help`). If no such command exists:
- Run `hermes skill list` to get all installed skills with their current versions.
- For each skill, check if there is an `hermes skill info <id>` field showing latest available version.
- If version checking is not supported at all in this Hermes build, return `[]` and document in `docs/hermes-agent-patches.md`.

---

## Phase 2 — Task 5: First-Run Wizard Overlay

### Current state
Backend `/api/setup/*` routes exist. The UI shows the main chat immediately — no wizard.

### What to build

Add a full-screen overlay to `index.html` that shows on first run. This must be built entirely within the existing `index.html` — no new HTML file, no separate page.

**Trigger logic (add near top of the main JS init):**
```javascript
async function checkFirstRun() {
  const res = await fetch('/api/setup/status');
  const { first_run } = await res.json();
  if (first_run) {
    showWizard();
  }
}
```

**Wizard overlay structure:**

```html
<div id="animus-wizard" style="
  position: fixed; inset: 0; z-index: 9999;
  background: var(--bg-primary, #0d0d1a);
  display: flex; align-items: center; justify-content: center;
">
  <div id="wizard-panel" style="
    max-width: 560px; width: 90%; padding: 2.5rem;
    background: var(--bg-secondary, #1a1a2e);
    border-radius: 16px; border: 1px solid var(--border-color, #333);
  ">
    <div id="wizard-step-content"></div>
    <div id="wizard-nav" style="display:flex; gap:1rem; margin-top:2rem; justify-content:flex-end;"></div>
  </div>
</div>
```

**Steps — implement as an array of step objects, each with a `render()` and optional `validate()` async function:**

```javascript
const WIZARD_STEPS = [
  stepWelcome(),          // Step 1: ANIMUS logo + description + "Get Started"
  stepHermesCheck(),      // Step 2: GET /api/setup/hermes-check → pass/fail
  stepApiKeys(),          // Step 3: Key fields per provider + Test buttons
  stepCursorCheck(),      // Step 4: GET /api/setup/cursor-check → status display
  stepModelSelect(),      // Step 5: GET /api/setup/models → pick default
  stepSkillsInfo(),       // Step 6: GET /api/skills/list → info only
  stepTailscale(),        // Step 7: Optional, skip-friendly
  stepDone()              // Step 8: Summary + "Open ANIMUS"
];
```

**Step 1 — Welcome:**
- ANIMUS logo (use the existing SVG icon from `icon.svg`).
- Headline: "Welcome to ANIMUS"
- Body: 2–3 sentences describing what ANIMUS is. Write good copy — this is the first thing a paying customer sees.
- Single button: "Get Started →"

**Step 2 — Hermes Agent Check:**
- Call `GET /api/setup/hermes-check` on render.
- Show a spinner while waiting.
- If `ok: true`: green checkmark + "Hermes Agent v{version} — ready". "Continue →" button enabled.
- If `ok: false`: red X + the error message. Instructions: "Install Hermes Agent and run `hermes --version` to verify." "Re-check" button re-calls the endpoint. "Continue →" button disabled until check passes.

**Step 3 — API Keys:**
- Render one row per provider: label, password input, "Test" button.
- Providers to show: OpenAI, Anthropic, Google, Mistral, Groq, Cohere, Together, xAI, DeepSeek.
- "Test" button calls `POST /api/setup/test-key` with `{ provider, key }`. Shows ✓ or ✗ inline on the row.
- Keys are not required. Show "Skip →" and "Save & Continue →" buttons. Save calls `POST /api/setup/save-config` with the entered keys.
- Fields are type="password" by default with a show/hide toggle.

**Step 4 — Cursor CLI:**
- Call `GET /api/setup/cursor-check` on render.
- Show one of three states:
  - **Not installed:** grey badge "Cursor not installed". Link to cursor.sh. "Skip" is the primary action.
  - **Installed, not logged in:** yellow badge "Not logged in". Instruction: "Run `cursor login` in your terminal, then click Re-check." "Re-check" button. "Skip" secondary.
  - **Authenticated:** green badge "Logged in as {account}". "Continue →".

**Step 5 — Model Selection:**
- Call `GET /api/setup/models` on render (which returns the model list from the cache).
- Render a searchable `<select>` or filterable list, grouped by provider.
- Pre-select whatever the current default is (or the first available model if none).
- "Continue →" saves the selection and proceeds.

**Step 6 — Skills Info:**
- Call `GET /api/skills/list` on render.
- If 0 skills: "No skills installed yet. You can install skills from the Skills tab after setup."
- If skills exist: "You have {n} skill(s) installed: {names}."
- `GET /api/skills/updates-available` — if updates exist, show a note.
- Purely informational. "Continue →" only.

**Step 7 — Tailscale:**
- Explain in 2 sentences what Tailscale enables (mobile access via HTTPS from anywhere).
- Link to `docs/tailscale.md`.
- Checkbox: "I've set up Tailscale" — saves to config.
- "Skip →" is equally prominent.

**Step 8 — Done:**
- Headline: "You're all set."
- Brief summary of what was configured (keys tested, model selected, Cursor status).
- Single button: "Open ANIMUS". On click: call `POST /api/setup/complete`, then hide the wizard overlay (`#animus-wizard` display: none), then trigger the normal app init.

**Step navigation:**
- Progress indicator: dots or pills at top of the panel (`● ○ ○ ○ ○ ○ ○ ○`).
- "Back" button on all steps except Step 1.
- Wizard state is held in a JS object — not persisted to localStorage until `POST /api/setup/complete` is called (so a refresh mid-wizard restarts from Step 1 if `first_run` is still true).

---

## Phase 2 — Task 6: Onboarding Tooltips

After wizard completion, show one-time dismissable tooltips pointing to each main tab.

**Trigger:** After `POST /api/setup/complete`, before showing the main UI. Or on first visit to each tab if `localStorage.getItem('animus_tooltip_{tab}')` is not set.

**Implementation — keep it simple:**

```javascript
const TOOLTIPS = {
  chat:      "Your main conversation workspace. Start chatting with your AI.",
  workspace: "Manage projects, notes, and goals for your work.",
  plan:      "Break down complex work into stages with AI assistance.",
  cron:      "Schedule automated AI tasks to run on a timer.",
  skills:    "Install and manage AI skills that extend ANIMUS capabilities.",
  settings:  "Configure your model, API keys, and preferences."
};

function showTooltipForTab(tabName) {
  if (localStorage.getItem(`animus_tooltip_${tabName}`)) return;
  // Show a small popover near the tab button with the tooltip text
  // Dismiss on click anywhere. On dismiss: localStorage.setItem(`animus_tooltip_${tabName}`, '1')
}
```

Tooltips should be small, non-blocking, and dismiss on any click. Don't use a library — a simple absolutely-positioned div is fine.

---

## Phase 2 — Task 7: About ANIMUS Modal

Add to Settings (or as a small `ℹ` button in the app header):

**Fetch on open:**
```javascript
const res = await fetch('/api/version');
const { app, hermes } = await res.json();
```

**Display:**
- ANIMUS logo
- "ANIMUS v{app}"
- "Hermes Agent v{hermes}"
- Link to docs/
- "Check for updates" → link to Gumroad page (use a placeholder URL for now: `https://gumroad.com/l/animus` — owner will update)

---

## Phase 2 — Task 8: Docker Build Verification

The docker setup was added in Phase 1 but never built. Do this now.

```bash
cd /home/sketch/animus/docker
docker compose build 2>&1 | tee /tmp/animus-docker-build.log
```

If the build fails:
1. Read the full error from the log.
2. Fix the `Dockerfile` or `docker-compose.yml`.
3. Re-run until it succeeds.
4. Then verify the container starts: `docker compose up -d && sleep 5 && curl -sS http://localhost:3001/api/version | python3 -m json.tool`
5. `docker compose down` when done.

The build must succeed and the version endpoint must respond before this task is considered done.

---

## Phase 2 — Task 9: `build-release.sh` — Add Missing Checks

The Phase 1 build-release.sh produces the zip correctly. Add the following checks to it:

```bash
# Check ANIMUS branding is complete
echo "[check] No 'Hermes Chat' in user-facing UI..."
if grep -rq "Hermes Chat" animus-chat/static/index.html; then
  echo "FAIL: 'Hermes Chat' found in index.html" && exit 1
fi

# Check legacy API paths are gone from the UI
echo "[check] No legacy /api/chat-models calls..."
if grep -q "chat-models" animus-chat/static/index.html; then
  echo "FAIL: legacy /api/chat-models still in index.html" && exit 1
fi

echo "[check] No legacy /api/cron/jobs calls..."
if grep -q "cron/jobs" animus-chat/static/index.html; then
  echo "FAIL: legacy /api/cron/jobs still in index.html" && exit 1
fi

# Check subprocess isolation
echo "[check] No direct subprocess hermes calls in server.py..."
if grep -n "subprocess" animus-chat/server.py | grep -v "# exempt:"; then
  echo "FAIL: raw subprocess call found in server.py without exemption comment" && exit 1
fi

# Check hermes-agent-patches.md exists and is non-empty
echo "[check] hermes-agent-patches.md exists..."
if [ ! -s docs/hermes-agent-patches.md ]; then
  echo "FAIL: docs/hermes-agent-patches.md is missing or empty" && exit 1
fi
```

---

## Phase 2 — Acceptance Criteria

Phase 2 is complete when ALL of the following pass:

**Backend integrity:**
- [ ] `grep -n "subprocess" animus-chat/server.py | grep -v "# exempt:"` returns zero lines.
- [ ] Legacy routes `/api/chat-models`, `/api/cron/jobs` are gone from `server.py`.
- [ ] `POST /api/hermes/restart-cron` exists and returns `{ ok: bool }`.
- [ ] `GET /api/cron/status` returns `{ running: bool, job_count: int }`.
- [ ] `POST /api/skills/enable/{id}` and `POST /api/skills/disable/{id}` no longer return 501 — they either work, or return a clear error with documentation.

**UI wiring:**
- [ ] Settings model selector fetches from `GET /api/models` — not a hardcoded list.
- [ ] "Refresh model list" button calls `POST /api/models/refresh` then re-renders.
- [ ] Cron tab calls `GET /api/cron/list` on open — not `/api/cron/jobs`.
- [ ] Skills tab calls `GET /api/skills/list` on open.
- [ ] `grep -q "chat-models" animus-chat/static/index.html` returns false.
- [ ] `grep -q "cron/jobs" animus-chat/static/index.html` returns false.

**Wizard:**
- [ ] Opening `http://localhost:3001` on a fresh install (with `first_run: true` in config) shows the wizard overlay — not the main chat.
- [ ] All 8 wizard steps render without JS errors.
- [ ] Step 2 Hermes check correctly shows pass/fail based on actual `hermes --version`.
- [ ] Step 4 Cursor check correctly shows not-installed / not-logged-in / authenticated.
- [ ] Completing the wizard calls `POST /api/setup/complete` and shows the main ANIMUS UI.
- [ ] After completion, `GET /api/setup/status` returns `{ first_run: false }`.
- [ ] Refreshing after completion does not show the wizard again.

**Docker:**
- [ ] `docker compose build` succeeds without errors.
- [ ] `docker compose up -d && curl -sS http://localhost:3001/api/version | python3 -m json.tool` returns valid JSON.

**Release:**
- [ ] `./build-release.sh` passes all new checks added in Task 9.
- [ ] Produced zip is under 50MB.

---

## What to Leave for Phase 3

Do not work on these now — flag them as known gaps:

- Full markdown rendering in skill detail panel (beyond basic formatting)
- Token usage tracker wiring to new backend (if existing tracker calls legacy paths)
- Wake lock settings persistence across wizard completion
- Windows installer (`install.ps1`) — verify it works on an actual Windows machine
- Tailscale HTTPS serving instructions — verify they still apply with the new monorepo layout
- Any Hermes Agent patches discovered during diffing that require Agent-side code changes

Document each of these in `project_status.md` under a "Phase 3" section.

---

*All tasks in this directive are required. Do not mark Phase 2 complete until all acceptance criteria pass and `./build-release.sh` runs clean.*



## ANIMUS — Phase 3 Build Directive

**Follows from:** Phase 2 (UI wiring, wizard, cron hardening, release pipeline)
**Working directory:** `/home/sketch/animus/` — live instances untouched
**Port:** ANIMUS on 3001. Live hermes-chat on 3000. Do not touch it.

---

## Status Coming In

Phase 2 delivered: full cron UI, model selector wired, About modal, first-run wizard (8 steps), tab tooltips, wizard backend extended, build-release.sh hardened, all greps passing, ~50MB zip builds clean.

**Carried forward from Phase 2 (must close before Phase 3 is done):**

| Item | Status | Action |
|---|---|---|
| Docker build | Blocked — Docker not in build environment | Verify on host machine with Docker installed |
| Cron logs | Placeholder payload in `cron_routes.py` | Wire to real log source (Task 1) |
| Skills UI tab wiring | Not confirmed done in Phase 2 report | Audit and complete (Task 2) |
| Skills enable/disable toggle | Option C documented — toggle not hidden in UI | Hide the control (Task 3) |

**New Phase 3 work:**

| Area | Task |
|---|---|
| Cron logs real implementation | Task 1 |
| Skills tab full audit and wiring | Task 2 |
| Skills enable/disable UI cleanup | Task 3 |
| Token usage tracker wiring | Task 4 |
| Wake lock persistence across wizard | Task 5 |
| Hermes Agent patch audit completion | Task 6 |
| Pre-release end-to-end smoke test | Task 7 |
| Docker verification | Task 8 |

---

## Phase 3 — Task 1: Cron Logs — Wire to Real Source

### Current state
`GET /api/cron/logs/{id}` returns a placeholder payload. The UI modal loads and renders it, but customers will see fake data.

### What to do

**Step 1 — Find where Hermes Agent writes cron job output.**

Run these to locate real log data — read only, do not modify:

```bash
hermes cron list                          # get a real job id
hermes cron logs <job_id>                 # does this command exist?
hermes cron --help                        # check available subcommands
hermes --config-dir                       # find config/data root
find $(hermes --config-dir 2>/dev/null) -name "*.log" 2>/dev/null | head -20
find ~/.hermes -name "*.log" 2>/dev/null | head -20
journalctl -u animus-agent.service --no-pager -n 50 2>/dev/null  # systemd logs
```

**Step 2 — Based on what you find, implement one of:**

**Option A — `hermes cron logs <id>` command exists:**
```python
@router.get("/logs/{job_id}")
async def get_cron_logs(job_id: str, lines: int = 50):
    result = run_hermes(["cron", "logs", job_id, "--lines", str(lines)], timeout=15)
    if not result["ok"]:
        return {"lines": [], "error": result["stderr"]}
    # Parse output into line objects
    parsed = [
        {"timestamp": "", "message": line, "level": "info"}
        for line in result["stdout"].splitlines()
        if line.strip()
    ]
    return {"lines": parsed[-lines:]}
```

**Option B — Log file on disk:**
```python
import re
from pathlib import Path

@router.get("/logs/{job_id}")
async def get_cron_logs(job_id: str, lines: int = 50):
    # Locate the log file for this job — adjust path to what you found
    log_path = Path(os.getenv("HERMES_DATA_DIR", Path.home() / ".hermes")) / "cron" / f"{job_id}.log"
    if not log_path.exists():
        return {"lines": [], "error": f"No log file found for job {job_id}"}
    raw = log_path.read_text(errors="replace").splitlines()
    parsed = [{"timestamp": "", "message": l, "level": "info"} for l in raw if l.strip()]
    return {"lines": parsed[-lines:]}
```

**Option C — Only systemd/journald:**
```python
@router.get("/logs/{job_id}")
async def get_cron_logs(job_id: str, lines: int = 50):
    result = run_hermes(  # use run_hermes wrapper pattern for system calls too
        # Actually use subprocess directly here since this is journalctl not hermes
        # Add # exempt: journalctl — not a hermes binary call
        ...
    )
```

For Option C, add `# exempt: journalctl — system log reader, not a hermes binary call` to comply with the subprocess audit rule.

**Option D — Truly no log source accessible:**
- Return a real error message, not a placeholder: `{ "lines": [], "error": "Log access is not available for this Hermes Agent build. Check your terminal for cron output." }`
- Document in `docs/hermes-agent-patches.md` under a "Known gaps" section.
- In the UI log modal, display the error message clearly instead of an empty list.

Whatever option applies, **remove the placeholder payload entirely**. A clear error is better than fake data.

**Step 3 — Update the cron_audit.log writer** to capture each run's output (first 500 chars) so there is at minimum an audit trail even if full log access isn't available:
```python
# In cron_routes.py POST /run/{id}, after getting the result:
audit_entry = f"{datetime.utcnow().isoformat()}Z RUN job_id={job_id} result={'ok' if result['ok'] else 'error'} output_preview={result['stdout'][:500]!r}\n"
AUDIT_LOG.write_text(AUDIT_LOG.read_text() + audit_entry if AUDIT_LOG.exists() else audit_entry)
```

---

## Phase 3 — Task 2: Skills Tab — Full Audit and Wiring

The Phase 2 report did not explicitly confirm the Skills tab was wired to the new API paths. Audit it now.

**Step 1 — Check current state:**
```bash
grep -n "api/skills" animus-chat/app/index.html
```

List every skills-related fetch call and which path it hits. Compare against the required endpoints from Phase 2 §3.3.

**Step 2 — For any path that is missing or still calling a legacy route, implement it.**

Required fetch calls that must exist in `index.html`:

| Trigger | Endpoint | Expected response shape |
|---|---|---|
| Skills tab open | `GET /api/skills/list` | `[{ id, name, version, description, enabled, source, last_updated }]` |
| "Check for updates" button | `GET /api/skills/updates-available` | `[{ id, name, current_version, latest_version }]` |
| "Install" form submit | `POST /api/skills/install` | `{ ok, id?, error? }` |
| "Update" button on row | `POST /api/skills/update/{id}` | `{ ok, version_before, version_after, error? }` |
| "Update All" button | `POST /api/skills/update-all` | `{ ok, updated: [], errors: [] }` |
| "Remove" confirm | `DELETE /api/skills/remove/{id}` | `{ ok, error? }` |
| Row click | `GET /api/skills/detail/{id}` | `{ id, name, version, description, readme?, config_schema? }` |

**Step 3 — After every mutating operation, re-fetch `GET /api/skills/list`.** Never optimistically update the local list. This must be true for install, update, update-all, and remove.

**Step 4 — Install progress.** Skill install can take 30+ seconds. The install button must show a spinner and the text "Installing…" while the request is in-flight. The submit button must be disabled during this time to prevent double-submissions.

**Step 5 — Skill detail panel.** Clicking a skill row must open a side panel or modal showing:
- Name, version, source, last updated.
- Description (full, not truncated).
- If `readme` is in the response: render it with minimal markdown — bold (`**text**`), inline code (`` `code` ``), code blocks (` ``` `), and unordered lists (`- item`). No external library needed — a small inline renderer (~30 lines) is sufficient.
- If `config_schema` is in the response: show it as formatted JSON in a `<pre>` block.

---

## Phase 3 — Task 3: Skills Enable/Disable — Hide the Broken Control

Phase 2 documented Option C for skills enable/disable: the capability doesn't exist in this Hermes build. The UI must reflect this — a toggle that always fails is worse than no toggle.

**In `index.html`, find the skills enable/disable toggle and:**

1. Hide it by default using a data attribute on the skills section container:
   ```html
   <div id="skills-container" data-enable-toggle="false">
   ```
2. In the CSS (or inline style logic):
   ```javascript
   // After loading skills list, check a backend capability flag
   const cap = await fetch('/api/skills/capabilities').then(r => r.json()).catch(() => ({}));
   document.getElementById('skills-container')
     .dataset.enableToggle = cap.enable_disable_supported ? 'true' : 'false';
   ```
3. Add `GET /api/skills/capabilities` to `skills_routes.py`:
   ```python
   @router.get("/capabilities")
   async def skills_capabilities():
       # Test whether enable/disable works by checking hermes skill --help
       result = run_hermes(["skill", "--help"], timeout=10)
       supports_toggle = "enable" in result["stdout"] and "disable" in result["stdout"]
       return {
           "enable_disable_supported": supports_toggle,
           "check_updates_supported": "check-updates" in result["stdout"],
           "install_supported": "install" in result["stdout"]
       }
   ```
4. In CSS, hide the toggle when `data-enable-toggle="false"`:
   ```css
   [data-enable-toggle="false"] .skill-enable-toggle { display: none; }
   ```
5. This future-proofs the feature — when a Hermes build that supports enable/disable is bundled, the toggle will appear automatically without any UI changes.

---

## Phase 3 — Task 4: Token Usage Tracker — Audit and Wire

The token usage tracker was implemented in the live hermes-chat instance. Check its current state in ANIMUS:

**Step 1 — Find it:**
```bash
grep -n "token" animus-chat/app/index.html | grep -i "track\|usage\|count" | head -20
grep -n "token_tracker\|tokenTracker\|token-tracker" animus-chat/app/index.html | head -20
```

**Step 2 — Check what API path it calls.** If it calls a legacy path or a path that no longer exists in `server.py`, update it.

**Step 3 — Verify the tracker populates.** The Phase 1 report noted the tracker only populates once new assistant messages include provider-reported usage in the response. Verify this works end-to-end:
- Send a test message.
- Check whether the response from `server.py` includes a `usage` field with `input_tokens` and `output_tokens`.
- If it does, verify the tracker records it.
- If it does not, find where in `server.py` the chat response is assembled and ensure `usage` data from the provider is forwarded to the client.

**Step 4 — The tracker must show data correctly grouped by provider and model** (this was implemented in the live instance per the project history). Verify the grouping still works with the new model selection system where the model is chosen from the full ANIMUS model selector.

**Step 5 — CSV export.** Verify the export still works. The export format must include `date, provider, model, input_tokens, output_tokens` per row. Run a test export after sending a few messages.

---

## Phase 3 — Task 5: Wake Lock — Persist Across Wizard

The wake lock setting (screen stays on while ANIMUS is working) was implemented in the live instance with a Settings toggle defaulted to on. Verify its state in ANIMUS:

**Step 1:**
```bash
grep -n "wake\|wakeLock\|WakeLock" animus-chat/app/index.html | head -20
```

**Step 2 — Verify the wizard persists the setting.** The wizard's final `POST /api/setup/save-config` should include a `wake_lock` field. Check `wizard_routes.py` — if it's not being saved, add it:
```python
# In save_config endpoint:
config["wake_lock"] = body.get("wake_lock", True)  # default on
```

**Step 3 — Verify the setting is read on startup.** When `index.html` initialises, it must read the wake lock preference from `config.json` under `chat_data_dir()` (via `GET /api/animus/client-config` or equivalent) and apply it — not always default to the hardcoded value.

**Step 4 — The wake lock must only activate during active streaming** (while a response is being generated). Verify this is still the case — it must not hold the wake lock indefinitely.

**Step 5 — Add a toggle in Settings** (if not already present) so users can change the preference after the wizard. The toggle must write back to `config.json` under `chat_data_dir()` via the backend (e.g. `POST /api/animus/client-config`), not just `localStorage`, so it survives a reinstall.

---

## Phase 3 — Task 6: Hermes Agent Patch Audit — Complete the Record

`docs/hermes-agent-patches.md` was created in Phase 1 and updated with the skills Option C gap in Phase 2. Before ANIMUS ships, this document must be complete.

**Step 1 — Run a thorough diff of the bundled `hermes-agent/` against upstream:**

```bash
cd /home/sketch/animus/hermes-agent

# If it's a git repo:
git log --oneline --all | head -30    # local commit history
git remote -v                          # does it have an upstream remote?
git diff HEAD~5..HEAD --stat           # what changed in the last 5 commits?
git log --oneline --all --graph | head -40

# If not a git repo, compare against a fresh upstream install:
pip download hermes-agent --no-deps -d /tmp/hermes-upstream 2>/dev/null
# or clone from GitHub if the source is public
```

**Step 2 — For every difference found, add an entry to `docs/hermes-agent-patches.md`:**

```markdown
## Patch N — [Short name]
**File(s):** relative/path/to/changed/file.py
**Type:** [new feature | bug fix | configuration change | provider addition]
**What it does:** One paragraph description.
**Why it exists:** Why this change was needed for ANIMUS.
**Risk if removed:** What breaks if a future Hermes Agent update overwrites this.
**Test to verify:** Command or action that confirms the patch is working.
```

**Step 3 — The Cursor CLI patch specifically must be documented with a "Test to verify" entry:**
```markdown
**Test to verify:** In ANIMUS Settings, select the Cursor provider and send a test message.
Response should arrive using Cursor's underlying model. The per-message provider badge
should show "cursor" or the specific Cursor model name.
```

**Step 4 — After completing the doc, add a check to `build-release.sh`:**
```bash
echo "[check] hermes-agent-patches.md has at least 3 patch entries..."
PATCH_COUNT=$(grep -c "^## Patch" docs/hermes-agent-patches.md 2>/dev/null || echo 0)
if [ "$PATCH_COUNT" -lt 1 ]; then
  echo "FAIL: hermes-agent-patches.md has no patch entries" && exit 1
fi
echo "  Found $PATCH_COUNT patch entries — OK"
```

---

## Phase 3 — Task 7: Pre-Release Smoke Test

Before marking Phase 3 complete, run a full end-to-end test of the ANIMUS product as a new user would experience it. This must be done against a **clean `chat_data_dir()`** — not your normal dev tree (usually `~/.hermes/chat`). There is **no** default `animus-chat/data/` folder; see `hermes_runner.chat_data_dir()` resolution order in Phase 4 Step 1 below.

**Setup (aligned with `scripts/phase3-smoke-checklist.md`):**
```bash
cd /home/sketch/animus/animus-chat

export CHAT_DATA_DIR="/tmp/animus-smoke-$(date +%s)"
mkdir -p "$CHAT_DATA_DIR"

# Same shell must start the server so it inherits CHAT_DATA_DIR.
# Use .venv/bin/python or python3 — plain `python` is often missing on Debian/Ubuntu.
./.venv/bin/python server.py &
# or: python3 server.py &

# Before opening the UI: confirm animus.env (repo) and/or ~/.hermes/.env has a working gateway API key — wizard step 3 and chat step 9 need it.
```

**Test sequence — run in order, do not skip:**

1. **First run:** Open `http://localhost:3001`. Confirm wizard appears — not the main chat.
2. **Wizard Step 1:** Welcome screen renders with ANIMUS name and logo.
3. **Wizard Step 2:** Hermes Agent check passes. Version number is shown.
4. **Wizard Step 3:** Enter a real API key for one provider. Click "Test" — confirm it shows ✓.
5. **Wizard Step 4:** Cursor check shows the correct state (installed/not installed/authenticated).
6. **Wizard Step 5:** Model list loads. Select a model from the tested provider.
7. **Wizard Steps 6–8:** Skills info, Tailscale, Done. Click "Open ANIMUS".
8. **Main UI:** Confirm wizard is gone. Confirm tab tooltips appear on first visit.
9. **Chat:** Send a real message. Confirm response arrives. Confirm provider badge shows at bottom.
10. **Model selector:** Go to Settings. Confirm full model list is loaded. Change model. Send another message. Confirm provider badge reflects new model.
11. **Cron tab:** Open. Confirm daemon banner shows correct status. Create a test job (e.g. `echo "animus cron test"`, schedule `* * * * *`). Confirm it appears in `hermes cron list` in the terminal.
12. **Skills tab:** Open. Confirm skill list loads (even if empty). Click "Check for updates".
13. **Token tracker:** Open Settings → Token tracker. Confirm the messages sent in step 9–10 appear in the chart.
14. **About modal:** Open. Confirm ANIMUS version and Hermes Agent version are shown.
15. **Refresh:** Reload the page. Confirm wizard does NOT appear again.
16. **Build release:** `./build-release.sh` — confirm all checks pass and zip is produced.

**After the test:**
```bash
kill %1   # or stop the server process you started
unset CHAT_DATA_DIR
rm -rf /tmp/animus-smoke-*   # throwaway smoke dir; your real ~/.hermes/chat was untouched
```

Document the result of each step in `project_status.md` under "Phase 3 Smoke Test".

Any step that fails is a blocker — fix it before proceeding to Task 8.

---

## Phase 3 — Task 8: Docker Verification

This was the only unclosed Phase 2 acceptance criterion. Run this on a machine with Docker installed.

```bash
cd /home/sketch/animus/docker

# Build
docker compose build 2>&1 | tee /tmp/animus-docker-build.log
# Must exit 0. If it fails, read the log and fix the Dockerfile.

# Start
docker compose up -d

# Wait for startup
sleep 8

# Version check
curl -sS http://localhost:3001/api/version | python3 -m json.tool
# Must return { "app": "1.0.0", "hermes": "x.y.z" }

# Hermes check
curl -sS http://localhost:3001/api/setup/hermes-check | python3 -m json.tool
# Must return { "ok": true, "version": "..." }

# Tear down
docker compose down
```

**If the build fails, common causes to check:**
- `hermes-agent/` install command in Dockerfile doesn't work in the container OS — fix the install step.
- The `hermes` binary ends up in a path not on `$PATH` inside the container — add the path to `ENV PATH`.
- Port conflict — the container tries to bind 3000 instead of 3001 — check `CHAT_PORT` env var in `docker-compose.yml`.
- `animus.env` not found inside the container — verify the volume mounts and env_file path in `docker-compose.yml`.

Once the build and curl checks pass, add a note to `INSTALL.md` confirming the Docker path is tested.

---

## Phase 3 — Acceptance Criteria

Phase 3 is complete when ALL of the following pass:

**Cron logs:**
- [ ] `GET /api/cron/logs/{job_id}` returns real data (or a clear error message) — not a placeholder payload.
- [ ] The placeholder payload has been removed from `cron_routes.py`.

**Skills:**
- [ ] All skills fetch calls in `index.html` use the new `/api/skills/*` paths.
- [ ] Skills install shows a spinner during the request and re-fetches the list on success.
- [ ] Skill detail panel opens on row click and shows full description and readme if available.
- [ ] Enable/disable toggle is hidden when `GET /api/skills/capabilities` returns `enable_disable_supported: false`.

**Token tracker:**
- [ ] Sending a chat message causes an entry to appear in the token tracker after a page refresh or manual tracker refresh.
- [ ] Per-provider and per-model grouping is correct.
- [ ] CSV export produces a valid file with at least one data row after the smoke test.

**Wake lock:**
- [ ] Wake lock preference is saved by the wizard and persisted in `config.json` under `chat_data_dir()`.
- [ ] Wake lock preference is read on startup, not assumed to be the hardcoded default.
- [ ] A Settings toggle exists and writing to it updates that `config.json` via the backend (e.g. `POST /api/animus/client-config`).

**Hermes Agent patches:**
- [ ] `docs/hermes-agent-patches.md` contains at least one entry per known customisation.
- [ ] The Cursor CLI patch entry includes a "Test to verify" section.
- [ ] `build-release.sh` checks for at least 1 patch entry.

**Smoke test:**
- [ ] All 16 smoke test steps pass without error.
- [ ] Results documented in `project_status.md`.

**Docker:**
- [ ] `docker compose build` exits 0.
- [ ] `curl -sS http://localhost:3001/api/version | python3 -m json.tool` returns valid JSON from the host against the running container.

**Release:**
- [ ] `./build-release.sh` passes all checks.
- [ ] Produced zip is under 50MB.
- [ ] Zip filename is `animus-v1.0.0.zip`.

---

## Phase 3 Complete = Product Ready for Gumroad

When all acceptance criteria above pass and the smoke test is documented, ANIMUS v1.0.0 is ready for the Gumroad listing. At that point, the remaining items deferred to future versions are:

- Windows installer (`install.ps1`) — verified on actual Windows hardware
- Skills enable/disable — when a Hermes Agent build that supports it is bundled
- Cron logs — if a richer log source becomes available
- Auto-update mechanism — notify users when a new ANIMUS version is available

Document all of these in `project_status.md` under "v1.1 backlog" so they're tracked.

---

*All tasks in this directive are required unless explicitly marked optional. Do not mark Phase 3 complete until the smoke test passes end-to-end and the release zip builds clean.*

## ANIMUS — Phase 4: Go-Live Directive

**Follows from:** Phase 3 (code complete, build passing, ~51MB zip)
**Who runs this:** The owner, on their real machine with Docker, gateway, and API keys
**Goal:** Smoke test → fix blockers → Gumroad listing live

---

## What Is and Isn't Left

**Code is complete.** All backend modules, UI wiring, wizard, cron, skills, wake lock, token tracker, and release tooling are implemented and building clean.

**What remains is owner-run validation and launch prep:**

| Item | Who | Blocker for launch? |
|---|---|---|
| Smoke test 16 steps | Owner | Yes |
| Docker build + verify | Owner or CI | Yes |
| Zip size trim (over 55MB) | Coder (v1.1) | If build exceeds cap |
| Token tracker gateway fix | Coder (if needed after smoke test) | Depends on step 9 result |
| Screenshots for Gumroad | Owner | Yes |
| Gumroad listing copy + delivery | Owner | Yes |
| Final `build-release.sh` clean run | Owner | Yes |

Work through this in the order below. Do not list ANIMUS on Gumroad until the smoke test passes.

---

## Step 1 — Run the Smoke Test

Run `scripts/phase3-smoke-checklist.md` exactly as written. **Before starting:** confirm `animus.env` (repo) and/or `~/.hermes/.env` contains a **working gateway API key** — wizard step 3 (key test) and smoke step 9 (real chat) both fail silently or obviously if the key is blank or invalid (a key that works in another Hermes Chat install should transfer, but verify before you start).

Also read the checklist section **Practical tips** (keys, SSE `usage` during chat, screenshot timing, **`unset CHAT_DATA_DIR`** before `./build-release.sh`) — same bullets live under **Go-live smoke** in `project_knowledge.md`.

Before starting, understand how the app finds its data directory — the smoke setup depends on this.

### How ANIMUS picks its data directory

ANIMUS does **not** use `animus-chat/data/` by default. Conversation history and `config.json` live in `chat_data_dir()`, resolved in this order:

1. `CHAT_DATA_DIR` environment variable (if set)
2. `HERMES_CHAT_DATA_DIR` environment variable (if set)
3. Value from `~/.hermes/.env` (if that file exists and sets it)
4. Default: `~/.hermes/chat`

There is likely **no** `animus-chat/data/` folder in your repo at all — `mv data/` will fail. Do not try to create or move it.

### Correct smoke test setup — use a throwaway directory

The safest approach is to point the server at a temporary directory for the smoke test. This avoids touching your real `~/.hermes/chat` data entirely:

```bash
cd /home/sketch/animus/animus-chat

# Create a fresh throwaway data dir for the smoke test
export CHAT_DATA_DIR="/tmp/animus-smoke-$(date +%s)"
mkdir -p "$CHAT_DATA_DIR"

# Start the server in the SAME shell so it inherits CHAT_DATA_DIR
./.venv/bin/python server.py &
# or: python3 server.py &
```

Note: use `.venv/bin/python` or `python3` — plain `python` is not installed on this machine.

Open `http://localhost:3001` and run steps 1–16.

**Fill in the results table in `project_status.md` as you go.** Do not do this from memory after the fact.

**If any step fails, stop.** Note which step, what the actual vs expected behaviour was, and hand it to the coder with that specific context. Do not continue with a failing step unresolved.

### After the smoke test

```bash
# Stop the test server
kill %1

# Clean up the throwaway data dir
unset CHAT_DATA_DIR
rm -rf /tmp/animus-smoke-*

# Your real ~/.hermes/chat data is untouched
```

---

## Step 2 — Docker Verification

On a machine with Docker installed (this can be your main machine once the smoke test above passes):

```bash
cd /home/sketch/animus/docker
docker compose build 2>&1 | tee /tmp/animus-docker-build.log
```

If this fails, send the log to the coder. Common fixes are a bad pip install command in the Dockerfile, a missing `ENV PATH` for the hermes binary, or a wrong port binding.

If it succeeds:

```bash
docker compose up -d
sleep 8
curl -sS http://localhost:3001/api/version | python3 -m json.tool
# Expected: { "app": "1.0.0", "hermes": "x.y.z" }
curl -sS http://localhost:3001/api/setup/hermes-check | python3 -m json.tool
# Expected: { "ok": true, "version": "..." }
docker compose down
```

Both curl calls must succeed. If they do, Docker is verified — note it in `project_status.md`.

---

## Step 3 — Token Tracker Gateway Check

During smoke test step 9 (send a real message), check whether the token tracker populates.

**If it does:** Token tracker is working. No action needed.

**If it does not:** The gateway is likely stripping the `usage` field from the SSE stream before it reaches the client. Stream a minimal chat and print any line containing `usage` (use **`python3`** — plain `python` is often not on PATH on Debian/Ubuntu):

```bash
curl -s -N -X POST http://localhost:3001/api/chat \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"Say one word"}],"stream":true}' \
  | python3 -c "
import sys
for line in sys.stdin:
    if 'usage' in line.lower():
        print(line.rstrip())
"
```

(Equivalent: pipe the same `curl` to `grep -i usage` if you prefer.)

If `usage` never appears in the stream output, open `animus-chat/server.py` and find the SSE proxy/forwarding code. The gateway response must include `include_usage: true` in the request to the upstream provider, and the `usage` block from the response must be forwarded through to the client. Hand the coder the specific lines in `server.py` where the SSE forwarding happens and ask them to ensure usage data passes through.

---

## Step 4 — Zip Size (Send to Coder if Over 55MB)

**v1.0:** Acceptance cap is **≤55MB** (~51MB typical). If the zip grows past 55MB, trim or split the ship tree; otherwise defer micro-optimisations to v1.1. If you need a hard trim below 55MB, send this to the coder:

> The release zip exceeds 55MB. Find what is pushing it over the cap and trim it. Check for: compiled `.pyc` files not excluded by .gitignore, any test fixtures or sample data files in hermes-agent/ that don't need to ship, any duplicate assets. Do not remove any functional code. Re-run `./build-release.sh` and confirm the new zip size.

This is not a launch blocker — 51MB is fine. It's cosmetic.

---

## Step 5 — Take Screenshots

You need at least 3 screenshots for the Gumroad listing. Take these after the smoke test so you have real populated data.

**Required shots:**

1. **The wizard welcome screen** — Step 1 of the first-run wizard, showing the ANIMUS name and logo on a clean install.
2. **Main chat interface** — An active chat conversation showing the model provider badge at the bottom of a response.
3. **Cron tab** — With at least one scheduled job in the list and the daemon status banner showing "Running".

**Recommended additional shots:**

4. Skills tab showing installed skills with the detail panel open.
5. Settings showing the full model selector with providers grouped.
6. The About ANIMUS modal.
7. ANIMUS installed as a PWA on an Android home screen (shows it works on mobile).

Save all screenshots to `docs/screenshots/` in the repo. Name them descriptively: `01-wizard-welcome.png`, `02-chat-interface.png`, etc.

---

## Step 6 — Gumroad Listing

### Product details

**Product name:** ANIMUS

**Tagline (under 100 chars):**
Your personal AI command center — powered by Hermes Agent, runs on your own machine.

**Description (use this as a starting point — edit to your voice):**

---

ANIMUS is a self-hosted AI workspace that puts you in complete control of your AI environment. Built on top of Hermes Agent, it runs entirely on your own hardware — your data stays yours.

**What you get:**
- A polished PWA chat interface that works on desktop and installs to your phone via Tailscale
- Full model selection across every provider Hermes Agent supports — OpenAI, Anthropic, Google, Cursor CLI, and more — in one unified picker
- A built-in cron scheduler to run AI tasks automatically on a timer
- A skills manager to install, update, and manage Hermes Agent skills without touching a terminal
- A first-run setup wizard so you're up and running in minutes
- Token usage tracking per provider and model with CSV export
- Docker support for easy deployment

**System requirements:**
- Linux or macOS (Windows via Docker)
- Python 3.10+
- Hermes Agent (bundled — no separate install needed)

**Includes:**
- Full source code
- One-command installer (`./installer/install.sh`)
- Docker Compose setup
- Complete documentation

---

### Pricing

This is your call, but for reference: a self-hosted AI tool of this scope with bundled agent, installer, Docker, and documentation typically sells in the **$29–$79** range on Gumroad for a one-time purchase. If you plan to offer updates, consider a pay-what-you-want with a minimum floor.

### Delivery file

Upload `animus-v1.0.0.zip` (produced by `./build-release.sh`).

### Gumroad settings to configure

- **Content type:** Digital product
- **File:** `animus-v1.0.0.zip`
- **Cover image:** Use screenshot 2 (main chat interface) or a composite of 2–3 screenshots
- **Summary:** Paste the tagline above
- **Description:** Paste and edit the description above
- **Ratings:** Enable
- **Refund policy:** Set to whatever you're comfortable with (suggest 30 days / no questions asked — it builds trust for a technical product)

---

## Step 7 — Final `build-release.sh` Clean Run

Before uploading to Gumroad, run the release script one final time on the exact commit you intend to ship:

```bash
cd /home/sketch/animus
git add -A && git commit -m "chore: Phase 3 complete — v1.0.0 release candidate"
./build-release.sh
```

Verify:
- All checks pass (no FAIL lines)
- Zip filename is `animus-v1.0.0.zip`
- Zip size is acceptable
- Unzip the zip to a temp directory and verify `animus.env` and `data/` are not in it:
  ```bash
  mkdir /tmp/animus-verify
  unzip -l animus-v1.0.0.zip | grep -E "animus\.env$|/data/"
  # Must return nothing
  ```

---

## Step 8 — Post-Launch Tracking

After listing goes live, set a reminder for these:

**Day 1:** Check Gumroad for any purchase issues or download errors.

**Week 1:** If anyone reports install failures, the most common causes will be:
- Python version below 3.10
- Hermes Agent pip install failing on their machine (different OS/arch)
- Port 3001 already in use

Capture these as issues and hand to the coder for installer hardening in v1.1.

**v1.1 backlog (do not block launch on these):**
- Windows installer (`install.ps1`) verified on real Windows hardware
- Skills enable/disable when a compatible Hermes Agent build supports it
- Richer cron log access if a better log source is available
- Auto-update notification when a new ANIMUS version is released
- Skills enable/disable capability auto-detected and toggle shown/hidden dynamically

Document all incoming issues in `project_status.md` under "v1.1 Issues".

---

## Launch Criteria — ANIMUS v1.0.0

List on Gumroad only when all of the following are true:

- [ ] Smoke test all 16 steps passed and documented in `project_status.md`
- [ ] Docker build and curl checks passed
- [ ] Token tracker confirmed working (or gateway fix applied and re-tested)
- [ ] At least 3 screenshots taken and in `docs/screenshots/`
- [ ] `./build-release.sh` final run passes all checks
- [ ] Zip does not contain `animus.env` or `data/`
- [ ] Gumroad listing drafted, cover image uploaded, file attached
- [ ] You have personally installed from the zip on a clean directory and run the wizard

That last one is important — install from the zip, not from your working directory. The zip is what customers get. Any gap between the two is a bug.

---

*When the launch criteria checklist above is fully checked, ANIMUS v1.0.0 is live. Good luck.*


## ANIMUS — Phase 5 Build Directive

**Follows from:** Phase 4 smoke test run (live walkthrough)
**Working directory:** `/home/sketch/animus/` — live instances untouched, port 3001
**Source of issues:** Owner smoke test, steps 3–done screen + settings audit

---

## Overview of Issues Found

All issues below were discovered during the live smoke test. They fall into four areas:

1. **Wizard UX** — provider selection, model picker, skills, Tailscale, wake lock, projects folder
2. **Branding** — "Hermes" showing in Plan tab instead of "ANIMUS"
3. **Settings** — Inference backend needs full provider/model matrix with auth status
4. **About + Updates** — fuller description, auto-update from GitHub

Work through the tasks in the order listed. Tasks 1–4 are wizard fixes and must be done together since they share state (provider selections flow into model picker). Tasks 5–7 are independent.

---

## Task 1 — Wizard Step 3: Replace Key Form with Provider Selection Flow

### Current behaviour
Step 3 shows all provider API key fields simultaneously. Test button says "Enter a key before testing" with no key available. Users who only use Cursor CLI or Codex must look at irrelevant empty fields.

### Required behaviour

**Part A — Provider picker (shown first):**

Render a clean checklist. User picks which providers they want to use. Nothing else is shown until they pick.

```
Which AI providers do you want to use?
(You can add more later in Settings)

[ ] OpenAI              — API key required
[ ] Anthropic           — API key required
[ ] Google              — API key required
[ ] Mistral             — API key required
[ ] Groq                — API key required
[ ] Cohere              — API key required
[ ] Together            — API key required
[ ] xAI                 — API key required
[ ] DeepSeek            — API key required
[ ] OpenAI Codex        — OAuth sign-in, no API key
[ ] Cursor CLI          — cursor login, no API key

[Skip all →]   [Continue →]
```

**Part B — Auth for selected providers only (shown after Continue):**

Dynamically render only what the selected providers need:

- **API key providers:** One field + one "Test" button per selected provider. Test button is disabled while field is empty. On click: calls `POST /api/setup/test-key`. Shows ✓ or ✗ inline. Never shows "Enter a key before testing" — the button is simply greyed out until there is a value.
- **OpenAI Codex:** "Sign in with Codex" button that triggers the OAuth browser flow. Shows auth status after completion.
- **Cursor CLI:** Show current auth status from `GET /api/setup/cursor-check`. If authenticated: green ✓ + account name. If not: "Run `cursor login` in your terminal" + Re-check button.
- **Nothing selected / Skip all:** Proceed directly to next step with no auth required.

**Fold the old standalone Cursor step (Step 4) into Part B.** It is no longer a separate wizard step — it renders inline when the user selects Cursor CLI in Part A. Remove Step 4 as a standalone step. Wizard goes from 8 steps to 7.

**State to carry forward:** The list of selected + authenticated providers must be passed to Step 5 (model picker) so it only shows models for configured providers.

---

## Task 2 — Wizard Step 5: Model Picker Scoped to Selected Providers

### Current behaviour
Model picker shows everything or nothing. Cursor CLI and OpenAI Codex do not appear as options even when authenticated.

### Required behaviour

The model picker must only show providers that the user selected and authenticated in Task 1 Step 3. If the user selected Anthropic and Cursor CLI, only Anthropic models and Cursor models appear. If they skipped all auth, show all available providers as a fallback (same as current behaviour — better than showing nothing).

**Implementation:**

```javascript
// After Step 3 completes, store selected providers
const selectedProviders = getWizardState('selected_providers'); // e.g. ['anthropic', 'cursor']

// When rendering Step 5:
const res = await fetch('/api/setup/models');
const allModels = await res.json();

const filtered = selectedProviders.length > 0
  ? allModels.filter(m => selectedProviders.includes(m.provider))
  : allModels;  // fallback: show all if user skipped

renderModelSelector(filtered);
```

**Cursor CLI models must appear.** If `hermes model list` does not include Cursor as a provider, this is a cache issue — the model cache was seeded before the Cursor patch was active or before the user authenticated. After Step 3 authenticates Cursor, call `POST /api/models/refresh` before rendering Step 5 so the cache is fresh.

**OpenAI Codex must appear** as a distinct provider group, separate from standard OpenAI.

**Auto-select logic:** If only one provider was configured, auto-select the first model from that provider so the user doesn't have to interact with the picker at all.

---

## Task 3 — Wizard Skills Step: Full Skill Manager, Not a Summary

### Current behaviour
Skills step shows a count ("you have 79 skills"), lists a few names, then shows "No hub-installed skills to check." Purely informational with no actions.

### Required behaviour

The wizard skills step must be a functional skill manager, not a summary. The user should be able to review and enable/disable skills before completing setup.

**Replace the current summary with:**

```
Skills (79 installed)

[Search skills...                    ]  [Update All]

┌─────────────────────────────────────────────────────┐
│ ● skill-name-one        v1.2.0   [Enabled  ▼]       │
│   Short description of what this skill does          │
├─────────────────────────────────────────────────────┤
│ ● skill-name-two        v0.9.1   [Enabled  ▼]       │
│   Short description                                  │
├─────────────────────────────────────────────────────┤
│ ○ skill-name-three      v2.0.0   [Disabled ▼]       │
│   Short description                                  │
└─────────────────────────────────────────────────────┘

[← Back]                          [Continue →]
```

**Behaviour:**
- Load from `GET /api/skills/list` on render. Show a loading spinner while fetching.
- Searchable: filter the list client-side as the user types in the search field.
- Enable/Disable dropdown per skill: calls `POST /api/skills/enable/{id}` or `POST /api/skills/disable/{id}`. If `GET /api/skills/capabilities` returns `enable_disable_supported: false`, replace the dropdown with a static badge (Enabled/Disabled) and show a tooltip: "Enable/disable via `hermes skills config` in terminal."
- "Update All" calls `POST /api/skills/update-all` and shows a progress indicator + summary on completion.
- "No hub-installed skills to check" only appears if the update-all result genuinely returns zero updatable skills — it must not appear as the default state before any action is taken.
- Continue → proceeds regardless of skill state. This step is not a blocker.

---

## Task 4 — Wizard Tailscale Step: Real Configuration, Not a Checkbox

### Current behaviour
Tailscale step shows an explanation and a checkbox "I have Tailscale set up (or I will skip)." No configuration is collected. No HTTPS is configured.

### Required behaviour

Replace the checkbox with a proper enable/disable toggle and configuration fields.

**Toggle: Enable Tailscale access**
- Default: off (do not assume the user has Tailscale)
- When toggled ON: reveal the configuration fields below

**Configuration fields (shown when enabled):**
```
Tailscale hostname
[ your-machine-name.tail12345.ts.net          ]
(Find this in your Tailscale admin panel or run: tailscale status)

Tailscale serve port
[ 3001                                         ]
(The local port ANIMUS runs on — default 3001)

HTTPS URL preview:
https://your-machine-name.tail12345.ts.net
```

- "Verify" button: calls `GET /api/setup/tailscale-check` with the provided hostname. Backend runs `tailscale status` or attempts a DNS lookup to verify the hostname is reachable. Returns `{ ok: bool, error?: str }`.
- If verification passes: show green checkmark + the full HTTPS URL.
- If verification fails: show the error with a suggestion ("Check that Tailscale is running: `tailscale status`").

**Backend endpoint to add** (`wizard_routes.py`):
```python
@router.get("/tailscale-check")
async def tailscale_check(hostname: str):
    import socket
    try:
        socket.getaddrinfo(hostname, None, timeout=5)
        return {"ok": True, "url": f"https://{hostname}"}
    except socket.gaierror as e:
        return {"ok": False, "error": str(e)}
```

**Save on Continue:** Persist `{ tailscale_enabled: bool, tailscale_hostname: str, tailscale_port: int }` to `config.json` via `POST /api/setup/save-config`.

**Wake lock toggle moves here:** Remove the wake lock checkbox from the Done screen entirely. Add it to the Tailscale step, below the configuration fields, shown only when Tailscale is enabled:

```
[ ] Keep screen awake while ANIMUS is generating
    (Recommended for phone use via Tailscale)
```

This is contextually correct — wake lock is only relevant when using ANIMUS as a PWA on a phone via Tailscale. Showing it on the Done screen next to an "Open ANIMUS" button made no sense.

---

## Task 5 — Wizard: Add Projects Folder Step

The wizard currently never asks the user where their projects live. Add a new step between Skills and Tailscale.

**New Step: Projects Folder**

```
Projects folder

ANIMUS organises your work into projects. Point it at a folder
on your machine and it will read project files from there.

Projects folder path
[ /home/user/projects                          ] [Browse]

[← Back]    [Skip — I'll set this up later]    [Continue →]
```

**Behaviour:**
- Text field pre-populated with a sensible default: `~/projects` (expand to full path on render).
- "Browse" is cosmetic only on a PWA — it can open a small helper text: "Type the full path to your projects folder, e.g. `/home/yourname/projects`."
- On Continue: call `POST /api/setup/save-config` with `{ projects_dir: "/full/expanded/path" }`. Expand `~` on the backend before saving.
- Validate on submit: call `GET /api/setup/check-path?path=<value>`. Backend checks the path exists and is a directory. Returns `{ ok: bool, error?: str }`.

**Backend endpoint to add** (`wizard_routes.py`):
```python
@router.get("/check-path")
async def check_path(path: str):
    from pathlib import Path
    expanded = Path(path).expanduser().resolve()
    if expanded.exists() and expanded.is_dir():
        return {"ok": True, "resolved": str(expanded)}
    return {"ok": False, "error": f"Path not found or not a directory: {expanded}"}
```

**Save:** Persist `projects_dir` to `config.json`. Expose via `GET /api/animus/client-config` so the main app can read it on startup.

**Updated wizard step order:**
1. Welcome
2. Hermes Agent check
3. Provider selection + auth (redesigned — Tasks 1 & 2)
4. Model selection (scoped — Task 2)
5. Skills manager (redesigned — Task 3)
6. Projects folder (new — Task 5)
7. Tailscale + wake lock (redesigned — Task 4)
8. Done

---

## Task 6 — Branding: Replace "Hermes" with "ANIMUS" in Plan Tab

### Current behaviour
Plan tab shows: "Each Hermes step is non-streaming and must return JSON only (no tools). Clarification and gap stages may pause for your input. The critic can halt weak ideas early."

### Required behaviour
Replace every instance of "Hermes" in the Plan tab UI with "ANIMUS". This includes:
- The descriptive text above
- Any other Plan tab UI strings referencing "Hermes" as the product name

```bash
grep -n "Hermes" animus-chat/app/index.html | grep -iv "hermes agent\|hermes_runner\|hermes-agent\|hermes model"
```

Run that grep and fix every result that refers to "Hermes" as the product name. "Hermes Agent" is acceptable where it refers to the underlying CLI tool. "Hermes" alone as a product name is not.

Add this check to `build-release.sh`:
```bash
echo "[check] No bare 'Hermes' product references in Plan tab..."
# Check for Hermes as product name (not Hermes Agent / hermes binary refs)
if grep -q "Each Hermes step\|Hermes step is\|Hermes chat" animus-chat/app/index.html; then
  echo "FAIL: bare Hermes product name found in index.html" && exit 1
fi
```

---

## Task 7 — Settings: Inference Backend — Full Provider Matrix with Auth Status

### Current behaviour
Settings shows a basic model/provider selector without auth status, without prompting for missing credentials, and without coverage of all providers.

### Required behaviour

Replace the current Settings inference backend section with a full provider matrix.

**Layout:**
```
Inference backend

Provider          Status    Model
─────────────────────────────────────────────────────
OpenAI            ● Ready   [gpt-4o                ▼]
Anthropic         ● Ready   [claude-sonnet-4-5     ▼]
Google            ○ No key  [gemini-2.0-flash      ▼]  [Add key]
Mistral           ○ No key  [mistral-large          ▼]  [Add key]
Groq              ○ No key  [llama-3.3-70b          ▼]  [Add key]
Cohere            ○ No key  [command-r-plus         ▼]  [Add key]
Together          ○ No key  [meta-llama/...          ▼]  [Add key]
xAI               ○ No key  [grok-3                 ▼]  [Add key]
DeepSeek          ○ No key  [deepseek-chat          ▼]  [Add key]
OpenAI Codex      ○ Not signed in  —                    [Sign in]
Cursor CLI        ● Ready   [auto                  ▼]

[Refresh model list ↺]
```

**Status indicators:**
- `● Ready` (green) — API key present and last test passed, or OAuth authenticated
- `○ No key` (red) — no API key configured
- `○ Not signed in` (red) — OAuth provider not authenticated
- `○ Error` (amber) — key present but last test failed (store test result in config)

**"Add key" button:** Opens an inline input field in the row for the provider. Shows a "Test" button once a value is entered. On test pass: saves key to `animus.env` via `POST /api/setup/save-config`, updates status indicator to green. On test fail: shows error inline, does not save.

**"Sign in" button (Codex and Cursor):**
- Cursor CLI: triggers `cursor login` flow. After 3 seconds shows a "Re-check" button that calls `GET /api/setup/cursor-check`.
- OpenAI Codex: triggers the Codex OAuth browser flow (same mechanism as wizard Task 1 Part B).

**Model dropdown per provider:** Populated from `GET /api/models`, filtered to that provider. "Auto" is always the first option for each provider. Changing a model calls `POST /api/animus/client-config` to persist the selection.

**Refresh model list:** Calls `POST /api/models/refresh`, then re-renders the entire matrix.

**When user selects a model from a provider with `○` status:** Show an inline prompt in the row: "This provider isn't configured yet. [Add key] / [Sign in] to use it." Do not silently allow selecting a model from a provider that won't work.

---

## Task 8 — Settings: About ANIMUS + Check for Updates

### Current behaviour
About ANIMUS modal shows version numbers and a link to docs.

### Required behaviour

**Layout change:** The "About ANIMUS" button in Settings sits next to a separate "Check for updates" button. They are two distinct buttons, not one.

**About ANIMUS modal — full product description:**

```
ANIMUS  v1.0.0

ANIMUS is a self-hosted AI command center built on top of Hermes Agent.
It gives you a unified interface to every AI provider you use — OpenAI,
Anthropic, Google, Cursor CLI, and more — running entirely on your own
hardware. Your conversations, projects, and data stay on your machine.

Features:
- Multi-provider chat with model switching per conversation
- Cron scheduler for automated AI tasks
- Skills manager for extending AI capabilities
- First-run setup wizard
- PWA — installs on Android and iPhone via Tailscale
- Token usage tracking per provider and model

Hermes Agent: v0.11.0 (2026.4.23)
Python: 3.11.15

[View docs]  [Close]
```

Write real copy here — this is what a customer reads when they want to understand what they bought.

**"Check for updates" button — auto-update from GitHub:**

When clicked, this button must:

1. Call `POST /api/animus/check-updates` on the backend.
2. Show a spinner with "Checking for updates…"
3. Display the result inline next to the button.

**Backend endpoint** (`server.py`):
```python
import subprocess
from pathlib import Path

ANIMUS_REPO = "https://github.com/SketchOTP/animus"
ANIMUS_ROOT = Path(__file__).parent.parent  # repo root

@app.post("/api/animus/check-updates")
async def check_updates():
    try:
        # Fetch latest from remote without merging
        fetch = subprocess.run(
            ["git", "fetch", "origin"],
            cwd=ANIMUS_ROOT,
            capture_output=True, text=True, timeout=30
        )
        if fetch.returncode != 0:
            return {"ok": False, "error": f"Could not reach remote: {fetch.stderr.strip()}"}

        # Compare local HEAD to origin/main
        status = subprocess.run(
            ["git", "rev-list", "--count", "HEAD..origin/main"],
            cwd=ANIMUS_ROOT,
            capture_output=True, text=True, timeout=10
        )
        commits_behind = int(status.stdout.strip() or "0")

        if commits_behind == 0:
            return {"ok": True, "status": "up_to_date", "message": "ANIMUS is up to date."}
        else:
            return {
                "ok": True,
                "status": "update_available",
                "commits_behind": commits_behind,
                "message": f"{commits_behind} update(s) available."
            }
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.post("/api/animus/apply-update")
async def apply_update():
    try:
        pull = subprocess.run(
            ["git", "pull", "origin", "main"],
            cwd=ANIMUS_ROOT,
            capture_output=True, text=True, timeout=60
        )
        if pull.returncode != 0:
            return {"ok": False, "error": pull.stderr.strip()}
        return {"ok": True, "message": "Update applied. Restart ANIMUS to use the new version."}
    except Exception as e:
        return {"ok": False, "error": str(e)}
```

**UI flow for the Check for Updates button:**

```
[Check for updates]
        ↓ click
[Checking…  ⟳]
        ↓ result
Up to date:    "✓ ANIMUS is up to date."
Update available: "↓ 12 updates available.  [Apply update]"
Error:         "✗ Could not reach GitHub. Check your connection."
```

**"Apply update" button** (shown only when updates are available):
- Calls `POST /api/animus/apply-update`.
- Shows "Updating…" spinner.
- On success: "✓ Update applied. Restart ANIMUS to use the new version." with a "Restart now" button that calls the existing restart endpoint.
- On failure: shows the git error message.

**Important:** The repo root must be a git repository with `origin` pointing to `https://github.com/SketchOTP/animus` for this to work. Verify this is the case before implementing — if the ANIMUS working directory was copied rather than cloned, the remote won't exist. Add to the install script:
```bash
# If no git remote, set it up
if ! git -C "$INSTALL_ROOT" remote get-url origin &>/dev/null; then
  git -C "$INSTALL_ROOT" remote add origin https://github.com/SketchOTP/animus.git
fi
```

---

## Updated `build-release.sh` Checks

Add alongside existing checks:

```bash
# Branding
echo "[check] No bare Hermes product name in Plan tab..."
if grep -q "Each Hermes step\|Hermes step is\|Hermes chat" animus-chat/app/index.html; then
  echo "FAIL: bare Hermes product name in index.html" && exit 1
fi

# Update endpoint exists
echo "[check] /api/animus/check-updates endpoint exists..."
if ! grep -q "check-updates" animus-chat/server.py; then
  echo "FAIL: check-updates endpoint not found in server.py" && exit 1
fi

# Projects dir in wizard
echo "[check] projects_dir in wizard save-config..."
if ! grep -q "projects_dir" animus-chat/setup_wizard/wizard_routes.py; then
  echo "FAIL: projects_dir not saved by wizard" && exit 1
fi
```

---

## Acceptance Criteria

Phase 5 is complete when ALL of the following pass:

**Wizard:**
- [ ] Step 3 shows provider checklist first, then auth fields only for selected providers
- [ ] Test button is disabled (not labelled with an error) until a key is entered
- [ ] Cursor CLI auth folds into Step 3 Part B — no standalone Cursor step
- [ ] Step 5 model picker only shows providers selected and authenticated in Step 3
- [ ] Cursor CLI and OpenAI Codex appear as model options when authenticated
- [ ] Skills step shows full scrollable skill list with enable/disable controls
- [ ] "No hub-installed skills to check" does not appear as the default state
- [ ] Projects folder step exists between Skills and Tailscale
- [ ] Projects folder validates path exists on Continue
- [ ] Tailscale step has enable/disable toggle and hostname + port fields
- [ ] Tailscale verify button checks hostname reachability
- [ ] Wake lock toggle is inside the Tailscale step, not on the Done screen
- [ ] Done screen has no wake lock checkbox
- [ ] Wizard has 8 steps in the new order (Welcome, Hermes check, Provider auth, Model, Skills, Projects, Tailscale+wake lock, Done)

**Branding:**
- [ ] Plan tab contains no instance of "Hermes" as a product name
- [ ] `build-release.sh` grep check for bare Hermes references passes

**Settings:**
- [ ] Inference backend shows all providers with green/red status indicators
- [ ] "Add key" inline flow works for API key providers
- [ ] "Sign in" button works for Cursor CLI (triggers cursor login, re-check)
- [ ] Selecting a model from an unconfigured provider shows a prompt, not a silent failure
- [ ] Model dropdowns populated from `GET /api/models`, one per provider

**About + Updates:**
- [ ] About ANIMUS modal shows full product description copy
- [ ] "Check for updates" is a separate button from "About ANIMUS"
- [ ] Check for updates calls `POST /api/animus/check-updates` and shows result
- [ ] "Apply update" button appears when updates are available
- [ ] Apply update calls `POST /api/animus/apply-update` and prompts restart
- [ ] `git remote get-url origin` in the ANIMUS repo returns the GitHub URL

**Release:**
- [ ] `./build-release.sh` passes all checks including new ones
- [ ] Zip is under 55MB (v1.0 cap; trim deferred to v1.1 if needed)

---

## Implementation Order

1. Task 6 first — branding fix is one grep + string replacement, quick win, closes a release blocker
2. Task 1 + Task 2 together — provider selection and model scoping are tightly coupled
3. Task 3 — skills step redesign
4. Task 5 — projects folder step (new step, isolated)
5. Task 4 — Tailscale step redesign + wake lock move
6. Task 7 — Settings inference backend matrix
7. Task 8 — About modal copy + check for updates
8. Update `build-release.sh` with new checks
9. Run `./build-release.sh` — confirm all pass
10. Owner re-runs smoke test wizard steps 3–8 to verify

---

*All tasks required. Do not mark Phase 5 complete until the owner has walked through the wizard again from a clean `CHAT_DATA_DIR` and confirmed the new flows.*