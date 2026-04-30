# Gumroad delivery — ANIMUS

Concise guide for packaging and listing. Full product criteria remain in `project_goal.md` (Gumroad sections).

## What buyers receive

The release artifact is **`animus-vX.Y.Z.zip`** from the repository root:

```bash
./build-release.sh
```

The zip is the **monorepo tree** with exclusions applied by `build-release.sh` (no `.git`, no `animus.env`, no `data/`, no local `.venv`, no top-level `node_modules`, plus **dev-only trims**: `Ghost3D/`, `hermes-agent/tests/`, `hermes-agent/website/`, `hermes-agent/scripts/whatsapp-bridge/node_modules/`, **`hermes-agent/.cursor/`**, and **internal ANIMUS continuity** files: `project_*.md`, `repo_map.md`, `AGENTS.md`, `CLAUDE.md`, `.cursorrules`, `.cursor/`, `setup_repo.md`, mirrored `animus-chat/repo_map.md` / `project_history.md` / `setup_repo.md` — see `build-release.sh` comments). **Clone the Git repo** for ANIMUS continuity files and root `AGENTS.md`; bundled **`hermes-agent/AGENTS.md`** is also omitted from the zip (use the public Hermes repo for upstream contributor docs). Buyers unzip and run **`installer/install.sh`** per **`START_HERE.txt`** and **`INSTALL.md`**. WhatsApp bridge users: see **INSTALL.md** troubleshooting.

## In-app updates (manifest + zip, no git)

Buyers never need git. **`ANIMUS_UPDATE_URL`** in **`animus.env`** (copied from **`animus.env.example`**) must point at a **GET**-able JSON manifest (default example: **`https://animusai.vercel.app/api/latest.json`**). Recommended: deploy the separate **`animus-site`** repo to **Vercel** (marketing site + Redis-backed API) — see that repo’s **`README.md`**. Self-hosted **Tailscale** or **`animus-update-server/`** (Python) remain valid alternatives. Before each **`./build-release.sh`**, set the production URL in **`animus.env.example`**. Publish flow: build zip → upload to Gumroad → publish the manifest (**`POST …/api/admin/publish`** with JSON + **`x-admin-token`**, or the seller page **`/seller-publish.html`** on **`animus-site`** with Vercel Blob configured) → buyers see the banner on next launch. **`install.sh`** already creates **`animus.env`** from **`animus.env.example`** when missing; **`preflight.sh`** does the same.

## Before you upload (seller checklist)

**Local admin token (optional):** keep Vercel **`ADMIN_TOKEN`** in **`seller-private/ADMIN_TOKEN`** (one line, file is gitignored and never in the buyer zip — see **`seller-private/README.md`**).

1. Bump **`VERSION`** if this is a new release line.
2. Run **`./build-release.sh`** on the exact commit you ship; confirm it exits **0**.
3. Open the zip and spot-check: **no `animus.env` or `animus-chat/animus.env`** (only `*.example`), **no `animus-chat/data/`**, **`START_HERE.txt` present**. (`build-release.sh` now fails the build if a raw env or chat data dir slips in.)
4. Smoke-test a **clean** install from the zip on a machine (wizard, one chat, optional cron) — see `scripts/phase3-smoke-checklist.md`.
5. Attach **`animus-vX.Y.Z.zip`** as the Gumroad product file (or host a signed URL if you move large files off Gumroad later).

## Suggested listing copy (edit as you like)

**Title (example)**  
ANIMUS — Self-hosted AI workspace (Hermes Agent bundle)

**Short summary**  
Install on your Mac or Linux box, open the browser, and run chat, projects, cron jobs, and skills behind your own gateway. Includes the ANIMUS UI and a bundled Hermes Agent tree — no separate “Hermes Chat” install.

**Bullets**

- Local-first: your disk, your API keys, your gateway URL  
- First-run wizard + Settings for providers, Tailscale hints, TTS, SSH hosts  
- Piper voice bundle optional at install; Docker path documented in `INSTALL.md`  
- MIT license — see `LICENSE`; Hermes Agent may carry additional notices under `hermes-agent/`

**Requirements (set expectations)**  
Python 3.10+, ~2 GB disk for agent source (excluding optional Piper voices), a running OpenAI-compatible **gateway** (or install/configure from bundled `hermes-agent/` per upstream docs).

## After-purchase message (email / Gumroad “thank you”)

You can paste:

> Thanks for purchasing ANIMUS. Unzip the archive, then follow **START_HERE.txt** at the top of the folder. If anything fails, check **INSTALL.md** and your Python version (3.10+). Updates: the app checks **`ANIMUS_UPDATE_URL`** automatically; see **docs/BUYER_UPDATES.md** or re-download from **gumroad.com/library**. Replies to this email with your OS and the last error line help a lot.

## Updates link

Point “Check for updates” / your site to the URL where you publish new zips (Gumroad product updates or a changelog page). Placeholder used in-app historically: replace with your real Gumroad or docs URL when ready.

## Zip size

`project_goal.md` targets **≤ 55 MB** for v1.0. `build-release.sh` **fails** if the zip is larger. Built-in trims (see script comments) usually keep the artifact **well under** the cap; document any extra excludes in release notes.
