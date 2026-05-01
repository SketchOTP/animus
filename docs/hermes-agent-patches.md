# Hermes Agent — ANIMUS patch record

**Bundled version:** v0.11.0 (2026.4.23). **Upstream drift:** as of this ANIMUS release, upstream `hermes-agent` was **778 commits ahead** of the bundled tree (measured on the release host). Customers receive this **patched, tested** snapshot — **do not** run `hermes update` (or similar in-place upstream sync) inside the ANIMUS install; it can **overwrite** the customisations recorded below and break gateway/chat alignment until re-patched.

**v1.1+ planning:** Rebasing ANIMUS’s patches onto a newer Hermes Agent is a real upgrade task with real merge risk. The sections in this document are the checklist that makes that manageable when you choose to do it.

## How to read this doc

Each section summarizes how the bundled `hermes-agent/` in ANIMUS differs from the upstream public repository, and why that matters for releases.

## Upstream

- Remote: `https://github.com/NousResearch/hermes-agent.git`
- The copy under `hermes-agent/` at the ANIMUS monorepo root was taken from the owner's live install (not a fresh upstream clone). It may be **ahead/behind** `origin/main`. Smoke **Step 2** (2026-04-29) reported bundled **v0.11.0 (2026.4.23)** with upstream **778 commits** ahead — re-verify drift before each release (e.g. `git fetch origin && git rev-list --count HEAD..origin/main` from `hermes-agent/`).

## Patch 1 — Local commits and working tree

**File(s):** entire `hermes-agent/` tree  
**Type:** configuration change / fork alignment  
**What it does:** The vendored tree may contain **local commits** and **modified files** versus `origin/main` (see recent `git log` on the bundle host).  
**Why it exists:** ANIMUS ships a known-good agent + gateway snapshot with the chat UI.  
**Risk if removed:** Replacing the folder with a fresh upstream clone without re-running ANIMUS acceptance tests can break gateway/chat alignment, cron paths, or Cursor integrations.  
**Test to verify:**

```bash
cd hermes-agent
git status -sb
git log --oneline -20
git diff origin/main --stat
```

## Patch 2 — Cursor / IDE integrations

**File(s):** `gateway/platforms/api_server.py`, Cursor-related shims (see tree)  
**Type:** provider addition / IDE integration  
**What it does:** Upstream gateway and tooling reference Cursor-driven flows (for example subprocess shims such as `cursor-agent`, `CURSOR_API_KEY`, or logged-in Cursor CLI).  
**Why it exists:** ANIMUS users select Cursor-backed backends from the chat UI.  
**Risk if removed:** Cursor-backed chat and agent tooling stops working for installs that rely on this snapshot.  
**Test to verify:** In ANIMUS Settings, select the Cursor provider and send a test message. The response should arrive using Cursor's underlying model. The per-message provider badge should show `cursor` or the specific Cursor model name.

**ANIMUS rule:** do not re-implement these integrations from scratch; carry forward the same files and CLI behaviour as in the bundled agent, then re-verify after each merge from upstream.

## Patch 3 — Skills and cron CLI surface

**File(s):** `hermes-agent/tools/skills_tool.py`, `hermes-agent/cron/jobs.py`, `hermes-agent/cron/scheduler.py` (indirectly)  
**Type:** new feature (CLI + data layout)  
**What it does:** Hermes Agent exposes `hermes skills …` and `hermes cron …` subcommands. Job output is written under `~/.hermes/cron/output/<job_id>/<timestamp>.md` (see `cron/jobs.py`). ANIMUS routes (`skills_routes.py`, `cron_routes.py`) wrap the CLI and local stores so the browser never shells out.  
**Why it exists:** ANIMUS Settings, Skills, and Cron tabs depend on the same layout as the gateway.  
**Risk if removed:** ANIMUS cron log tail and skills install/update/remove will fail or drift from the gateway.  
**Test to verify:** `hermes skills list` and `hermes cron list` succeed on the host; ANIMUS Skills tab loads; create a cron job and confirm a file appears under `~/.hermes/cron/output/<job_id>/` after a run.

### Skill enable / disable (Phase 2 — Option C) + capabilities (Phase 3)

`GET /api/skills/capabilities` still probes `hermes skills --help` for install/update verbs; **`enable_disable_supported`** is **true** in ANIMUS because toggles use **`hermes_cli.skills_config`** (same persistence as Hermes dashboard **`PUT /api/skills/toggle`**) or the dashboard HTTP path when **`HERMES_DASHBOARD_SESSION_TOKEN`** is set.

- `POST /api/skills/enable/{id}` / **`disable`** return **`{ "ok": true }`** on success; **`{ "ok": false, "error": … }`** with HTTP 400 when Hermes config cannot be updated.

## Patch 4 — ANIMUS monorepo alignment (chat data dir)

**File(s):** `animus-chat/hermes_runner.py` (`chat_data_dir`), `animus-chat/server.py` (`DATA_DIR`), `animus-chat/setup_wizard/wizard_routes.py`  
**Type:** configuration change  
**What it does:** Wizard `config.json` and model cache paths use the same directory resolution as Hermes Chat conversations (`CHAT_DATA_DIR` / `HERMES_CHAT_DATA_DIR` / `~/.hermes/chat` default).  
**Why it exists:** Phase 2 stored wizard state under `./data` while chats lived under `~/.hermes/chat`, so `first_run` and wake-lock prefs could diverge.  
**Risk if removed:** Wizard may not reappear on first launch, or wake lock may not persist next to real chat data.  
**Test to verify:** With a clean `config.json` under the resolved chat data dir, open ANIMUS on port 3001 and confirm the wizard shows once; after completion, confirm `wake_lock` is present in the same `config.json`.

## Patch 5 — Known gaps (cron logs from ANIMUS host)

**File(s):** `animus-chat/cron_routes.py`  
**Type:** configuration change / documentation  
**What it does:** `GET /api/cron/logs/{id}` tries `hermes cron logs <id>`, then reads markdown under `cron/jobs.OUTPUT_DIR`. If neither yields content, the API returns `{ "lines": [], "error": "…" }` (no fake placeholder lines).  
**Why it exists:** Some builds or hosts do not expose log tail to the chat process; a clear error is preferable to fabricated log lines.  
**Risk if removed:** Users may see misleading placeholder “log” content.  
**Test to verify:** Open Cron → Logs on a job that has run; expect either real lines or the documented error string — never a fake success message.

## Patch 6 — `hermes project` CLI (workspace + repo maps)

**File(s):** `hermes-agent/hermes_cli/main.py` (argparse + `cmd_project`), `hermes-agent/hermes_cli/project_workspace_cmd.py` (handlers; unchanged)  
**Type:** CLI surface  
**What it does:** Registers **`hermes project`** with subcommands **`init`**, **`history-append`**, **`repo-map-refresh`**, **`repo-maps-refresh-all`**, **`show`**, **`write`** — same behaviour as `project_workspace_cmd.project_command` (continuity markdown under a repo root; bulk repo-map refresh across Hermes Chat project dirs).  
**Why it exists:** Gateway and cron already import `agent.project_workspace` / `cron.hermes_chat_delivery`; operators had no CLI entrypoint until `main.py` wired the existing handler module.  
**Risk if removed:** Scripts and docs referencing `hermes project …` fail with “invalid choice”.  
**Test to verify:** `hermes project --help` lists actions; `hermes project init /path/to/repo` creates workspace files when that tree is writable.

## Patch 7 — Codex device OAuth module (ANIMUS + dashboard)

**File(s):** `hermes-agent/hermes_cli/codex_device_oauth.py` (new), `hermes-agent/hermes_cli/web_server.py` (delegate start/poll/cancel + GC), `animus-chat/setup_wizard/wizard_routes.py` (Codex start/poll uses module instead of `hermes auth` subprocess), `animus-chat/app/index.html` (open `verification_url`, poll interval from API)  
**Type:** refactor / shared implementation  
**What it does:** Extracts OpenAI Codex **device OAuth** (credential pool persist) into **`hermes_cli.codex_device_oauth`** so ANIMUS chat (no FastAPI in venv) calls the **same** code path as **`hermes dashboard`** instead of spawning **`hermes auth add openai-codex`** or duplicating httpx logic in ANIMUS only.  
**Why it exists:** Hermes already implements the flow in the dashboard server; ANIMUS should reuse it, not fork.  
**Risk if removed:** ANIMUS Codex sign-in regresses to subprocess/terminal-only or duplicate divergent OAuth code.  
**Test to verify:** `PYTHONPATH=hermes-agent` from `animus-chat`: `import server`; Settings **Sign in** for Codex returns `verification_url` + `user_code` and polling reaches success after browser approval.

## Patch 8 — Gateway `/api/jobs` create+PATCH accept `schedule_tz`

**File(s):** `hermes-agent/gateway/platforms/api_server.py`  
**Type:** API parity with `cron.jobs.create_job` / `update_job`  
**What it does:** **`POST /api/jobs`** passes **`schedule_tz`** into **`create_job`**; **`PATCH /api/jobs/{id}`** allows updating **`schedule_tz`** (whitelisted field).  
**Why it exists:** ANIMUS Cron UI sends **`schedule_tz`**; the gateway HTTP path previously dropped it so wall-time jobs differed from in-process **`cron_routes`**.  
**Risk if removed:** Cron jobs created/edited only through the gateway lose timezone metadata.  
**Test to verify:** `POST /api/jobs` with **`schedule_tz`** set; **`GET /api/jobs/{id}`** returns the field; ANIMUS **Save** on an edited job preserves timezone.

## Patch 9 — Gateway `/api/jobs` create+PATCH accept `workdir`; larger cron `prompt` cap

**File(s):** `hermes-agent/gateway/platforms/api_server.py`  
**Type:** API parity with `cron.jobs.create_job` / `update_job`  
**What it does:** **`POST /api/jobs`** passes **`workdir`** into **`create_job`**; **`PATCH`** whitelists **`workdir`**; raises **`_MAX_PROMPT_LENGTH`** to **100000** so ANIMUS can store overseer + invariant + task in one job prompt.  
**Why it exists:** ANIMUS Cron binds jobs to a project repo path and prepends overseer / documentation-update instructions.  
**Risk if removed:** Jobs fall back to in-process create without `workdir` when the gateway is up, or prompt save fails with “too long”.  
**Test to verify:** Create a job with **`workdir`** set to an absolute existing directory; **`GET /api/jobs`** includes **`workdir`**; long composed prompt saves.

## Patch 10 — `transcribe_audio_force_local_faster_whisper` (ANIMUS chat STT)

**File(s):** `hermes-agent/tools/transcription_tools.py`  
**Type:** small API addition (downstream: `animus-chat/server.py` embedded STT)  
**What it does:** Adds **`transcribe_audio_force_local_faster_whisper(file_path, model=None)`**, which runs **`_transcribe_local`** / faster-whisper only and **ignores** `stt.provider` in Hermes `config.yaml`, so ANIMUS **`POST /api/stt/transcribe`** can stay on-device when **`HERMES_CHAT_STT_LOCAL_EMBEDDED=1`** even if messaging STT defaults to a cloud provider. The force path passes a tunable **`beam_size`** (env **`HERMES_CHAT_STT_BEAM_SIZE`**, default **1**) for lower chat latency vs Hermes messaging STT (**`beam_size` 5**).  
**Why it exists:** Conversation mode and the chat mic must not silently use cloud Whisper when the product expects local STT.  
**Risk if removed:** ANIMUS would need to duplicate faster-whisper wiring or call private `_transcribe_local`.  
**Test to verify:** With embedded flag on, `curl` multipart to **`/api/stt/transcribe`** returns JSON **`text`** without **`OPENAI_API_KEY`**.

## Patch 11 — `cursor-agent` in `HERMES_OVERLAYS` (gateway provider resolution)

**File(s):** `hermes-agent/hermes_cli/providers.py`  
**Type:** bugfix — provider registry parity with `run_agent` / `cursor_agent_client`  
**What it does:** Registers **`cursor-agent`** in **`HERMES_OVERLAYS`** (transport **`openai_chat`**, **`external_process`**, base **`cursor-agent://hermes`**, env hint **`CURSOR_API_KEY`**) plus **`ALIASES`** (`cursor`, `cursor-cli` → **`cursor-agent`**) and **`_LABEL_OVERRIDES`**.  
**Why it exists:** Cursor subprocess support lived in **`agent/`** and **`auth.py`**, but **`resolve_provider_full("cursor-agent", …)`** returned **None** because **`get_provider`** had no overlay / models.dev row — gateway **`/v1/chat/completions`** with **`hermes_provider: cursor-agent`** failed with **Unknown provider** (non-stream) or empty streamed deltas (ANIMUS **“No reply text…”**).  
**Risk if removed:** ANIMUS Settings → Cursor as active backend breaks again even when **`cursor-agent`** is installed and authenticated.  
**Test to verify:** `cd hermes-agent && ./scripts/run_tests.sh tests/hermes_cli/test_provider_registry_external_shims.py -q` (asserts every **`auth_type=external_process`** row in **`PROVIDER_REGISTRY`** has **`HERMES_OVERLAYS`** + **`resolve_provider_full`**); restart **`hermes-gateway`** and send a chat with Cursor active (still requires working Cursor CLI / **`CURSOR_API_KEY`**).

## Maintenance

Before merging new upstream Hermes Agent commits into ANIMUS:

1. Re-run the diff commands in Patch 1.
2. Append a new `## Patch N` section for every behavioural change.
3. Re-run ANIMUS acceptance checks (installer, Docker, wizard, chat proxy).
