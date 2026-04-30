# Text-to-speech (read aloud) — Piper on the ANIMUS host

ANIMUS can read assistant replies aloud using either the **browser** (Web Speech API) or **Piper**, a local neural TTS engine on the server.

## Piper requirements

1. **Binary:** The `piper` executable must be on the server `PATH`, or set **`PIPER_BIN`** in `animus.env` to the full path of the binary.
2. **Voice models:** Piper needs **`.onnx`** files plus matching **`.onnx.json`** configs. ANIMUS scans these directories (first match wins per voice id — stem of the `.onnx` is the voice id):

   - `$PIPER_VOICES_DIR` if set (absolute or `~` path)
   - `~/.local/share/piper/`
   - `~/.piper/voices/`
   - `~/.cache/piper/`
   - `~/piper-voices/` (recursive; any nested `.onnx` is listed)

   **Automatic default voices:** When the **`piper`** binary is present but no `.onnx` models are found, the ANIMUS server **downloads** six default models (~380 MB): `en_GB-alan-medium` (default UI voice), `en_US-lessac-medium`, `en_US-amy-medium`, `en_US-ryan-medium`, `en_US-norman-medium`, `de_DE-thorsten-medium` from [rhasspy/piper-voices](https://huggingface.co/rhasspy/piper-voices) into **`~/.local/share/piper/`** (or **`PIPER_VOICES_DIR`**) in the **background** at startup and on **`GET /api/tts/piper/voices`**. The Settings UI polls until they appear. Disable: **`SKIP_ANIMUS_PIPER_VOICES=1`**. Optional pre-seed: **`./installer/install.sh`** still runs **`installer/fetch-piper-voices.sh`** when **`curl`** is installed.

3. **Restart:** After adding voices manually, use **Settings → Read aloud → Refresh voice list** or restart the ANIMUS chat service so the UI rescans.

## Where to get voices

Official voice bundles are published as **[rhasspy/piper-voices](https://huggingface.co/rhasspy/piper-voices)** on Hugging Face. Download the `.onnx` + `.json` pair for your language (e.g. `en_US-lessac-medium.onnx`).

Place the files under one of the directories above. The **voice id** shown in ANIMUS is the **stem** of the `.onnx` file (e.g. `en_US-lessac-medium`).

## API (for debugging)

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/tts/backends` | `{ "backends": ["browser", "piper"] }` — `piper` only if binary found |
| GET | `/api/tts/piper/voices` | `{ "voices": […], "fetching": bool, "fetch_error": str|null }` — starts background download when Piper is installed and the list is empty |
| POST | `/api/tts/piper/speak` | JSON `{ "text": "…", "voice": "en_GB-alan-medium" }` → `audio/wav` body |

## Client behaviour

- **Settings → Read aloud:** Choose **Browser** or **Piper**. Piper is only offered when the server reports it in `/api/tts/backends`.
- **Chat speaker button:** Uses Piper when that backend is selected; if the Piper request fails, ANIMUS falls back to browser TTS when available.

## Speech-to-text (mic upload and Conversation mode)

The chat **microphone** (tap to record, tap to stop) uploads audio to **`POST /api/stt/transcribe`** on the ANIMUS server. **Settings → Read aloud → Conversation mode** uses the same path: it records with VAD, then transcribes on the server. It does **not** use the browser Web Speech API, so the host must expose a configured STT backend.

**Settings → Read aloud → Conversation mode → STT source:** choose **Local** (embedded faster-whisper, no restart) or **Online** (OpenAI-compatible Whisper API). This persists in **`DATA_DIR/config.json`** via **`POST /api/animus/client-config`**: **`animus_chat_stt_source`** is **`embedded`** or **`openai`**; online mode can store **`animus_chat_stt_openai_key`**, **`animus_chat_stt_openai_base`**, **`animus_chat_stt_openai_model`** (UI never syncs the raw key through **`ui_settings`**). **Local** in Settings is equivalent to wanting embedded STT without editing **`animus.env`** (server treats **`embedded`** like **`HERMES_CHAT_STT_LOCAL_EMBEDDED=1`** for mic transcription when no higher-precedence local URL is set).

Configure in **`animus.env`** (repo root or next to the chat server), then restart the chat service.

**On-device (recommended):** set **`HERMES_CHAT_STT_LOCAL_EMBEDDED=1`**. ANIMUS runs **[faster-whisper](https://github.com/SYSTRAN/faster-whisper)** in the chat process (same stack as Hermes local STT). Install deps with **`pip install -r animus-chat/requirements.txt`** (includes **`python-multipart`** for multipart STT uploads and **`faster-whisper`** for embedded local STT). First transcription downloads the model (size depends on **`HERMES_CHAT_STT_LOCAL_MODEL`**, default **`small`**). Install **`ffmpeg`** on the server for reliable **webm/mp4** decoding from the browser.

| Variable | Purpose |
|----------|---------|
| **`HERMES_CHAT_STT_LOCAL_EMBEDDED`** | Set to **`1`** / **`true`** / **`yes`** / **`on`** to use embedded faster-whisper. Takes effect after **`HERMES_CHAT_STT_LOCAL_URL`** (if set) and **before** any OpenAI Whisper key. |
| **`HERMES_CHAT_STT_LOCAL_MODEL`** | Whisper size: **`tiny`**, **`base`**, **`small`**, **`medium`**, **`large-v3`**. Default **`small`** (balance of speed and accuracy on CPU). |
| **`HERMES_CHAT_STT_BEAM_SIZE`** | **ANIMUS** embedded mic path only: faster-whisper **`beam_size`** (integer **1–5**, default **1** for lower latency; messaging/local STT elsewhere still defaults to **5**). |
| **`HERMES_CHAT_STT_LOCAL_URL`** | Full URL of a separate local HTTP service that accepts multipart `file` / `audio` and returns JSON `text` / `transcript` or plain text. Highest precedence. |
| **`HERMES_CHAT_STT_OPENAI_KEY`** | API key for OpenAI Whisper (`/v1/audio/transcriptions`) when embedded + URL are unset. |
| **`OPENAI_API_KEY`** | Used for Whisper only when the dedicated STT key is unset **and** embedded local is **off**. |
| **`HERMES_CHAT_STT_OPENAI_BASE`** | Optional; default `https://api.openai.com/v1` (or **`OPENAI_BASE_URL`**). |
| **`HERMES_CHAT_STT_MODEL`** | Optional for cloud path; default `whisper-1`. |

Verify: **`curl -sS 'http://127.0.0.1:3001/api/hermes-chat-meta' | jq .stt_backend`** — expect **`local`** (embedded or HTTP) or **`openai`**, not **`none`**.

## Troubleshooting

| Symptom | Check |
|---------|--------|
| Conversation mode / mic: `stt_not_configured` | Use **Settings → Local** STT (embedded) or **Online** with an API key, or set **`HERMES_CHAT_STT_LOCAL_EMBEDDED=1`** (and ensure **`faster-whisper`** is installed), or **`HERMES_CHAT_STT_LOCAL_URL`**, or cloud keys in **`animus.env`**; restart may be needed for env-only changes; confirm **`stt_backend`** in **`/api/hermes-chat-meta`** |
| `embedded_stt_failed` / empty transcript | Install **`ffmpeg`**; check logs; try **`HERMES_CHAT_STT_LOCAL_MODEL=base`** if CPU is slow or **`medium`** for higher accuracy |
| Piper not in backend list | `which piper` on host; set `PIPER_BIN` if installed outside PATH |
| Empty voice list (stays empty) | Server needs outbound HTTPS to Hugging Face; ~400 MB disk under `~/.local/share/piper`; check logs. **`SKIP_ANIMUS_PIPER_VOICES`** must not be set. Optional: **`bash installer/fetch-piper-voices.sh`** to pre-download |
| Playback fails | Server logs; confirm `piper -m /path/to/model.onnx` works manually with a short string on stdin |
