# ANIMUS

ANIMUS is a distributable bundle: the **animus-chat** web app (Starlette + PWA) and a full **hermes-agent** checkout, so local customisations (gateway, skills, cron, Cursor-related tooling) stay aligned.

## Quick start

```bash
chmod +x installer/install.sh installer/preflight.sh build-release.sh animus-chat/restart.sh
./installer/install.sh
```

Open **http://localhost:3001** (default). Copy `animus.env.example` to `animus.env` at the repo root and set `HERMES_API_URL` / `HERMES_API_KEY`, or use the onboarding wizard APIs under `/api/setup/*`.

## Docker

```bash
cd docker
cp .env.example .env   # edit keys / gateway URL
docker compose up --build
```

## Docs

- `INSTALL.md` — manual install, systemd, troubleshooting
- `docs/tailscale.md` — remote access
- `docs/models.md` — model cache and providers
- `docs/hermes-agent-patches.md` — how this Hermes Agent tree differs from upstream

## Version

The root `VERSION` file is exposed at `GET /api/version`.
