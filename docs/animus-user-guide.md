# ANIMUS user guide

This document is the **official in-app Help source**. The Help assistant only uses what is written here.

## What ANIMUS is

ANIMUS is a **self-hosted web chat** for working with AI coding agents (via a **Hermes gateway**). You run the ANIMUS chat server and gateway on your machine or server. The chat **server** (not the browser) calls your gateway at **`HERMES_API_URL`**. If your Hermes gateway uses **`API_SERVER_KEY`** in **`~/.hermes/.env`**, current ANIMUS builds reuse that value automatically when **`HERMES_API_KEY`** is blank (and **`install.sh`** copies it into **`animus.env`** when possible). Set **`HERMES_API_KEY`** manually only when you need a different token or the gateway has no Hermes env file on the same machine.

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
- **Projects**: each project has a **name**, **color**, and **path** (workspace on disk). Opening a project filters the sidebar to that project’s chats and adds **project tools** (workspace files: `project_goal.md`, `project_status.md`, `project_knowledge.md`, `repo_map.md`, `project_history.md`, `notes.md` when configured).

**New chat** creates a conversation. The purple **New chat** button uses your **active inference provider and model** from Settings.

## Sidebar layout

- **Projects** list: click a project to enter **project mode**. On desktop, **◀** in the sidebar header either **shrinks** the panel to a narrow or medium width or **collapses** it completely, depending on **Settings → Sidebar** (**Shrink** vs **Collapse**). Use the **▶** rail tab to restore a hidden sidebar.
- **Chats** are grouped by **Today / Yesterday / This week / This month**. Group headers collapse and expand.
- In a project, **Notifications** lists **notification threads** (for example **Cron updates**). **Chats** lists normal threads for that project.

### Notification unread

ANIMUS tracks how many **new messages** arrived in notification threads since you last read them (per thread). **Settings → Notifications → Unread badge on Notifications** toggles the count badge next to the Notifications label in the sidebar. Unread **notification rows** use the same **accent (purple) background and white text** as **New chat** until you open that thread or expand the Notifications section (which marks notification threads read).

## Settings overview

Open **Settings** from the tab bar. Each major block has at most **one** **(i)** info control in the **top-right** of that block, summarizing everything inside it.

Sections include:

1. **Sidebar** — choose **Shrink** (keep a slim panel) or **Collapse** (hide completely) for the header **◀** control. When **Shrink** is on, pick **Narrow** or **Medium** width (radio buttons).
2. **Notifications** (collapsible) — when run-finished notifications fire (always / screen off / off), browser notification permission + **Test**, and **Unread badge on Notifications** (toggle).
3. **Screen wake** — toggle only (label **Screen wake**); the **(i)** explains Wake Lock behavior (Chrome / Edge / Android PWA).
4. **Read aloud** (collapsible) — **Piper** (server) vs **Browser** (Web Speech), voice list, preview / refresh; Piper needs the server binary and models (**`docs/tts.md`**).
5. **Inference** (collapsible) — provider matrix + **Model** picker for the active provider; **About**, **Check updates**, **Refresh models**.
6. **Messaging** (collapsible) — Hermes **gateway platforms** (Telegram, Discord, **Slack**, …): turn each **On**, open **Configuration**, save credentials to **`~/.hermes/.env`**, then **Restart gateway**. If you already had **`SLACK_BOT_TOKEN`** in **`animus.env`** but not in Hermes yet, ANIMUS may **import it once** when the Messaging list loads (see **Slack** below).
7. **SSH hosts** — aliases for remote project roots (**`docs/ssh.md`**).
8. **Token usage** — separate tab: usage aggregates and CSV export.
9. **HELP** — this guide + **Ask ANIMUS** (read-only).
10. **Server** — restart gateway / chat server, and **Purge all chat history** (destructive).

Server-backed prefs (e.g. wake lock, `tts_backend`, `cron_timezone`, `projects_dir`) sync to **`config.json`** under the chat data directory (see Data locations).

## Models and providers

The **active** row in the inference matrix is what **new messages** use. The **Model** dropdown lists models for the selected backend (from gateway catalog or fallbacks). Some backends support **Auto** routing (e.g. OpenAI Codex): the gateway may pick a concrete model per request.

If chat fails with **configuration** or **upstream** errors, check `animus.env` keys and gateway logs. If you see a very old message about **`HERMES_API_KEY` not configured** after upgrading, your **`animus-chat/server.py`** may still be an older file on disk—confirm with **`GET /api/version`** (`chat_server_rev` and **`chat_proxy_blocks_on_missing_hermes_api_key`: false**). **`INSTALL.md`** describes patching from a newer zip: use **`installer/sync-animus-chat-from-zip.sh`** when **`installer/`** exists, or **`animus-chat/sync-from-release-zip.sh`** when you only have the **`animus-chat/`** folder.

## Read aloud (TTS)

- **Browser**: Web Speech API; works everywhere; pick a voice from the list.
- **Piper**: runs on the **ANIMUS server**; requires the `piper` binary (`PATH` or `PIPER_BIN`) and voice models. The server can download default voices when Piper is present (unless `SKIP_ANIMUS_PIPER_VOICES=1`). See **`docs/tts.md`**.

## Token usage tracker

**Settings → Token usage → Open token usage tracker** shows usage aggregates (provider, model, source). Usage is recorded when the gateway returns token counts on chat streams and for some other API paths. It helps compare cost and verify reporting.

## Cron jobs

ANIMUS can list and manage **cron jobs** tied to Hermes on the gateway host. Jobs can deliver output into a project’s **Cron updates** notification thread. Each project can show **cron** controls and a **delivery / project ID** hint for external schedulers.

If a cron job has a project **workdir**, Hermes runs it from that directory and auto-checks the project continuity files before the job starts. This keeps scheduled runs aligned with the same project rules used by normal chat/project refresh flows.

If delivery is **Slack**, that path uses the **webhook** in **`animus.env`** (**`SLACK_WEBHOOK_URL`**), not the Messaging bot token—configure the webhook in **`animus.env`** and restart ANIMUS. Use **Settings → Messaging → Slack** for the Hermes **bot**.

Timezone for cron UI may be stored as **`cron_timezone`** in client config.

## Project continuity system (memory + map)

When a project folder is added, updated, or refreshed, ANIMUS/Hermes ensures a continuity set exists under that project root:

- Governance mirrors: **`AGENTS.md`**, **`CLAUDE.md`**, **`.cursorrules`** (kept synchronized to the same policy text)
- Project memory/map docs: **`project_goal.md`**, **`project_status.md`**, **`project_knowledge.md`**, **`project_history.md`**, **`repo_map.md`**, **`notes.md`**

Project workspace **Refresh** re-checks this set, repairs missing/stale files, and regenerates **`repo_map.md`**. The intended outcome is faster, lower-token navigation in project conversations because agents can rely on concise per-project goal/status/knowledge/map files instead of broad repo scans.

## Skills

The **Skills** UI lists Hermes skills, enables/disables when the CLI supports it, and may offer **create skill** (writes `SKILL.md` under the user skills directory). Capabilities come from **`GET /api/skills/capabilities`**.

## SSH hosts and remote projects

Under **Settings → SSH hosts**, add hosts (alias, hostname, user, key or password, options). When **creating or editing a project**, you can mark it **remote** and pick an SSH host plus **remote project path**. See **`docs/ssh.md`**.

## Slack

There are **two** Slack-related mechanisms:

- **Gateway bot (Hermes)** — configure under **Settings → Messaging → Slack**: **Bot token** and optional **home channel** are stored in **`~/.hermes/.env`** (and enable flags / home channel in **`~/.hermes/config.yaml`**). Restart the **gateway** after saving. If **`SLACK_BOT_TOKEN`** (and optionally **`SLACK_DEFAULT_CHANNEL`**) already exist in repo-root **`animus.env`** from an older setup but Hermes had **no** bot token yet, ANIMUS may **import** those values into Hermes env **once** when Messaging loads (status text explains when that happens).
- **Incoming webhook (ANIMUS server / cron)** — **`SLACK_WEBHOOK_URL`** (and related vars) still live in **`animus.env`** at the ANIMUS monorepo root for features that post via webhook (for example **Cron** delivery method **Slack**). Edit **`animus.env`** and restart the **ANIMUS chat server** when you change webhook settings.

## Updates

**Settings → Check for updates** compares your **`VERSION`** file to a manifest at **`ANIMUS_UPDATE_URL`** (in **`animus.env`**). When a newer version is listed, **Apply update** downloads the release zip and unpacks it over the install. Leave **`ANIMUS_UPDATE_URL`** unset to skip update checks. See **`docs/BUYER_UPDATES.md`**.

## Data and important paths

- **Chat data directory** (`CHAT_DATA_DIR` or defaults documented in INSTALL): holds conversations sync, **`config.json`** (client prefs), token log **`token_usage.jsonl`**, etc.
- **`animus.env`** at the ANIMUS **monorepo root**: gateway URL, optional gateway bearer (**`HERMES_API_KEY`**), Piper paths, Slack vars, etc.
- **`docs/`** in the repo: **`tts.md`**, **`ssh.md`**, **`hermes-agent-patches.md`**, **`models.md`**, this **`animus-user-guide.md`**.

Do not paste secrets into the Help chat; the Help bot does not store them, but the channel may log requests on the server.

## Screen wake (wake lock)

**Settings → Screen wake** toggles whether the UI requests a **screen wake lock** while a chat stream is active so phones stay awake. The lock is released when streaming ends. If the browser denies the lock, ANIMUS continues without it (see **(i)** in Settings for client support notes).

## Plan tab

The **Plan** tab runs a **multi-agent pipeline** (idea → clarification → handoff) **only while the tab is open**. Use the **play** control to **run** the pipeline and the **square stop** control to **abort** a run. Clarification and gap stages open a **modal** with one answer box per question — **Submit** continues the run; **Cancel** (or Esc) saves your partial answers so you can tap **▶** on the saved row later. The saved row shows **time + date stamp** and a one-line **starting-idea** summary, with **✎** (scroll to idea), **▶** (resume), and **−** (delete draft). After a successful **handoff**, you can save **`project_plan.md`** into a project folder. Token usage may be recorded when the gateway returns usage metadata on plan steps.

## Troubleshooting (short)

| Symptom | What to check |
|--------|----------------|
| Chat says API key missing / old “HERMES_API_KEY not configured” text | On current builds, gateway bearer is **optional** when the gateway has no key; that exact sentence usually means an **old** `server.py` is still running—upgrade or patch **`animus-chat/`** from a newer zip (**`INSTALL.md`**). If the gateway **does** require a token, set **`HERMES_API_KEY`** in **`animus.env`**. |
| Chat says **Invalid API key** (401) | Hermes **`API_SERVER_KEY`** and ANIMUS **`HERMES_API_KEY`** must match. See **`INSTALL.md`** — check **`curl …/api/version`** for **`gateway_openai_models_ok`** and **`gateway_bearer_source`**. |
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

Add hosts under **Settings → SSH hosts**. When creating or editing a **remote** project, you pick a host alias and **remote project path**. ANIMUS uses that for workspace and agent context; see **`docs/ssh.md`**.

### Slack is configured but nothing posts—why?

Depends which path you use: **Cron → Slack** needs **`SLACK_WEBHOOK_URL`** in **`animus.env`** and a restart of the **ANIMUS** server. **Hermes bot** Slack needs **Settings → Messaging → Slack** ( **`~/.hermes/.env`** ) and a **gateway** restart. Confirm you edited the right file and restarted the right process.

### Can I use ANIMUS without Tailscale?

Yes. Tailscale is **optional** (wizard and Settings). Without it, open ANIMUS on `localhost`, LAN IP, or your own HTTPS setup as documented in **INSTALL.md**.

## HELP and “Ask ANIMUS”

The **HELP** button opens this guide in the app. The **Ask ANIMUS** field sends your question to the **same configured chat model** as normal chat, but with **strict instructions**: the model must answer **only from this guide**, must **not** claim to change settings or run commands, and must admit when the guide does not cover a topic. It is **read-only help** — not an agent that edits your system.

For product direction and release scope, maintainers use **`project_goal.md`** in the repository (developer-facing, not shown inside the default Help pane).

---

*End of ANIMUS user guide (in-app).*
