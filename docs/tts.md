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

## Troubleshooting

| Symptom | Check |
|---------|--------|
| Piper not in backend list | `which piper` on host; set `PIPER_BIN` if installed outside PATH |
| Empty voice list (stays empty) | Server needs outbound HTTPS to Hugging Face; ~400 MB disk under `~/.local/share/piper`; check logs. **`SKIP_ANIMUS_PIPER_VOICES`** must not be set. Optional: **`bash installer/fetch-piper-voices.sh`** to pre-download |
| Playback fails | Server logs; confirm `piper -m /path/to/model.onnx` works manually with a short string on stdin |
