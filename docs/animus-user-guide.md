# ANIMUS user guide

This document is the **official in-app Help source**. The Help assistant only uses what is written here.

## What ANIMUS is

ANIMUS is a **self-hosted web chat** for working with AI coding agents (via a **Hermes gateway**). You run the ANIMUS chat server and gateway on your machine or server; the browser UI talks to your gateway using a configured API key (`HERMES_API_KEY` in `animus.env`).

ANIMUS is **not** a hosted SaaS: you control data, models, and integrations.

## First visit: wizard

On first run, ANIMUS shows a **setup wizard**. Typical steps include:

- Checking that the **Hermes agent / gateway** is reachable.
- Choosing and testing **AI providers** (API keys or OAuth where supported).
- Picking a **default chat model** for the active provider.
- Optional: **skills** folder, **projects** directory, **Tailscale**, **wake lock** (when Tailscale is enabled).

Finish the wizard to reach the main **Chats** UI. You can change many options later under **Settings**.

## Chats vs projects

- **Chats** (default sidebar): conversations **without** a project. Good for quick questions.
- **Projects**: each project has a **name**, **color**, and **path** (workspace on disk). Opening a project filters the sidebar to that project’s chats and adds **project tools** (workspace files: `project_goal.md`, `repo_map.md`, `project_history.md`, `notes.md` when configured).

**New chat** creates a conversation. The purple **New chat** button uses your **active inference provider and model** from Settings.

## Sidebar layout

- **Projects** list: click a project to enter **project mode**. Click **◀** (desktop) to hide or shrink the sidebar (see Settings → Sidebar).
- **Chats** are grouped by **Today / Yesterday / This week / This month**. Group headers collapse and expand.
- In a project, **Notifications** lists **notification threads** (for example **Cron updates**). **Chats** lists normal threads for that project.

### Notification unread

ANIMUS tracks how many **new messages** arrived in notification threads since you last read them (per thread). **Settings → Notifications → Show unread badge** toggles the count badge next to the Notifications label. Unread **notification rows** use the same **accent (purple) background and white text** as **New chat** until you open that thread or expand the Notifications section (which marks notification threads read).

## Settings overview

Open **Settings** from the tab bar. Sections include:

1. **Sidebar** — behavior of the sidebar collapse control (hide vs shrink, width tier).
2. **Notifications** — when run-finished notifications fire (always / screen off / off), permission test, **unread badge** toggle (switch).
3. **Screen** — **Keep screen awake** (Wake Lock API) while ANIMUS is working (toggle).
4. **Read aloud** — **Browser** vs **Piper** (server-side) voice engine; Piper voice picker when Piper is installed on the server.
5. **Inference backend** — matrix of providers; **Model** picker for the active provider. This is what chat requests use.
6. **Integrations** — e.g. **Slack** (webhook / bot token).
7. **Connections** — **SSH hosts** for remote project roots.
8. **Token usage** — opens the token tracker (reported usage from chat and related calls).
9. **HELP** — opens this guide and the **Ask ANIMUS** bar (answers from this guide only).
10. **Server controls** — restart gateway / chat server (operator actions).
11. **Chat history** — purge local+server history (destructive).

Server-backed prefs (e.g. wake lock, `tts_backend`, `cron_timezone`, `projects_dir`) sync to **`config.json`** under the chat data directory (see Data locations).

## Models and providers

The **active** row in the inference matrix is what **new messages** use. The **Model** dropdown lists models for the selected backend (from gateway catalog or fallbacks). Some backends support **Auto** routing (e.g. OpenAI Codex): the gateway may pick a concrete model per request.

If chat fails with **configuration** or **upstream** errors, check `animus.env` keys and gateway logs.

## Read aloud (TTS)

- **Browser**: Web Speech API; works everywhere; pick a voice from the list.
- **Piper**: runs on the **ANIMUS server**; requires the `piper` binary (`PATH` or `PIPER_BIN`) and voice models. The server can download default voices when Piper is present (unless `SKIP_ANIMUS_PIPER_VOICES=1`). See **`docs/tts.md`**.

## Token usage tracker

**Settings → Token usage → Open token usage tracker** shows usage aggregates (provider, model, source). Usage is recorded when the gateway returns token counts on chat streams and for some other API paths. It helps compare cost and verify reporting.

## Cron jobs

ANIMUS can list and manage **cron jobs** tied to Hermes on the gateway host. Jobs can deliver output into a project’s **Cron updates** notification thread. Each project can show **cron** controls and a **delivery / project ID** hint for external schedulers.

Timezone for cron UI may be stored as **`cron_timezone`** in client config.

## Skills

The **Skills** UI lists Hermes skills, enables/disables when the CLI supports it, and may offer **create skill** (writes `SKILL.md` under the user skills directory). Capabilities come from **`GET /api/skills/capabilities`**.

## SSH hosts and remote projects

Under **Settings → Connections**, add **SSH hosts** (alias, hostname, user, key or password, options). When **creating or editing a project**, you can mark it **remote** and pick an SSH host plus **remote project path**. See **`docs/ssh.md`**.

## Slack

**Settings → Integrations → Slack** can configure webhook and/or bot token and channel; the server writes **`SLACK_*`** entries into **`animus.env`**. Restart may be needed for the gateway to pick up env changes.

## Updates

**Settings** may offer **Check for updates** / **Apply update** when the install is a **git** checkout with `origin`. Zip installs without git history cannot use apply-update as shipped.

## Data and important paths

- **Chat data directory** (`CHAT_DATA_DIR` or defaults documented in INSTALL): holds conversations sync, **`config.json`** (client prefs), token log **`token_usage.jsonl`**, etc.
- **`animus.env`** at the ANIMUS **monorepo root**: gateway URL, API key, Piper paths, Slack vars, etc.
- **`docs/`** in the repo: **`tts.md`**, **`ssh.md`**, **`hermes-agent-patches.md`**, **`models.md`**, this **`animus-user-guide.md`**.

Do not paste secrets into the Help chat; the Help bot does not store them, but the channel may log requests on the server.

## Wake lock

When enabled, the UI requests a **screen wake lock** while a chat stream is active so phones stay awake. It is released when streaming ends. If the browser denies the lock, ANIMUS continues without it.

## Plan tab (if present)

Some builds expose a **Plan** tab for structured multi-step work with Hermes; usage recording may attach to plan steps when the gateway returns usage metadata.

## Troubleshooting (short)

| Symptom | What to check |
|--------|----------------|
| Chat says API key missing | Wizard or **`animus.env`** `HERMES_API_KEY` |
| Gateway unreachable | `HERMES_API_URL`, systemd units, firewall |
| Piper silent | `piper` on server PATH, voices dir, **`docs/tts.md`** |
| Cron edits fail | `HERMES_HOME` alignment between chat server and gateway |
| SSH errors | **`docs/ssh.md`**, host key options, keys on disk |

## Frequently asked questions

### Where is my chat data stored?

Under the **chat data directory** (often set via `CHAT_DATA_DIR`, or defaults described in **INSTALL.md**). That folder holds synced conversations, **`config.json`** for client preferences, **`token_usage.jsonl`**, and related files—not inside the git repo’s `animus-chat/data/` unless you pointed `CHAT_DATA_DIR` there.

### What is the difference between a chat and a project?

**Chats** live in the default sidebar and are not tied to a workspace path. **Projects** bind conversations and tools to a **folder on disk** (and optional SSH remote). Open a project from the sidebar to see that project’s chats, **Notifications**, and cron UI.

### Why does the Help assistant refuse to change something for me?

**Ask ANIMUS** is **read-only**: it only explains what the user guide says. It cannot run commands, edit `animus.env`, or change Settings—that is by design so it does not pretend to act on your system.

### How do I pick which AI model chats use?

**Settings → Inference backend**: set the **active** provider row, then choose **Model** for that provider. **New chat** uses that combination. Some providers offer **Auto** routing; the gateway resolves the concrete model per request where supported.

### Piper / Read aloud does nothing—what should I check?

The **Piper** engine runs on the **server** hosting ANIMUS, not in the browser. You need the **`piper`** binary on `PATH` or **`PIPER_BIN`**, voice models under **`PIPER_VOICES_DIR`** or default dirs, and outbound HTTPS if the server auto-downloads voices. See **`docs/tts.md`**.

### What are “Cron updates” in Notifications?

When a **cron job** is configured to deliver into a project, runs can append messages to a **Cron updates** thread under **Notifications** for that project. Unread counts and purple highlighting follow **per-thread** read state until you open the thread or expand the Notifications section.

### How do SSH hosts relate to projects?

Add hosts under **Settings → Connections → SSH hosts**. When creating or editing a **remote** project, you pick a host alias and **remote project path**. ANIMUS uses that for workspace and agent context; see **`docs/ssh.md`**.

### Slack is configured but nothing posts—why?

The server writes **`SLACK_*`** variables into **`animus.env`**. The **gateway** (or related services) may need a **restart** to load new environment values. Confirm webhook URL or bot token and channel in Settings.

### Can I use ANIMUS without Tailscale?

Yes. Tailscale is **optional** (wizard and Settings). Without it, open ANIMUS on `localhost`, LAN IP, or your own HTTPS setup as documented in **INSTALL.md**.

## HELP and “Ask ANIMUS”

The **HELP** button opens this guide in the app. The **Ask ANIMUS** field sends your question to the **same configured chat model** as normal chat, but with **strict instructions**: the model must answer **only from this guide**, must **not** claim to change settings or run commands, and must admit when the guide does not cover a topic. It is **read-only help** — not an agent that edits your system.

For product direction and release scope, maintainers use **`project_goal.md`** in the repository (developer-facing, not shown inside the default Help pane).

---

*End of ANIMUS user guide (in-app).*
