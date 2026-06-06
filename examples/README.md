# Examples — multi-language Discord webhook senders

Discord webhooks are plain HTTP POST + JSON. Any language that can POST to
HTTPS can talk to them. The Python package in this repo is one convenient
wrapper — these examples show the same behaviour in 10 other languages so
you can drop the pattern into whatever stack you already use.

All examples implement the same essentials:

- POST JSON to a webhook URL
- 429 Retry-After backoff (Discord rate limit: 5 per 1s per webhook)
- 5xx single retry
- Read webhook URL from `DISCORD_WEBHOOK` env var (never hard-code secrets)

| Folder | Language | Runtime needed |
|--------|----------|----------------|
| [`python/`](python/) | Python 3.10+ | the `discord_alert_transport` package (`pip install discord-alert-transport`) — full-featured |
| [`javascript/`](javascript/) | Node.js 18+ | stdlib `fetch` |
| [`typescript/`](typescript/) | TypeScript / Node 18+ | `tsx` or `tsc` |
| [`go/`](go/) | Go 1.21+ | stdlib `net/http` |
| [`rust/`](rust/) | Rust | `reqwest` + `tokio` + `serde_json` |
| [`bash/`](bash/) | bash 4+ | `curl` (+ optional `jq` for clean retry parsing) |
| [`php/`](php/) | PHP 8+ | stdlib `curl` |
| [`ruby/`](ruby/) | Ruby 3+ | stdlib `net/http` |
| [`java/`](java/) | Java 11+ | stdlib `java.net.http` |
| [`csharp/`](csharp/) | .NET 6+ | stdlib `System.Net.Http` |

## Run any example

```bash
export DISCORD_WEBHOOK="https://discord.com/api/webhooks/<id>/<token>"
# pick one:
python examples/python/basic.py
node    examples/javascript/send.js
tsx     examples/typescript/send.ts
go      run examples/go/send.go
cargo   run --manifest-path examples/rust/Cargo.toml      # add minimal Cargo.toml first
bash    examples/bash/send.sh
php     examples/php/send.php
ruby    examples/ruby/send.rb
java    examples/java/Send.java
dotnet  run --project examples/csharp/                    # add Send.csproj first
```

## Want the full Python package features?

The Python package adds severity routing, audit mirror, secret-safe
`__repr__`, and channel enums on top of the raw HTTP pattern. The other
language examples here implement only the raw send. If you want feature
parity in Node/Go/etc., port `src/discord_alert_transport/sender.py` — it's
~150 lines.
