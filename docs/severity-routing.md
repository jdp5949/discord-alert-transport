---
title: Severity routing
---

# Severity-routed channels

When your app sends a notification for every kind of event into one
channel, you scroll past the important ones. **Route by severity into
colour-coded channels.** This is the headline feature of the Python
package, and the convention is portable to any language.

## The five-channel layout

| Severity | Channel | Embed colour | Push setting (mobile) |
|----------|---------|--------------|-----------------------|
| **P0 critical** (system down) | `#alerts` | red `0xFF0000` | All Messages + override mute |
| **P1 high** (degraded, halts) | `#alerts` | orange `0xFF8800` | All Messages |
| **P2 medium** (rejects, spikes) | `#info` | yellow `0xFFCC00` | Only @mentions |
| **P3 info / trades** (fills, signups) | `#trades` or `#info` | blue / green | All Messages or @mentions, your taste |
| **DEV** (deploy, cron, debug) | `#dev` | gray `0x808080` | Muted |
| **AUDIT mirror** (every event) | `#audit` | white `0xFFFFFF` | Muted — search history only |

## Python — use the enums

```python
from discord_alert_transport import (
    Channel, DiscordSender, Severity, build_embed, channel_for, color_for,
)

s = DiscordSender(
    webhooks={
        Channel.ALERTS: "https://discord.com/api/webhooks/<a>/<a-token>",
        Channel.INFO:   "https://discord.com/api/webhooks/<b>/<b-token>",
        Channel.TRADES: "https://discord.com/api/webhooks/<c>/<c-token>",
        Channel.DEV:    "https://discord.com/api/webhooks/<d>/<d-token>",
        Channel.AUDIT:  "https://discord.com/api/webhooks/<e>/<e-token>",
    },
    enabled=True,
)

def notify(sev, title, desc, **fields):
    s.send_embed(
        channel_for(sev),
        build_embed(
            title=title,
            description=desc,
            color=color_for(sev),
            fields=[{"name": k, "value": str(v)} for k, v in fields.items()],
        ),
        content="@everyone" if sev == Severity.P0 else "",
    )

notify(Severity.P0, "DB down",       "Primary unreachable 5min")
notify(Severity.P1, "Auth degraded", "p99 over 2s")
notify(Severity.P2, "Cache miss",    "Hit rate 60% (normally 95%)")
notify(Severity.P3, "Daily report",  "Sales dashboard refreshed")
notify(Severity.DEV, "Deploy",       "v2.1.0 → prod")
```

## Same idea, any language

```js
// Minimal severity router in Node
const CHANNELS = {
  P0: { url: process.env.DISCORD_WEBHOOK_ALERTS, color: 0xff0000 },
  P1: { url: process.env.DISCORD_WEBHOOK_ALERTS, color: 0xff8800 },
  P2: { url: process.env.DISCORD_WEBHOOK_INFO,   color: 0xffcc00 },
  P3: { url: process.env.DISCORD_WEBHOOK_TRADES, color: 0x3399ff },
  DEV:{ url: process.env.DISCORD_WEBHOOK_DEV,    color: 0x808080 },
};

async function notify(sev, title, desc) {
  const { url, color } = CHANNELS[sev];
  await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      content: sev === 'P0' ? '@everyone' : '',
      embeds: [{ title, description: desc, color, timestamp: new Date().toISOString() }],
    }),
  });
}
```

## Audit mirror (one channel = full history)

For long-term searchability, fire every event a **second time** as a
compact one-liner to `#audit`. Mute that channel so it doesn't ping you,
but Discord's free-unlimited history means you have a searchable log of
every alert your system has ever fired. The Python package does this
automatically; in other languages it's two `fetch`/`POST` calls instead
of one.

```python
# Python — built in, no extra code
sender = DiscordSender(webhooks={...}, audit_channel=Channel.AUDIT)
sender.send_embed(Channel.ALERTS, embed)  # also lands in #audit
```

## Why this beats a single firehose

- **Triage on the lock screen** — red embed = drop everything. Green = ignore.
- **Mute different severities differently** — sleep through P3 fills,
  wake for P0.
- **Threading** — Discord lets you reply to a P0 alert in a thread,
  keeping incident postmortems attached to the original alert.
- **Per-channel role pings** — `@oncall` only fires for P0.
- **Postmortem search** — six months later, `#alerts` shows you every
  major incident with full context.

Next: [use cases](use-cases.html).
