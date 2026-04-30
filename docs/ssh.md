# SSH hosts and remote projects (ANIMUS)

## SSH key authentication (recommended)

1. On the machine where ANIMUS runs, generate a key if needed: `ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519`.
2. Install the **public** key on the remote host (`~/.ssh/authorized_keys` on the remote user account).
3. In **Settings → Connections → SSH Hosts**, add a host with **SSH key** selected and the private key path on the ANIMUS server (e.g. `~/.ssh/id_ed25519`). The private key is never uploaded through the UI as a file blob; only the path is stored in `ssh_hosts.json` under the chat data directory.

## Password authentication

Password auth is supported for cases where keys are not possible. Passwords are written to repo-root **`animus.env`** as `SSH_PASSWORD_<ALIAS_IN_UPPERCASE_WITH_NON_ALNUM_AS_UNDERSCORE>` and are **plain text** on disk. Only use on trusted hosts; prefer keys.

## Remote project paths and local mount convention

When you mark a project as **on another machine** and pick a saved SSH host plus a **remote project path**, ANIMUS stores the local project folder as:

`<projects_sync_root>/_ssh_mounts/<alias><remote_absolute_path>`

(normalised slashes). You still need to **`sshfs`** (or similar) that remote path onto this local path on the ANIMUS host if you want the folder to exist for tools and validation — ANIMUS does not mount it automatically.

## Adding hosts

Use **Settings → Connections → SSH Hosts → + Add SSH host**. **Test connection** calls `POST /api/ssh/test` from the ANIMUS server (same probes as the modal’s inline test).

## Troubleshooting

| Symptom | Likely cause |
|--------|----------------|
| `sshpass not installed (required for password auth)` | Install **`sshpass`** on the machine that runs ANIMUS. Buyer **`./installer/install.sh`** prompts for it on Linux/macOS when missing; Debian/Ubuntu: `sudo apt install -y sshpass`; Fedora: `sudo dnf install -y sshpass`; macOS: `brew install sshpass`. Set **`SKIP_ANIMUS_SSHPASS=1`** to skip the installer prompt. |
| `Permission denied (publickey,password)` with password auth | On the **remote**, ensure **`PasswordAuthentication yes`** in **`sshd_config`** (and **`KbdInteractiveAuthentication`** if you rely on challenge-response). ANIMUS must run **`ssh`** with **`BatchMode=no`** for password login — older builds used **`BatchMode=yes`**, which disables password auth even when **`sshpass`** is installed. |
| Connection refused | Remote `sshd` down, firewall, or wrong port. |
| Permission denied (publickey) | Key not in `authorized_keys`, wrong `IdentityFile`, or `IdentitiesOnly` mismatch. |
| Host key verification failed | First connect needs host key acceptance; avoid disabling `StrictHostKeyChecking` unless you understand the risk. |

## API

- `GET /api/ssh/hosts` — list configured hosts (no passwords).
- `POST /api/ssh/hosts` — create host (optional `password` in body for password auth).
- `PUT /api/ssh/hosts/{alias}` — update host.
- `DELETE /api/ssh/hosts/{alias}` — remove host and clear env password entry when present.
- `POST /api/ssh/test` — `{ "alias": "…" }` for a saved host, or full inline `{ "user", "hostname", "port", "auth_method", "key_path", … }` before save.
