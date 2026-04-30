# ANIMUS Phase 3 — Pre-release smoke checklist

Run on a host with **Docker** (optional for steps 15–16), **Hermes gateway + API key**, and **`hermes` on PATH**. Use a **clean** chat data directory to test the wizard (see `project_goal.md` Phase 3 Task 7).

## Setup (clean wizard)

Chat state lives in **`chat_data_dir()`** (see `hermes_runner.chat_data_dir`): **`CHAT_DATA_DIR` / `HERMES_CHAT_DATA_DIR` env**, value from **`~/.hermes/.env`**, else **`~/.hermes/chat`**. There is often **no `./data` folder** in the repo — `mv data/` will fail if you never used `./data`.

**Option A — isolated smoke dir (recommended):**

```bash
cd animus-chat
export CHAT_DATA_DIR="/tmp/animus-smoke-$(date +%s)"
mkdir -p "$CHAT_DATA_DIR"
# same shell: start server so it picks up CHAT_DATA_DIR
```

**Option B — reset real default chat dir:**

```bash
mv ~/.hermes/chat ~/.hermes/chat-backup-$(date +%s)
mkdir -p ~/.hermes/chat
```

Then start the server in that environment and ensure **animus.env / gateway key** is valid.

## Practical tips (before and during the run)

1. **Keys — before step 1:** Confirm **`animus.env`** and/or **`~/.hermes/.env`** has at least one **non-placeholder** provider API key. Blank or expired keys waste time on steps 3–4 and 9.
2. **Token tracker — during step 9:** Watch DevTools **Network** (chat SSE) or terminal **stdout** for a **`usage`** object in the stream; if it appears, step 13 is very likely to pass once the tracker refreshes.
3. **Screenshots:** Take Gumroad shots **while the smoke session is active** (wizard on screen, populated chat/cron). After you tear down **`CHAT_DATA_DIR`**, first-run UI is gone unless you use another temp dir or edit **`config.json`**.
4. **Step 16:** After smoke **teardown**, open a **new shell** or **`unset CHAT_DATA_DIR`**, **`cd`** to **repo root**, then **`./build-release.sh`**. Do not run the release script while still exporting the smoke temp dir unless you intend to.

## Steps 1–16

1. Open `http://localhost:3001` — **wizard** appears (not main chat only).
2. Wizard step 1 — welcome shows **ANIMUS** + logo.
3. Step 2 — **Hermes check** passes; version text visible.
4. Step 3 — enter a real API key; **Test** shows success.
5. Step 4 — **Cursor** state matches machine (installed / not / authenticated).
6. Step 5 — **models** load; pick a model.
7. Steps 6–8 — skills info, Tailscale, **Done** → **Open ANIMUS**.
8. Main UI — wizard gone; **tab tooltips** on first tab visits.
9. **Chat** — send a message; reply arrives; **provider badge** on assistant message.
10. **Settings** — model list loads; change model; send again; badge reflects selection.
11. **Cron** — daemon banner sane; create a test job; confirm `hermes cron list` on host shows it.
12. **Skills** — list loads; **Check for updates** returns (may be empty); install/update paths do not error unexpectedly.
13. **Token tracker** — entries from steps 9–10 appear (requires `stream_options.include_usage` from gateway).
14. **About** — versions from `/api/version`.
15. **Reload** — wizard does **not** reappear (`first_run: false` in `config.json`).
16. From repo root (no `CHAT_DATA_DIR` from smoke): `./build-release.sh` — **pass** (script **fails** if zip > 55MB); zip **≤ 55MB** (v1.0 cap; typical ~28MB with default trims); name `animus-v1.0.0.zip` if `VERSION` is `1.0.0`.

## Teardown

- If you used **Option A**: remove `/tmp/animus-smoke-*` when done; unset `CHAT_DATA_DIR`.
- If you used **Option B**: `mv ~/.hermes/chat-backup-* ~/.hermes/chat` (or merge as needed).

```bash
# example after Option A
unset CHAT_DATA_DIR
rm -rf /tmp/animus-smoke-*
```

Record pass/fail per step in `project_status.md` under **Phase 3 Smoke Test**.
