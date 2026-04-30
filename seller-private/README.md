# Seller-only local files (not shipped, not committed)

This directory is for **machine-local secrets** you use when publishing updates (for example Vercel **`ADMIN_TOKEN`**), notes, or copies of env files.

- **Git:** Everything here except this **`README.md`** is ignored (see repo root **`.gitignore`**). Do not force-add tokens.
- **Buyer zip:** **`./build-release.sh`** excludes **`seller-private/`** entirely so Gumroad / manifest installs never receive these files.
- **Security:** This is normal filesystem storage — use disk encryption, a locked account, and **`chmod 700 seller-private`** if others can access the machine. Prefer a password manager for long-term storage; use a one-line file here only for convenience when running publish scripts.

## Suggested layout (create yourself; names are optional)

| File | Purpose |
|------|---------|
| `ADMIN_TOKEN` | Single line: Vercel Production **`ADMIN_TOKEN`** for **`animus-site`**. |
| `BLOB_READ_WRITE_TOKEN` | Optional; only if you script Blob uploads locally (rare). |

Then from repo root:

```bash
export ADMIN_TOKEN="$(tr -d '[:space:]' < seller-private/ADMIN_TOKEN)"
./scripts/publish-animus-manifest.sh
```

Never paste real tokens into chat, tickets, or commits.
