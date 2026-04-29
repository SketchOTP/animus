# Project knowledge (animus)

Durable lessons for future agents. Not a backlog or duplicate of `project_history.md`.

---

## Conventions

- **Session start:** Read `AGENTS.md` then `project_goal.md`, `project_status.md`, `project_history.md`, this file, and `repo_map.md` before code edits.
- **Session end:** Append `project_history.md`; update this file with new lessons or a no-new-knowledge note; refresh `project_status.md` / `repo_map.md` when state or layout changes.

---

## Stack and validation

- **Python venv:** `cd animus-chat && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt` then `.venv/bin/python -c "import server"`.
- **Release:** `./build-release.sh` (requires `rg`; scans `animus-chat`, `hermes-agent`, `installer`, `docker`, `systemd` only — root `project_goal.md` may still mention example paths). Phase 2 greps **`animus-chat/app/index.html`** (not `static/index.html`) for legacy API paths and checks `server.py` subprocess lines are tagged `# exempt:`.
- **Default port:** `CHAT_PORT` / `PORT` default **3001** in `server.py`; live Hermes on 3000 stays untouched.

---

## 290426 — Initial repo

- Repository was empty before continuity docs; there is no `package.json` / `Cargo.toml` / etc. until added.

## Bootstrap (`setup_repo.md`)

- **`setup_repo.md`** holds full steps and Appendix A (complete `AGENTS.md` body with `[repo]` placeholder) so another repo can mirror this structure. Policy edits should stay in sync across `AGENTS.md`, `.cursorrules`, `CLAUDE.md`, and `.cursor/rules/operating_rules.md` (use `cmp` to verify).

## Token and navigation (290426)

- **`repo_map.md` first:** Small tree here—open listed paths only; when code lands, keep the map current so agents avoid whole-repo walks.
- **`project_history.md`:** Append new entries at EOF; do not load the full log just to add a line. Skim recent entries for context.
- **Mirrors:** After editing `AGENTS.md`, run `cmp` copies: `cp AGENTS.md .cursorrules CLAUDE.md .cursor/rules/operating_rules.md` (adjust paths); one source of truth.
- **`setup_repo.md`:** Appendix A must stay aligned with `AGENTS.md` (same policy body; `[repo]` vs real name is the only intentional difference).

---

## 290426 — ANIMUS bootstrap

- **`hermes skills` not `hermes skill`:** route modules call `hermes skills …` per current CLI.
- **`build-release.sh` password grep:** use word boundary (`\b5206\b`) so `uv.lock` numeric hashes do not false-positive.
- **Skills enable/disable (Option C):** `POST /api/skills/enable|disable/{id}` returns **200** with `{ ok: false, error: "…hermes skills config…" }`; UI hides toggles. Do not reintroduce 501 for these routes.

## 290426 — Phase 2 UI / wizard

- **Primary UI file:** `animus-chat/app/index.html` (single-file PWA). Wizard + tooltips live here; acceptance greps target this path.
- **Cron manual run:** UI uses `POST /api/cron/run/{id}` (alias of trigger). List uses `GET /api/cron/list`.

## 290426 — Phase 3 alignment

- **`chat_data_dir()`** in `hermes_runner.py` matches `server.DATA_DIR` (CHAT_DATA_DIR / ~/.hermes/.env / default `~/.hermes/chat`). Wizard `config.json` + model cache use it — avoids wizard living in `./data` while chats live under `~/.hermes/chat`.
- **Wake lock:** persisted via `GET/POST /api/animus/client-config` and wizard `save-config` `wake_lock`; client loads on init after wizard.
- **Skills toggles:** `GET /api/skills/capabilities` drives `#skills-container[data-enable-toggle]`; CSS hides `.skill-enable-toggle` when false.
- **Smoke doc:** `scripts/phase3-smoke-checklist.md` — run on a host with Docker + gateway; update `project_status.md` table with results.
- **Smoke setup:** there is often **no** `animus-chat/data/`; wizard + chats use **`chat_data_dir()`** (`CHAT_DATA_DIR` → `~/.hermes/.env` → `~/.hermes/chat`). Use `CHAT_DATA_DIR=/tmp/...` for a clean wizard without touching your real `~/.hermes/chat`.
- **Support / “where did my data go?”** Ask which resolution step applies: `CHAT_DATA_DIR` env, `HERMES_CHAT_DATA_DIR`, keys in `~/.hermes/.env`, or default `~/.hermes/chat`. **`CHAT_DATA_DIR`** is the clean escape hatch for smoke tests and for users who want a dedicated folder.
- **Docs / examples:** Prefer **`python3`** or **`animus-chat/.venv/bin/python`** in shell snippets — `python` alone is often missing on Debian/Ubuntu.

## Hermes Agent bundle vs upstream

- **Smoke Step 2 (host):** bundled **v0.11.0 (2026.4.23)**, Python 3.11.15; upstream was **778 commits ahead** at that check — not a v1.0 blocker (shipped snapshot is intentional).
- **Operators:** Do **not** run **`hermes update`** inside ANIMUS expecting to keep patch alignment; see top of **`docs/hermes-agent-patches.md`**.
- **v1.1+:** Rebasing ANIMUS patches onto newer upstream Hermes Agent is a scheduled merge/re-test effort; the patch audit doc is the merge checklist.

## 290426 — Phase 5 (wizard + settings + updates)

- **Wizard flow:** Step order is 0 Welcome → 1 Hermes Agent → 2 provider checklist + inline auth (no standalone Cursor step) → 3 default model (uses `wizard_ready_providers` / `wizard_selected_providers` from `GET /api/animus/client-config` to filter; refresh models after Cursor when needed) → 4 skills manager (`/api/skills/list` + enable/disable when capabilities allow) → 5 projects folder (`GET /api/setup/check-path`, saves `projects_dir`) → 6 Tailscale (`GET /api/setup/tailscale-check`) + wake lock only when Tailscale enabled → 7 Done (no wake checkbox).
- **Settings inference:** `GET /api/setup/provider-status` drives the matrix; `POST /api/setup/test-key` + `save-config` keys update env; Codex: `POST /api/setup/codex-auth-start` spawns background `hermes auth add openai-codex` and returns `poll_id` — UI polls `GET /api/setup/codex-auth-status/{poll_id}` every 3s (180s client timeout); session probe is `GET /api/setup/codex-auth-session`. Cursor: `POST /api/setup/cursor-login-start` + re-check.
- **Updates:** `POST /api/animus/check-updates` / `apply-update` run `git` from `server.py`’s monorepo parent (`Path(__file__).parent.parent`); requires **`origin`**, a resolvable **`origin/main`**, and a **local `HEAD`** (e.g. `git fetch origin` then `git checkout -b main origin/main` on a fresh init — `git init` + `remote add` alone leaves no commits / no `HEAD..origin/main`).
- **Smoke Python venv:** Do not create arbitrary venvs under `animus-chat/` (e.g. `.venv-smoke`): `build-release.sh` sanitisation greps the whole `animus-chat/` tree and **fails** on pip vendor numeric tokens. Use the repo’s ignored `.venv/` at repo root or `/tmp/...` for throwaway envs.
- **Release checks:** `build-release.sh` greps Plan-tab strings `Each Hermes step|Hermes step is|Hermes chat`, asserts `check-updates` in `server.py`, and `projects_dir` in `wizard_routes.py`.
- **`GET /api/version`:** includes `python` short version for About modal.

## Go-live smoke (operator)

- **Before step 1:** Open **`animus.env`** and/or **`~/.hermes/.env`** and confirm at least one **real** provider key (not placeholder / not expired). Wizard may proceed without it, but **step 3 (key test)** and **step 9 (chat)** give misleading results if the key is bad.
- **During step 9:** Watch **browser Network** (SSE) or **server stdout**. The first assistant stream chunk that includes a **`usage`** block means the **token tracker** can populate once you open it — you may see proof before opening Settings → Token tracker.
- **Screenshots (Gumroad):** Capture **during** the smoke run (wizard welcome, chat with badge, cron list) while **`CHAT_DATA_DIR`** still shows first-run UI. After teardown + return to normal data, the wizard is gone unless you reset **`config.json`** or start another throwaway **`CHAT_DATA_DIR`** session.
- **Step 16 (`./build-release.sh`):** Run **last**, from **repo root**, in a **clean shell** — **`unset CHAT_DATA_DIR`** after smoke teardown so the release build is not tied to the temp tree. The script does not need smoke data, but avoiding a stray env var avoids confusion.

## No-new-knowledge template

When a session adds nothing durable, append:

```text
DDMMYY — No new durable knowledge (routine doc-only / trivial change).
```
