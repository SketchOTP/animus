#!/usr/bin/env bash
# Download default Piper voice models (6× ~63MB ≈ 380MB) so Read aloud → Piper has choices
# after install. Idempotent: skips files that already exist.
#
# Override install dir: PIPER_VOICES_DIR=/path/to/dir ./installer/fetch-piper-voices.sh
# Skip in CI: SKIP_ANIMUS_PIPER_VOICES=1

set -u

if [[ "${SKIP_ANIMUS_PIPER_VOICES:-}" == "1" ]]; then
  echo "[piper-voices] SKIP_ANIMUS_PIPER_VOICES=1 — skipping."
  exit 0
fi

if ! command -v curl >/dev/null 2>&1; then
  echo "[piper-voices] curl not found — cannot download voices." >&2
  exit 1
fi

DEST="${PIPER_VOICES_DIR:-${HOME}/.local/share/piper}"
DEST="$(mkdir -p "${DEST}" && cd "${DEST}" && pwd)"
HF_BASE="${PIPER_VOICE_HF_BASE:-https://huggingface.co/rhasspy/piper-voices/resolve/main}"

dl() {
  local rel="$1"
  local out="$2"
  local tmp="${out}.partial.$$"
  if [[ -f "${out}" ]]; then
    return 0
  fi
  echo "[piper-voices] GET ${rel}"
  if ! curl -fL --retry 3 --connect-timeout 30 --max-time 900 \
    "${HF_BASE}/${rel}" -o "${tmp}"; then
    rm -f "${tmp}"
    return 1
  fi
  mv -f "${tmp}" "${out}"
}

pair() {
  local reldir="$1"
  local stem="$2"
  local onnx="${DEST}/${stem}.onnx"
  local jsn="${DEST}/${stem}.onnx.json"
  local ok=1
  if [[ -f "${onnx}" && -f "${jsn}" ]]; then
    echo "[piper-voices] ${stem} already complete — skipping."
    return 0
  fi
  dl "${reldir}/${stem}.onnx" "${onnx}" || ok=0
  dl "${reldir}/${stem}.onnx.json" "${jsn}" || ok=0
  if [[ "${ok}" -eq 0 ]]; then
    echo "[piper-voices] Failed to fetch ${stem} (network or HF rate limit)." >&2
    rm -f "${onnx}" "${jsn}"
    return 1
  fi
  echo "[piper-voices] Installed ${stem} under ${DEST}"
}

echo "[piper-voices] Voice directory: ${DEST}"
mkdir -p "${DEST}"

failed=0
pair "en/en_GB/alan/medium" "en_GB-alan-medium" || failed=1
pair "en/en_US/lessac/medium" "en_US-lessac-medium" || failed=1
pair "en/en_US/amy/medium" "en_US-amy-medium" || failed=1
pair "en/en_US/ryan/medium" "en_US-ryan-medium" || failed=1
pair "en/en_US/norman/medium" "en_US-norman-medium" || failed=1
pair "de/de_DE/thorsten/medium" "de_DE-thorsten-medium" || failed=1

if [[ "${failed}" -ne 0 ]]; then
  echo "[piper-voices] One or more downloads failed. Re-run: ${0}" >&2
  exit 1
fi
echo "[piper-voices] Done. Install the \`piper\` binary on PATH (or set PIPER_BIN) — see docs/tts.md"
