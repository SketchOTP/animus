# Proof: ANIMUS digest no longer duplicated in `sessions.system_prompt` (token inflation fix)

This document records **live gateway** verification after deploying `strip_animus_transient_chat_digest_for_session_persist` (see `hermes-agent/animus_chat_digest_persist.py` and first-turn persist path in `hermes-agent/run_agent.py`).

## Preconditions

- Gateway process was running from **`/home/sketch/animus/hermes-agent`** (`python -m hermes_cli.main gateway run --replace`).
- SQLite DB resolved from **`GET http://127.0.0.1:8642/health/detailed`** → `hermes_home_resolved` =  
  **`/home/sketch/hermes/companion/hermes-home`** → **`state.db`** =  
  **`/home/sketch/hermes/companion/hermes-home/state.db`**.

## 1) Gateway restart (load new code)

Command:

```bash
cd /home/sketch/animus/hermes-agent && ./venv/bin/python -m hermes_cli.main gateway restart
```

Notes:

- `systemctl --user status hermes-gateway.service` may show **inactive** briefly while a new `gateway run` process binds **8642**; health was re-checked until **`/health` returned 200**.

## 2) Fresh session id

**`session_id` used:** `96e5bf80-7037-4e64-9c44-4d1b1dd343ed`

(Generated UUID; passed on every request as **`X-Hermes-Session-Id`**.)

## 3) Synthetic “ANIMUS-like” ephemeral (digest + project block)

Each `POST /v1/chat/completions` body included a **single `system` message** shaped like ANIMUS `buildMessages` output after auto-summarize:

- Starts with **`[In-chat session digest (proof run).]`**
- Contains a distinctive synthetic body: **`SYNTHETIC_DIGEST_PARAGRAPH_AAAAA_BBBBB_CCCCC_DDDDD_EEEEE`**
- Then a **`Project "DigestProof" · workspace: /tmp/...`** block (so the strip logic can cut at `\n\nProject "`).

This mimics “digest exists, then user sends a short line” while forcing a **first-turn persist** that historically would have **frozen the digest** into SQLite.

## 4) HTTP calls (three turns)

Endpoint: **`POST http://127.0.0.1:8642/v1/chat/completions`**  
Auth: **`Authorization: Bearer <HERMES_API_KEY>`** from **`/home/sketch/animus/animus.env`** (not reproduced here).

All requests:

- **`X-Hermes-Session-Id: 96e5bf80-7037-4e64-9c44-4d1b1dd343ed`**
- **`"model": "auto"`**, **`"stream": false`**

Turns:

1. User: **`Reply with exactly one word: pong.`** (establishes session + first persist)
2. User: **`test`** (same synthetic system blob resent — like ANIMUS prepending digest each turn)
3. User: **`test again`**

Full JSON capture (usage + SQLite checks): **`/tmp/animus_digest_proof.json`** on the machine that ran the proof.

### Provider `usage` (no +~6k “digest duplication” steps)

| Turn | `prompt_tokens` | `completion_tokens` | `total_tokens` |
|------|-----------------|---------------------|----------------|
| 1 (`pong`) | 5502 | 1 | 5503 |
| 2 (`test`) | 5547 | 5 | 5552 |
| 3 (`test again`) | 5572 | 3 | 5575 |

**Interpretation:** prompt size grows only modestly turn-to-turn (**+45**, then **+25**) as **conversation history** in SQLite expands — not by re-injecting an entire extra digest copy from `sessions.system_prompt` on every turn.

## 5) SQLite inspection for that `session_id`

`sqlite3` CLI was **not installed** on this host; equivalent query via Python **`sqlite3` stdlib**:

```python
import sqlite3
con = sqlite3.connect("/home/sketch/hermes/companion/hermes-home/state.db")
cur = con.cursor()
cur.execute(
    "SELECT length(system_prompt), instr(system_prompt, ?), instr(system_prompt, ?) "
    "FROM sessions WHERE id = ?",
    ("[In-chat session digest", "[Prior conversation summarized", "96e5bf80-7037-4e64-9c44-4d1b1dd343ed"),
)
print(cur.fetchone())
cur.execute(
    "SELECT instr(system_prompt, ?) FROM sessions WHERE id = ?",
    ("SYNTHETIC_DIGEST_PARAGRAPH_AAAAA_BBBBB_CCCCC_DDDDD_EEEEE", "96e5bf80-7037-4e64-9c44-4d1b1dd343ed"),
)
print("synthetic_digest_marker:", cur.fetchone()[0])
```

**Result row (`length`, `instr('[In-chat…')`, `instr('[Prior…')`):**

```text
(21551, 0, 0)
```

**`instr(..., 'SYNTHETIC_DIGEST...')`:** `0`

### Expected vs observed

| Check | Expected | Observed |
|-------|----------|----------|
| Hermes core / stable system present | yes (non-trivial length) | `system_prompt_len == 21551` |
| **No** `[In-chat session digest` in persisted `system_prompt` | `instr == 0` | **0** |
| **No** `[Prior conversation summarized` | `instr == 0` | **0** |
| **No** synthetic digest body persisted | marker `instr == 0` | **0** |

The **`substr(system_prompt, 1, 900)`** prefix begins with the companion kernel identity header (Hermes core / product system), **not** the ANIMUS digest markers.

## 6) Unit tests (supplementary; not sufficient alone)

Command:

```bash
cd /home/sketch/animus/hermes-agent
python -m pytest tests/run_agent/test_animus_digest_persist_strip.py -q -o addopts=
```

Output (this run):

```text
....                                                                     [100%]
4 passed in 0.12s
```

## 7) Operator follow-ups

- **Restart gateway** after upgrading `hermes-agent` on any host: `hermes gateway restart` (or your unit).
- **Existing sessions** created before the fix may still carry a bloated `sessions.system_prompt`; use a **new chat / new `session_id`** for a clean baseline.

---

## Bottom line

**Root cause (historical):** first-turn `update_system_prompt` merged the full client ephemeral **including** the ANIMUS digest into `sessions.system_prompt`; later turns **reloaded** that blob and **re-appended** ephemeral digest again → duplicated digest + large per-turn prompt jumps.

**Fix:** strip digest markers from ephemeral **before** the first SQLite persist merge.

**Live proof:** new session **`96e5bf80-7037-4e64-9c44-4d1b1dd343ed`** — SQLite shows **no** digest markers and **no** synthetic digest body in `sessions.system_prompt`, while short follow-ups do **not** exhibit repeated multi-thousand prompt-token jumps.
