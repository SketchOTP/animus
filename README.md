# ANIMUS

ANIMUS is a distributable bundle: the **animus-chat** web app (Starlette + PWA) and a full **hermes-agent** checkout, so local customisations (gateway, skills, cron, Cursor-related tooling) stay aligned.

## Download / Gumroad buyers

If you unpacked a **release zip**, open **`START_HERE.txt`** in the root of the folder first, then **`INSTALL.md`** for the full guide. Sellers: see **`docs/GUMROAD.md`** for packaging checklist and suggested listing copy.

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

Single source of truth: root **`VERSION`** (semver, no `v` prefix). The running app exposes it at **`GET /api/version`** — keep it aligned with your Gumroad file name (`animus-vX.Y.Z.zip`).
