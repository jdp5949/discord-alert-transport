---
title: Reference
---

# Reference

## Python package — public API

### `class DiscordSender`

```python
DiscordSender(
    webhooks: Mapping[Channel | str, str],
    *,
    enabled: bool = True,
    username: str = "notifier-bot",
    audit_channel: Channel | str | None = Channel.AUDIT,
    max_retries: int = 5,
    http_timeout_s: float = 10.0,
    max_retry_after_s: float = 30.0,
)
```

Methods:

- `send_embed(channel, embed, *, content="", mirror_to_audit=True, allowed_mentions=None) -> bool`
- `send_text(channel, content) -> bool`
- `enabled` (property) — `True` iff master flag on AND at least one webhook configured.

### `class Channel(str, Enum)`

`ALERTS, INFO, TRADES, DEV, AUDIT`. Use members or matching strings.

### `class Severity(IntEnum)`

`P0 (4), P1 (3), P2 (2), P3 (1), DEV (0)`.

### Routing helpers

- `channel_for(severity, *, is_trade=False) -> Channel`
- `color_for(severity, *, is_trade=False) -> int`
- `severity_label(severity) -> str`

### Colour constants

`COLOR_P0, COLOR_P1, COLOR_P2, COLOR_P3_INFO, COLOR_P3_TRADE, COLOR_DEV, COLOR_AUDIT`.

### Embed builder

```python
build_embed(
    *,
    title: str,
    description: str,
    color: int,
    fields: list[dict] | None = None,
    footer: str | None = None,
    timestamp: str | None = None,
) -> dict
```

Truncates each field to Discord limits (title 256, description 4096,
field name 256, field value 1024, 25 fields max, footer 2048).

## Env vars (Python — recommended convention)

| Variable | Purpose |
|----------|---------|
| `DISCORD_WEBHOOK_ALERTS` | Webhook URL for the `alerts` channel |
| `DISCORD_WEBHOOK_INFO` | … `info` |
| `DISCORD_WEBHOOK_TRADES` | … `trades` |
| `DISCORD_WEBHOOK_DEV` | … `dev` |
| `DISCORD_WEBHOOK_AUDIT` | … `audit` |
| `NOTIFY_DISCORD_ENABLED` | `1` to enable, `0` to disable (master switch) |
| `DISCORD_P0_MENTION` | What to ping on P0 (default `@everyone`) |

The package itself reads `webhooks=` from its constructor — these env
names are a project-side convention, used by the included shim in the
parent repo.

## Discord webhook URL format

```
https://discord.com/api/webhooks/<id>/<token>
```

- `<id>` — 17-20 digit Discord snowflake.
- `<token>` — 60+ char base64-url. Acts as the API key.

## Discord embed schema (full)

```jsonc
{
  "title": "string (<= 256)",
  "description": "string (<= 4096, markdown)",
  "url": "https://...",
  "timestamp": "ISO-8601 string",
  "color": 16711680,                          // 24-bit RGB int
  "footer": { "text": "string (<= 2048)", "icon_url": "https://..." },
  "image": { "url": "https://..." },
  "thumbnail": { "url": "https://..." },
  "author": { "name": "string (<= 256)", "url": "...", "icon_url": "..." },
  "fields": [
    { "name": "string (<= 256)", "value": "string (<= 1024)", "inline": true }
  ]
}
```

## Rate limits (observed)

| Scope | Limit | Reset |
|-------|-------|-------|
| Per webhook bucket | 5 requests | 1 second |
| Per webhook soft | ~30 messages | 60 seconds |
| Per channel total | 50 messages | 1 second |
| Body size | 8 MB |  |
| Embed JSON total | 6000 chars |  |

Rate-limit headers on responses:

```
x-ratelimit-limit:        5
x-ratelimit-remaining:    4
x-ratelimit-reset-after:  1.0
x-ratelimit-bucket:       <bucket-id>
```

On 429:

```json
{ "message": "...", "retry_after": 0.5, "global": false }
```

## HTTP responses

| Code | Meaning |
|------|---------|
| `200 OK` | Sent (with response body, rare for webhooks) |
| `204 No Content` | Sent (typical) |
| `400 Bad Request` | Payload malformed / over length limit |
| `401 Unauthorized` | Token wrong |
| `403 Forbidden` | Permission revoked |
| `404 Not Found` | Webhook deleted |
| `429 Too Many Requests` | Rate-limited, see `retry_after` |
| `5xx` | Discord transient |

## Length limits

| Field | Max |
|-------|-----|
| `content` | 2000 chars |
| `embeds` array | 10 entries |
| `embed.title` | 256 |
| `embed.description` | 4096 |
| `embed.fields` | 25 entries |
| `embed.fields[].name` | 256 |
| `embed.fields[].value` | 1024 |
| `embed.footer.text` | 2048 |
| `embed.author.name` | 256 |
| Total embed JSON | 6000 |
| `username` override | 80 |
| File attachment | 25 MB (free), 500 MB (Nitro) |

## Allowed mentions

```jsonc
{
  "parse": ["roles", "users", "everyone"],   // which mention types to actually ping
  "roles": ["123", "456"],                   // OR exact role IDs (overrides parse:roles)
  "users": ["789"],                          // OR exact user IDs
  "replied_user": true
}
```

`parse: []` = suppress all mentions even if syntax is in `content`.

## Useful colour values

```
0xFF0000  red          P0 critical
0xFF8800  orange       P1 high
0xFFCC00  yellow       P2 medium
0x00CC66  green        P3 positive
0x3399FF  blue         P3 neutral / trade
0x808080  gray         DEV / debug
0xFFFFFF  white        audit
0x9933CC  purple       custom
0x009999  teal         custom
```

## Links

- [Discord webhook docs (official)](https://discord.com/developers/docs/resources/webhook)
- [Embed visualizer (online)](https://discohook.org/) — paste payload, see what it'll look like
- [This repo](https://github.com/jdp5949/discord-alert-transport)
