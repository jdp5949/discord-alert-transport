# discord-notifier

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](#)
[![Zero dependencies](https://img.shields.io/badge/runtime%20deps-0-brightgreen.svg)](#)
[![Docs](https://img.shields.io/badge/docs-github.io-blue.svg)](https://jdp5949.github.io/discord/)

**Portable Discord webhook transport. One Python package, ten language
references. From "hello world" to severity-routed phone alerts in 3
minutes.**

📖 **Full documentation:** <https://jdp5949.github.io/discord/>

---

## What this is

A Discord **webhook** is a public URL that turns any HTTP POST into a
Discord channel message. No bot. No OAuth. No SDK strictly required.

This repo gives you:

1. A **Python package** with production batteries — severity routing,
   429 Retry-After backoff, audit-channel mirror, secret-safe logging.
2. **10 language reference implementations** (Python, JS, TS, Go, Rust,
   Bash, PHP, Ruby, Java, C#) — same protocol, your stack.
3. **Production patterns documented** — throttling, dedup, secret
   hygiene, test-suite guards, mobile push setup.

## Why

| Problem | Discord webhook solves it |
|---------|---------------------------|
| Push alerts on my phone, free | yes |
| Different channels per severity | yes |
| Unlimited free message history | yes |
| Colour-coded triage | yes (embeds) |
| Threaded postmortems attached to alerts | yes (Discord threads) |
| Don't want to build a dashboard | yes |
| Don't want to pay for PagerDuty / Opsgenie | yes |
| Use from any language | yes (HTTP POST) |

## Install (Python)

```bash
pip install git+https://github.com/jdp5949/discord
```

(PyPI release pending — for now install from git.)

Requirements: Python 3.10+. Zero runtime dependencies.

## Hello, world

```python
from discord_notifier import Channel, DiscordSender, build_embed

s = DiscordSender(
    webhooks={Channel.ALERTS: "https://discord.com/api/webhooks/.../..."},
    enabled=True,
)
s.send_embed(
    Channel.ALERTS,
    build_embed(title="Hello", description="From discord-notifier", color=0x00cc66),
)
```

Phone buzzes.

## Hello, world (other languages)

### bash + curl

```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"content":"hello from bash"}' "$DISCORD_WEBHOOK"
```

### Node.js

```js
await fetch(process.env.DISCORD_WEBHOOK, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ content: 'hello from node' }),
});
```

### Go

```go
http.Post(os.Getenv("DISCORD_WEBHOOK"), "application/json",
    strings.NewReader(`{"content":"hello from go"}`))
```

See [`examples/`](examples/) for full versions with 429 backoff in 10
languages.

## Five-channel severity layout (convention)

| Channel | Severity | Embed colour |
|---------|----------|--------------|
| `#alerts` | P0 / P1 | red / orange |
| `#info` | P2 / P3 | yellow / green |
| `#trades` | P3 positive event | blue |
| `#dev` | DEV | gray |
| `#audit` | mirror of all events | white |

```python
from discord_notifier import Severity, channel_for, color_for

notify(Severity.P0, "DB down", "Primary unreachable")
notify(Severity.P2, "Cache miss spike", "Hit rate dipped to 60%")
```

Full guide: [Severity routing](https://jdp5949.github.io/discord/severity-routing.html).

## Features

- ✅ **Stdlib only** (`urllib.request`). No `requests`, no `httpx`.
- ✅ **429 Retry-After backoff** — Discord rate-limits at ~5 req/sec/webhook.
- ✅ **Audit mirror** — every send fans a one-liner to a dedicated
  audit channel for searchable history.
- ✅ **Secret-safe** — `__repr__` and log records never include webhook
  URLs.
- ✅ **Failure-silent** — never raises to caller; logs a warning and
  returns `False`.
- ✅ **Length limits enforced** — `build_embed` truncates to Discord
  per-field maxes.
- ✅ **Configurable** — bring your own channel keys, mention defaults,
  retry counts, timeouts.
- ✅ **Backwards-compatible string channel keys** — pass enum members or
  raw strings.

## Layout

```
src/discord_notifier/
    __init__.py          public API
    channels.py          Channel + Severity enums + routing helpers
    embed.py             length-safe embed builder
    sender.py            HTTP transport with 429 backoff + audit mirror
examples/
    python/              full-feature samples
    javascript/          Node 18+ fetch
    typescript/          typed fetch
    go/                  stdlib net/http
    rust/                reqwest + tokio
    bash/                curl
    php/                 stdlib curl
    ruby/                stdlib net/http
    java/                stdlib java.net.http
    csharp/              .NET HttpClient
tests/                   pytest suite (30+ tests)
docs/                    GitHub Pages site source
```

## Tests

```bash
pip install -e .[dev]
pytest
```

## Documentation site

Full hosted documentation, including use cases, production patterns,
and the underlying webhook protocol: **<https://jdp5949.github.io/discord/>**

## Use cases

25+ documented in [use cases](https://jdp5949.github.io/discord/use-cases.html).
Highlights:

- CI/CD pass/fail notifications
- Cron job monitoring
- Prometheus/Grafana alerts
- Backup completion
- Application errors (with throttle/dedup)
- Payment / Stripe webhook relay
- New signup / churn alerts
- IoT sensor alerts (temperature, leak, door)
- Trading / fintech (fills, P&L, risk breaches — this package was
  extracted from one such system)
- Security alerts (failed logins, new IP)
- ChatOps approvals

## Licence

MIT. See [LICENSE](LICENSE).
