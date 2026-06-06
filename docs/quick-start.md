---
title: Quick start
---

# Quick start — 3 minutes

## 1. Make a Discord server + channel + webhook (60 sec)

1. Discord app → `+` icon → **Create My Own** → name `my-app-prod`.
2. Right-click the auto-created `#general` (or make a new `#alerts`
   channel) → **Edit Channel** → **Integrations** → **Webhooks** →
   **New Webhook** → **Copy Webhook URL**.

Stash the URL somewhere safe. **Treat it like an API key** — anyone with
the URL can post to your channel (they cannot read it, just post).

## 2. Install

```bash
pip install discord-alert-transport
```

Python 3.10+. Zero runtime dependencies (stdlib only).

## 3. Send

```python
from discord_alert_transport import Channel, DiscordSender, build_embed

s = DiscordSender(
    webhooks={
        Channel.ALERTS: "https://discord.com/api/webhooks/.../...",
    },
    enabled=True,
    username="my-app",
)

s.send_embed(
    Channel.ALERTS,
    build_embed(
        title="Backup completed",
        description="Nightly Postgres dump finished",
        color=0x00cc66,
        fields=[
            {"name": "Size", "value": "12.4 GB", "inline": True},
            {"name": "Duration", "value": "8m 14s", "inline": True},
        ],
        footer="cron / backup.sh",
    ),
)
```

Phone buzzes (assuming Discord mobile app installed + channel
notifications set to "All Messages").

## 4. Don't have Python? Use any language

```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"username":"my-bot","content":"hello world"}' \
  https://discord.com/api/webhooks/.../...
```

Returns `204 No Content` on success. Try it from `node`, `go`, `bash`,
PHP, etc. See [languages](languages.html) for ready-to-paste examples.

## 5. Production checklist

- [ ] Webhook URL stored in env var or secret manager, **never** committed
- [ ] Pre-commit hook blocking `discord.com/api/webhooks/<long>/<long>`
      patterns (sample one in this repo)
- [ ] 429 Retry-After backoff implemented (the Python package does this
      for you)
- [ ] Throttle/dedup at app level so a bug-storm doesn't burn your
      rate-limit budget
- [ ] Mobile push: per-channel **All Messages** + system-level Discord
      notifications **enabled** (off by default!)
- [ ] For wake-from-silent-mode, layer one of: real phone call
      (Twilio/CallMeBot), Pushover Pro, or ntfy.sh priority 5 — Discord
      push alone is silent on iOS silent mode by hardware design

Next: [how it works](how-it-works.html).
