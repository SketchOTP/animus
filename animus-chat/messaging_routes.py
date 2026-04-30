"""Settings → Messaging: Hermes gateway platforms — read/write ``~/.hermes/.env`` + ``config.yaml``."""

from __future__ import annotations

import copy
import logging
import re
from pathlib import Path
from typing import Any

from starlette.requests import Request
from starlette.responses import JSONResponse

from hermes_service_client import gateway_http_json

log = logging.getLogger("animus.messaging")

# Field: id (API key), env (HERMES .env name), type, label, optional?, options? (for select)
# home: optional { "chat_env", "name_env" } — persisted to .env + mirrored in config.yaml home_channel


def _platform_specs() -> dict[str, dict[str, Any]]:
    """Declarative UI + env mapping aligned with ``gateway.config._apply_env_overrides``."""
    sel_reply = ["off", "first", "all"]

    def bot(token_env: str, home_prefix: str, reply_env: str | None = None) -> dict[str, Any]:
        fields: list[dict[str, Any]] = [
            {"id": "token", "env": token_env, "type": "secret", "label": "Bot token"},
        ]
        if reply_env:
            fields.append(
                {
                    "id": "reply_to_mode",
                    "env": reply_env,
                    "type": "select",
                    "label": "Reply threading",
                    "optional": True,
                    "options": sel_reply,
                }
            )
        return {
            "fields": fields,
            "home": {"chat_env": f"{home_prefix}_HOME_CHANNEL", "name_env": f"{home_prefix}_HOME_CHANNEL_NAME"},
        }

    specs: dict[str, dict[str, Any]] = {
        "local": {
            "readonly": True,
            "note": "Built-in local interface — always available; no credentials to configure.",
        },
        "telegram": bot("TELEGRAM_BOT_TOKEN", "TELEGRAM", "TELEGRAM_REPLY_TO_MODE"),
        "discord": bot("DISCORD_BOT_TOKEN", "DISCORD", "DISCORD_REPLY_TO_MODE"),
        "slack": bot("SLACK_BOT_TOKEN", "SLACK"),
        "whatsapp": {
            "fields": [
                {
                    "id": "enabled",
                    "env": "WHATSAPP_ENABLED",
                    "type": "bool",
                    "label": "Enable WhatsApp bridge",
                    "optional": True,
                }
            ],
            "note": "Requires the Hermes WhatsApp bridge installed and running; see INSTALL.md.",
        },
        "signal": {
            "fields": [
                {"id": "http_url", "env": "SIGNAL_HTTP_URL", "type": "text", "label": "signal-cli REST URL"},
                {"id": "account", "env": "SIGNAL_ACCOUNT", "type": "text", "label": "Phone number (E.164)"},
                {
                    "id": "ignore_stories",
                    "env": "SIGNAL_IGNORE_STORIES",
                    "type": "bool",
                    "label": "Ignore stories",
                    "optional": True,
                },
            ],
            "home": {"chat_env": "SIGNAL_HOME_CHANNEL", "name_env": "SIGNAL_HOME_CHANNEL_NAME"},
        },
        "mattermost": {
            "fields": [
                {"id": "url", "env": "MATTERMOST_URL", "type": "text", "label": "Server base URL"},
                {"id": "token", "env": "MATTERMOST_TOKEN", "type": "secret", "label": "Personal access token"},
            ],
            "home": {"chat_env": "MATTERMOST_HOME_CHANNEL", "name_env": "MATTERMOST_HOME_CHANNEL_NAME"},
        },
        "matrix": {
            "fields": [
                {"id": "homeserver", "env": "MATRIX_HOMESERVER", "type": "text", "label": "Homeserver URL"},
                {"id": "user_id", "env": "MATRIX_USER_ID", "type": "text", "label": "User ID", "optional": True},
                {"id": "access_token", "env": "MATRIX_ACCESS_TOKEN", "type": "secret", "label": "Access token", "optional": True},
                {"id": "password", "env": "MATRIX_PASSWORD", "type": "secret", "label": "Password (if no token)", "optional": True},
                {"id": "device_id", "env": "MATRIX_DEVICE_ID", "type": "text", "label": "Device ID", "optional": True},
                {"id": "encryption", "env": "MATRIX_ENCRYPTION", "type": "bool", "label": "E2EE", "optional": True},
            ],
            "home": {"chat_env": "MATRIX_HOME_ROOM", "name_env": "MATRIX_HOME_ROOM_NAME"},
        },
        "homeassistant": {
            "fields": [
                {"id": "url", "env": "HASS_URL", "type": "text", "label": "Home Assistant URL", "optional": True},
                {"id": "token", "env": "HASS_TOKEN", "type": "secret", "label": "Long-lived access token"},
            ],
        },
        "email": {
            "fields": [
                {"id": "address", "env": "EMAIL_ADDRESS", "type": "text", "label": "Email address"},
                {"id": "password", "env": "EMAIL_PASSWORD", "type": "secret", "label": "Password / app password"},
                {"id": "imap_host", "env": "EMAIL_IMAP_HOST", "type": "text", "label": "IMAP host"},
                {"id": "smtp_host", "env": "EMAIL_SMTP_HOST", "type": "text", "label": "SMTP host"},
            ],
            "home": {"chat_env": "EMAIL_HOME_ADDRESS", "name_env": "EMAIL_HOME_ADDRESS_NAME"},
        },
        "sms": {
            "fields": [
                {"id": "account_sid", "env": "TWILIO_ACCOUNT_SID", "type": "text", "label": "Twilio Account SID"},
                {"id": "auth_token", "env": "TWILIO_AUTH_TOKEN", "type": "secret", "label": "Twilio Auth Token"},
            ],
            "home": {"chat_env": "SMS_HOME_CHANNEL", "name_env": "SMS_HOME_CHANNEL_NAME"},
        },
        "dingtalk": {
            "fields": [
                {"id": "client_id", "env": "DINGTALK_CLIENT_ID", "type": "text", "label": "Client ID"},
                {"id": "client_secret", "env": "DINGTALK_CLIENT_SECRET", "type": "secret", "label": "Client secret"},
            ],
            "home": {"chat_env": "DINGTALK_HOME_CHANNEL", "name_env": "DINGTALK_HOME_CHANNEL_NAME"},
        },
        "api_server": {
            "fields": [
                {"id": "enabled", "env": "API_SERVER_ENABLED", "type": "bool", "label": "Enable OpenAI-compatible API", "optional": True},
                {"id": "api_key", "env": "API_SERVER_KEY", "type": "secret", "label": "API bearer key (optional)", "optional": True},
                {"id": "port", "env": "API_SERVER_PORT", "type": "text", "label": "Listen port", "optional": True},
                {"id": "host", "env": "API_SERVER_HOST", "type": "text", "label": "Bind host", "optional": True},
                {"id": "cors_origins", "env": "API_SERVER_CORS_ORIGINS", "type": "text", "label": "CORS origins (comma-separated)", "optional": True},
                {"id": "model_name", "env": "API_SERVER_MODEL_NAME", "type": "text", "label": "Advertised model name", "optional": True},
            ],
        },
        "webhook": {
            "fields": [
                {"id": "enabled", "env": "WEBHOOK_ENABLED", "type": "bool", "label": "Enable webhook server", "optional": True},
                {"id": "port", "env": "WEBHOOK_PORT", "type": "text", "label": "Listen port", "optional": True},
                {"id": "secret", "env": "WEBHOOK_SECRET", "type": "secret", "label": "Shared secret", "optional": True},
            ],
        },
        "feishu": {
            "fields": [
                {"id": "app_id", "env": "FEISHU_APP_ID", "type": "text", "label": "App ID"},
                {"id": "app_secret", "env": "FEISHU_APP_SECRET", "type": "secret", "label": "App secret"},
                {"id": "domain", "env": "FEISHU_DOMAIN", "type": "text", "label": "Domain (feishu / lark)", "optional": True},
                {"id": "connection_mode", "env": "FEISHU_CONNECTION_MODE", "type": "text", "label": "Connection mode", "optional": True},
                {"id": "encrypt_key", "env": "FEISHU_ENCRYPT_KEY", "type": "secret", "label": "Encrypt key", "optional": True},
                {"id": "verification_token", "env": "FEISHU_VERIFICATION_TOKEN", "type": "secret", "label": "Verification token", "optional": True},
            ],
            "home": {"chat_env": "FEISHU_HOME_CHANNEL", "name_env": "FEISHU_HOME_CHANNEL_NAME"},
        },
        "wecom": {
            "fields": [
                {"id": "bot_id", "env": "WECOM_BOT_ID", "type": "text", "label": "Bot ID"},
                {"id": "secret", "env": "WECOM_SECRET", "type": "secret", "label": "Secret"},
                {"id": "websocket_url", "env": "WECOM_WEBSOCKET_URL", "type": "text", "label": "WebSocket URL", "optional": True},
            ],
            "home": {"chat_env": "WECOM_HOME_CHANNEL", "name_env": "WECOM_HOME_CHANNEL_NAME"},
        },
        "wecom_callback": {
            "fields": [
                {"id": "corp_id", "env": "WECOM_CALLBACK_CORP_ID", "type": "text", "label": "Corp ID"},
                {"id": "corp_secret", "env": "WECOM_CALLBACK_CORP_SECRET", "type": "secret", "label": "Corp secret"},
                {"id": "agent_id", "env": "WECOM_CALLBACK_AGENT_ID", "type": "text", "label": "Agent ID", "optional": True},
                {"id": "token", "env": "WECOM_CALLBACK_TOKEN", "type": "secret", "label": "Callback token", "optional": True},
                {"id": "encoding_aes_key", "env": "WECOM_CALLBACK_ENCODING_AES_KEY", "type": "secret", "label": "Encoding AES key", "optional": True},
                {"id": "host", "env": "WECOM_CALLBACK_HOST", "type": "text", "label": "Listen host", "optional": True},
                {"id": "port", "env": "WECOM_CALLBACK_PORT", "type": "text", "label": "Listen port", "optional": True},
            ],
        },
        "weixin": {
            "fields": [
                {"id": "token", "env": "WEIXIN_TOKEN", "type": "secret", "label": "iLink token", "optional": True},
                {"id": "account_id", "env": "WEIXIN_ACCOUNT_ID", "type": "text", "label": "Account ID", "optional": True},
                {"id": "base_url", "env": "WEIXIN_BASE_URL", "type": "text", "label": "API base URL", "optional": True},
            ],
            "home": {"chat_env": "WEIXIN_HOME_CHANNEL", "name_env": "WEIXIN_HOME_CHANNEL_NAME"},
        },
        "bluebubbles": {
            "fields": [
                {"id": "server_url", "env": "BLUEBUBBLES_SERVER_URL", "type": "text", "label": "BlueBubbles server URL"},
                {"id": "password", "env": "BLUEBUBBLES_PASSWORD", "type": "secret", "label": "Server password"},
                {"id": "webhook_host", "env": "BLUEBUBBLES_WEBHOOK_HOST", "type": "text", "label": "Webhook host", "optional": True},
                {"id": "webhook_port", "env": "BLUEBUBBLES_WEBHOOK_PORT", "type": "text", "label": "Webhook port", "optional": True},
                {"id": "webhook_path", "env": "BLUEBUBBLES_WEBHOOK_PATH", "type": "text", "label": "Webhook path", "optional": True},
                {"id": "send_read_receipts", "env": "BLUEBUBBLES_SEND_READ_RECEIPTS", "type": "bool", "label": "Send read receipts", "optional": True},
            ],
            "home": {"chat_env": "BLUEBUBBLES_HOME_CHANNEL", "name_env": "BLUEBUBBLES_HOME_CHANNEL_NAME"},
        },
        "qqbot": {
            "fields": [
                {"id": "app_id", "env": "QQ_APP_ID", "type": "text", "label": "App ID"},
                {"id": "client_secret", "env": "QQ_CLIENT_SECRET", "type": "secret", "label": "Client secret"},
            ],
            "home": {"chat_env": "QQBOT_HOME_CHANNEL", "name_env": "QQBOT_HOME_CHANNEL_NAME"},
        },
    }
    return specs


def _all_env_keys_for_spec(spec: dict[str, Any]) -> list[str]:
    keys: list[str] = []
    for f in spec.get("fields") or []:
        ek = f.get("env")
        if ek:
            keys.append(ek)
    home = spec.get("home") or {}
    for k in ("chat_env", "name_env"):
        ek = home.get(k)
        if ek:
            keys.append(ek)
    return keys


def _mask_secret(val: str) -> dict[str, Any]:
    v = (val or "").strip()
    if not v:
        return {"has_secret": False}
    tail = v[-4:] if len(v) >= 4 else "****"
    return {"has_secret": True, "masked": f"…{tail}"}


def _env_bool_str(on: bool) -> str:
    return "true" if on else "false"


def _parse_json_bool(raw: Any) -> bool | None:
    if isinstance(raw, bool):
        return raw
    if raw is None:
        return None
    s = str(raw).strip().lower()
    if s in ("true", "1", "yes", "on"):
        return True
    if s in ("false", "0", "no", "off", ""):
        return False
    return None


async def messaging_gateway_status_api(_req: Request) -> JSONResponse:
    st, body = await gateway_http_json("GET", "/health/detailed", timeout=12.0)
    if st == 200 and isinstance(body, dict):
        return JSONResponse({"ok": True, "health": body})
    return JSONResponse(
        {"ok": False, "http": st, "error": body if isinstance(body, dict) else str(body)},
        status_code=200,
    )


def _messaging_overview_payload() -> dict[str, Any]:
    from gateway.config import Platform, load_gateway_config

    specs = _platform_specs()
    gc = load_gateway_config()
    connected = {x.value for x in gc.get_connected_platforms()}
    rows: list[dict[str, Any]] = []
    for p in Platform:
        pid = p.value
        spec = specs.get(pid) or {}
        pc = gc.platforms.get(p)
        enabled = bool(pc and pc.enabled)
        home = gc.get_home_channel(p) if pc else None
        home_id = str(getattr(home, "chat_id", "") or "").strip() if home else ""
        cron_deliver_home_ready = bool(enabled and pid in connected and home_id)
        rows.append(
            {
                "id": pid,
                "label": p.name.replace("_", " ").title(),
                "enabled": enabled,
                "connected": pid in connected,
                "readonly": bool(spec.get("readonly")),
                "has_form": bool(spec.get("fields")) and not spec.get("readonly"),
                "cron_deliver_home_ready": cron_deliver_home_ready,
            }
        )
    return {
        "ok": True,
        "platforms": rows,
        "restart_hint": "After saving, restart the Hermes gateway so it reloads ~/.hermes/.env (Settings → Restart gateway).",
    }


async def messaging_overview_api(_req: Request) -> JSONResponse:
    try:
        from hermes_cli.config import is_managed

        managed = bool(is_managed())
    except Exception:
        managed = False
    payload = _messaging_overview_payload()
    payload["managed_profile"] = managed
    if managed:
        payload["error"] = "Hermes profile is managed — gateway messaging cannot be edited from ANIMUS."
    return JSONResponse(payload)


async def messaging_platform_get_api(req: Request) -> JSONResponse:
    from gateway.config import Platform, load_gateway_config
    from hermes_cli.config import is_managed, load_env

    pid = str(req.path_params.get("platform_id") or "").strip().lower()
    try:
        Platform(pid)
    except ValueError:
        return JSONResponse({"ok": False, "error": "unknown platform"}, status_code=404)

    spec = _platform_specs().get(pid)
    if not spec:
        return JSONResponse({"ok": False, "error": "unknown platform"}, status_code=404)
    if spec.get("readonly"):
        return JSONResponse(
            {
                "ok": True,
                "platform": pid,
                "readonly": True,
                "note": spec.get("note", ""),
            }
        )

    try:
        managed = bool(is_managed())
    except Exception:
        managed = False

    env = load_env()
    gc = load_gateway_config()
    p = Platform(pid)
    pc = gc.platforms.get(p)
    fields_out: list[dict[str, Any]] = []
    for f in spec.get("fields") or []:
        fid = f["id"]
        ek = f["env"]
        typ = f.get("type", "text")
        raw = env.get(ek) or ""
        entry: dict[str, Any] = {
            "id": fid,
            "env": ek,
            "label": f.get("label", fid),
            "type": typ,
            "optional": bool(f.get("optional")),
        }
        if typ == "secret":
            entry.update(_mask_secret(raw))
        elif typ == "bool":
            entry["value"] = str(raw).strip().lower() in ("1", "true", "yes", "on")
        elif typ == "select":
            entry["value"] = (raw or "first").strip().lower() if "reply" in fid else (raw or "").strip()
            entry["options"] = f.get("options") or []
        else:
            entry["value"] = raw
        fields_out.append(entry)

    home = spec.get("home") or {}
    chat_env = home.get("chat_env")
    name_env = home.get("name_env")
    home_out: dict[str, Any] = {}
    if chat_env:
        home_out["chat_id"] = env.get(chat_env) or (pc.home_channel.chat_id if pc and pc.home_channel else "") or ""
    if name_env:
        home_out["name"] = env.get(name_env) or (pc.home_channel.name if pc and pc.home_channel else "") or ""

    return JSONResponse(
        {
            "ok": True,
            "managed_profile": managed,
            "platform": pid,
            "enabled": bool(pc and pc.enabled),
            "fields": fields_out,
            "home": home_out if home_out else None,
            "note": spec.get("note"),
        }
    )


async def messaging_platform_post_api(req: Request) -> JSONResponse:
    from gateway.config import Platform, load_gateway_config

    from hermes_cli.config import is_managed, read_raw_config, remove_env_value, save_config, save_env_value

    pid = str(req.path_params.get("platform_id") or "").strip().lower()
    try:
        plat = Platform(pid)
    except ValueError:
        return JSONResponse({"ok": False, "error": "unknown platform"}, status_code=404)

    spec = _platform_specs().get(pid)
    if not spec or spec.get("readonly"):
        return JSONResponse({"ok": False, "error": "platform not editable"}, status_code=400)

    try:
        if is_managed():
            return JSONResponse(
                {"ok": False, "error": "Hermes profile is managed — cannot save gateway messaging here."},
                status_code=403,
            )
    except Exception as exc:
        log.warning("messaging save is_managed check: %s", exc)

    try:
        body = await req.json()
    except Exception:
        body = {}

    enabled = body.get("enabled")
    if isinstance(enabled, str):
        enabled = enabled.strip().lower() in ("1", "true", "yes", "on")
    elif enabled is not None:
        enabled = bool(enabled)
    else:
        gc0 = load_gateway_config()
        pc0 = gc0.platforms.get(plat)
        enabled = bool(pc0 and pc0.enabled)

    fields_in = body.get("fields")
    if not isinstance(fields_in, dict):
        fields_in = {}

    home_in = body.get("home")
    if home_in is not None and not isinstance(home_in, dict):
        home_in = {}

    wrote: list[str] = []

    def set_env(key: str, value: str) -> None:
        save_env_value(key, value)
        wrote.append(key)

    def clear_env(key: str) -> None:
        if remove_env_value(key):
            wrote.append(f"-{key}")

    if not enabled:
        for ek in _all_env_keys_for_spec(spec):
            clear_env(ek)
    else:
        id_to_env = {f["id"]: f for f in spec.get("fields") or ()}
        for fid, val in fields_in.items():
            fdef = id_to_env.get(fid)
            if not fdef:
                continue
            ek = fdef["env"]
            typ = fdef.get("type", "text")
            if val is None or (isinstance(val, str) and val == "__KEEP__"):
                continue
            if typ == "secret":
                if isinstance(val, str) and not val.strip():
                    continue
                if val == "__CLEAR__":
                    clear_env(ek)
                    continue
                set_env(ek, str(val).strip())
            elif typ == "bool":
                b = _parse_json_bool(val)
                if b is None:
                    continue
                if fdef.get("optional") and b is False:
                    clear_env(ek)
                else:
                    set_env(ek, _env_bool_str(b))
            elif typ == "select":
                s = str(val).strip().lower()
                opts = [str(x).lower() for x in (fdef.get("options") or [])]
                if s in opts:
                    set_env(ek, s)
            else:
                s = str(val).strip()
                if not s and fdef.get("optional"):
                    clear_env(ek)
                else:
                    set_env(ek, s)

        home = spec.get("home") or {}
        chat_env = home.get("chat_env")
        name_env = home.get("name_env")
        if home_in and chat_env:
            cid = str(home_in.get("chat_id") or "").strip()
            nm = str(home_in.get("name") or "").strip()
            if cid:
                set_env(chat_env, cid)
            else:
                clear_env(chat_env)
            if name_env:
                if nm:
                    set_env(name_env, nm)
                else:
                    clear_env(name_env)

    # Merge enabled + home_channel into raw config.yaml (no secrets)
    raw = read_raw_config()
    if not isinstance(raw, dict):
        raw = {}
    plat_yaml = copy.deepcopy(raw.get("platforms") or {})
    if not isinstance(plat_yaml, dict):
        plat_yaml = {}
    block = plat_yaml.get(pid)
    if not isinstance(block, dict):
        block = {}
    block["enabled"] = bool(enabled)
    if not enabled:
        block.pop("home_channel", None)
    # Strip inline secrets we may have inherited — env is source of truth from UI
    for k in ("token", "api_key"):
        block.pop(k, None)
    home = spec.get("home") or {}
    chat_env = home.get("chat_env")
    name_env = home.get("name_env")
    if home_in is not None and chat_env:
        cid = str((home_in or {}).get("chat_id") or "").strip()
        nm = str((home_in or {}).get("name") or "").strip() or "Home"
        if cid and enabled:
            block["home_channel"] = {"platform": pid, "chat_id": cid, "name": nm}
        elif not cid or not enabled:
            block.pop("home_channel", None)
    plat_yaml[pid] = block
    raw["platforms"] = plat_yaml
    try:
        save_config(raw)
    except Exception as exc:
        log.exception("save_config failed")
        return JSONResponse({"ok": False, "error": str(exc), "wrote_env_keys": wrote}, status_code=500)

    return JSONResponse(
        {
            "ok": True,
            "wrote_env_keys": wrote,
            "restart_recommended": True,
            "enabled": bool(enabled),
        }
    )


# Legacy paths (read-only + old names) — still registered for compatibility
async def hermes_gateway_status_api(_req: Request) -> JSONResponse:
    return await messaging_gateway_status_api(_req)


async def hermes_gateway_platforms_api(_req: Request) -> JSONResponse:
    """Deprecated list shape; prefer ``GET /api/messaging/overview``."""
    try:
        data = _messaging_overview_payload()
        rows = data.get("platforms") or []
        connected = [r["id"] for r in rows if r.get("connected")]
        return JSONResponse(
            {
                "ok": True,
                "platforms": [{"id": r["id"], "label": r["label"]} for r in rows],
                "connected": connected,
                "setup_hint": data.get("restart_hint", ""),
            }
        )
    except Exception as exc:
        log.warning("hermes_gateway_platforms_api: %s", exc)
        return JSONResponse({"ok": False, "platforms": [], "connected": [], "error": str(exc)})


def _read_animus_env_kv() -> dict[str, str]:
    """Parse ``KEY=value`` pairs from repo-root ``animus.env`` (comments / blanks skipped)."""
    root = Path(__file__).resolve().parent.parent
    path = root / "animus.env"
    out: dict[str, str] = {}
    if not path.is_file():
        return out
    try:
        raw = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return out
    for line in raw.splitlines():
        s = line.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        k, _, v = s.partition("=")
        k = k.strip()
        if not k or not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", k):
            continue
        v = v.strip().strip('"').strip("'")
        out[k] = v
    return out


async def messaging_import_animus_slack_api(_req: Request) -> JSONResponse:
    """If ``animus.env`` has ``SLACK_BOT_TOKEN`` and Hermes env does not, copy token (+ optional home) and enable Slack in ``config.yaml``."""

    from gateway.config import Platform, load_gateway_config

    from hermes_cli.config import is_managed, load_env, read_raw_config, save_config, save_env_value

    try:
        if is_managed():
            return JSONResponse(
                {"ok": False, "error": "Hermes profile is managed — cannot import Slack here."},
                status_code=403,
            )
    except Exception as exc:
        log.warning("messaging_import_animus_slack is_managed: %s", exc)

    animus_kv = _read_animus_env_kv()
    bot = (animus_kv.get("SLACK_BOT_TOKEN") or "").strip()
    default_ch = (animus_kv.get("SLACK_DEFAULT_CHANNEL") or "").strip()

    try:
        env = load_env()
    except Exception as exc:
        return JSONResponse({"ok": False, "error": str(exc)[:500]}, status_code=500)

    if (env.get("SLACK_BOT_TOKEN") or "").strip():
        return JSONResponse({"ok": True, "skipped": True, "reason": "gateway_already_has_bot_token"})

    if not bot:
        return JSONResponse({"ok": True, "skipped": True, "reason": "no_slack_bot_token_in_animus_env"})

    wrote: list[str] = []
    try:
        save_env_value("SLACK_BOT_TOKEN", bot)
        wrote.append("SLACK_BOT_TOKEN")
        if default_ch:
            save_env_value("SLACK_HOME_CHANNEL", default_ch)
            wrote.append("SLACK_HOME_CHANNEL")
    except Exception as exc:
        log.exception("import animus slack save_env_value")
        return JSONResponse({"ok": False, "error": str(exc)[:500]}, status_code=500)

    raw = read_raw_config()
    if not isinstance(raw, dict):
        raw = {}
    plat_yaml = copy.deepcopy(raw.get("platforms") or {})
    if not isinstance(plat_yaml, dict):
        plat_yaml = {}
    block = plat_yaml.get("slack")
    if not isinstance(block, dict):
        block = {}
    block["enabled"] = True
    for k in ("token", "api_key"):
        block.pop(k, None)
    if default_ch:
        block["home_channel"] = {"platform": "slack", "chat_id": default_ch, "name": "Home"}
    else:
        block.pop("home_channel", None)
    plat_yaml["slack"] = block
    raw["platforms"] = plat_yaml
    try:
        save_config(raw)
    except Exception as exc:
        log.exception("import animus slack save_config")
        return JSONResponse({"ok": False, "error": str(exc)[:500], "wrote_env_keys": wrote}, status_code=500)

    try:
        gc = load_gateway_config()
        pc = gc.platforms.get(Platform.SLACK) if gc else None
        enabled = bool(pc and pc.enabled)
    except Exception:
        enabled = True

    return JSONResponse(
        {
            "ok": True,
            "skipped": False,
            "imported": True,
            "wrote_env_keys": wrote,
            "restart_recommended": True,
            "slack_enabled_in_config": enabled,
        }
    )


def messaging_route_table():
    from starlette.routing import Route

    return [
        Route("/api/messaging/gateway-status", messaging_gateway_status_api, methods=["GET"]),
        Route("/api/messaging/overview", messaging_overview_api, methods=["GET"]),
        Route("/api/messaging/import-animus-slack", messaging_import_animus_slack_api, methods=["POST"]),
        Route("/api/messaging/platform/{platform_id}", messaging_platform_get_api, methods=["GET"]),
        Route("/api/messaging/platform/{platform_id}", messaging_platform_post_api, methods=["POST"]),
        Route("/api/integrations/hermes-gateway/status", hermes_gateway_status_api, methods=["GET"]),
        Route("/api/integrations/hermes-gateway/platforms", hermes_gateway_platforms_api, methods=["GET"]),
    ]
