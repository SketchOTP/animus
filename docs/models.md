# Models in ANIMUS

## Hermes gateway

Chat traffic goes to the OpenAI-compatible gateway at `HERMES_API_URL` (default `http://127.0.0.1:8642`) with `HERMES_API_KEY`.

## Cached catalogue

`POST /api/models/refresh` pulls `/v1/models` from the gateway and stores JSON in `data/hermes_models_cache.json` under `DATA_DIR`.

`GET /api/models?source=local` returns that cache (for the onboarding wizard and future Settings work).

## Provider catalog (`/api/chat-models`)

The existing endpoint asks Hermes CLI code (via `HERMES_AGENT_DIR`) for per-provider model IDs used by the chat UI.

## “Auto” models

When the UI selects provider-specific **Auto** routing, the server may run a small router model to pick a concrete model ID before forwarding to the gateway.

## Cursor CLI

If Cursor is installed and authenticated (`cursor whoami`), the bundled Hermes Agent may expose Cursor-backed models through the same gateway flow. Use **Settings →** gateway logs if a Cursor model fails.
