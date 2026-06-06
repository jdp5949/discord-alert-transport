---
title: discord-alert-transport
---

# discord-alert-transport

**Portable Discord webhook transport for every language and any
application — Python package + 10-language reference + production
patterns for severity routing, rate-limit backoff, audit history, and
secret hygiene.**

[GitHub repo](https://github.com/jdp5949/discord-alert-transport) · [PyPI-ready Python package](https://github.com/jdp5949/discord-alert-transport/tree/main/src/discord_alert_transport) · [10 language examples](https://github.com/jdp5949/discord-alert-transport/tree/main/examples)

---

## The 30-second version

A Discord **webhook** is a public URL Discord generates per channel. POST
JSON to it and a message appears. That's it. Free, instant, no bot
account, no OAuth, no SDK strictly required.

```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"content":"hello"}' \
  https://discord.com/api/webhooks/.../...
```

This repo ships:

1. A **Python package** (`discord_alert_transport`) with batteries — severity
   routing, 429 backoff, audit-channel mirror, secret-safe logging.
2. **10 language reference implementations** — Python, JS, TS, Go, Rust,
   Bash, PHP, Ruby, Java, C# — so you can drop the same idiom into any
   stack.
3. **Production patterns** — how to fan out alerts by severity, dedupe
   storms, ring a phone from silent mode, audit-trail every event.

---

## Why bother

| Without webhooks | With webhooks |
|------------------|---------------|
| Build a custom dashboard | Push to Discord, view on phone |
| Set up PagerDuty ($$$) | Push to Discord + add ntfy for free wake-up |
| Email floods inbox | Channels per severity, colour-coded |
| No history, no search | Unlimited free history, server-wide search |
| Per-user 1:1 alerts | Whole team sees same events instantly |

---

## Pages on this site

- [Quick start](quick-start.html) — Python install + first send in 3 minutes
- [How webhooks work](how-it-works.html) — the underlying protocol, no SDK required
- [Multi-language examples](languages.html) — Node, Go, Rust, Bash, etc.
- [Severity routing](severity-routing.html) — colour-coded channels per priority
- [Use cases](use-cases.html) — 20+ real applications
- [Production patterns](production-patterns.html) — backoff, dedup, audit, security
- [Reference](reference.html) — API + env vars + Discord limits

---

## Install (Python)

```bash
pip install discord-alert-transport
```

Or from this repo:

```bash
pip install git+https://github.com/jdp5949/discord-alert-transport
```

## Hello, world

```python
from discord_alert_transport import Channel, DiscordSender, build_embed

s = DiscordSender(
    webhooks={Channel.ALERTS: "https://discord.com/api/webhooks/.../..."},
    enabled=True,
)
s.send_embed(
    Channel.ALERTS,
    build_embed(title="Hello", description="From discord-alert-transport", color=0x00cc66),
)
```

Phone buzzes.

---

## Licence

MIT. See [LICENSE](https://github.com/jdp5949/discord-alert-transport/blob/main/LICENSE).
