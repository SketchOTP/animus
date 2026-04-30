# Tailscale and ANIMUS

## Recommended pattern

1. Run ANIMUS on loopback only: set `CHAT_HOST=127.0.0.1` and `CHAT_PORT=3001` in `animus.env` (the stock example defaults to `CHAT_HOST=::` for browser `localhost` compatibility; Tailscale Serve to this port is tighter with `127.0.0.1`).
2. On the machine, use **Tailscale Serve** to publish HTTPS to your tailnet, proxying to the local HTTP port.

Example (adjust hostname and port):

```bash
tailscale serve --bg http://127.0.0.1:3001
```

3. Set `HERMES_CHAT_PUBLIC_URL` in `animus.env` to the HTTPS URL users open (so `/api/hermes-chat-meta` hints stay correct).

## TLS on uvicorn

You can terminate TLS in ANIMUS using `CHAT_SSL_CERTFILE` / `CHAT_SSL_KEYFILE`, but browsers on Tailscale often rely on Tailscale’s own certificates for `*.ts.net` names. Prefer Serve unless you have a specific reason to terminate TLS in Python.

## mkcert

If you terminate TLS locally with mkcert, regenerate certificates whenever the DNS name changes, and include every hostname you use in the SAN list.
