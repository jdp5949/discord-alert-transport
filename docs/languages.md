---
title: Multi-language examples
---

# Multi-language Discord webhook examples

All examples implement the same essentials:

- POST JSON to the webhook URL
- 429 Retry-After backoff
- 5xx single retry
- Webhook URL read from `DISCORD_WEBHOOK` env var

Run any of them after exporting the env var:

```bash
export DISCORD_WEBHOOK="https://discord.com/api/webhooks/<id>/<token>"
```

| Language | Runtime needed | Sample |
|----------|----------------|--------|
| [Python](https://github.com/jdp5949/discord-alert-transport/blob/main/examples/python/basic.py) | 3.10+, `pip install discord-alert-transport` | full package — severity routing + audit mirror + backoff |
| [JavaScript (Node)](https://github.com/jdp5949/discord-alert-transport/blob/main/examples/javascript/send.js) | Node 18+, stdlib `fetch` | raw send + backoff |
| [TypeScript](https://github.com/jdp5949/discord-alert-transport/blob/main/examples/typescript/send.ts) | Node 18+, `tsx` | typed embed + backoff |
| [Go](https://github.com/jdp5949/discord-alert-transport/blob/main/examples/go/send.go) | Go 1.21+, stdlib `net/http` | embed + 429/5xx retry |
| [Rust](https://github.com/jdp5949/discord-alert-transport/blob/main/examples/rust/send.rs) | Rust + `reqwest` + `tokio` + `serde_json` | async send + backoff |
| [Bash](https://github.com/jdp5949/discord-alert-transport/blob/main/examples/bash/send.sh) | bash + curl (+ optional jq) | works anywhere curl is installed |
| [PHP](https://github.com/jdp5949/discord-alert-transport/blob/main/examples/php/send.php) | PHP 8+, stdlib `curl` | embed + backoff |
| [Ruby](https://github.com/jdp5949/discord-alert-transport/blob/main/examples/ruby/send.rb) | Ruby 3+, stdlib `net/http` | embed + backoff |
| [Java](https://github.com/jdp5949/discord-alert-transport/blob/main/examples/java/Send.java) | Java 11+, stdlib `java.net.http` | single-file, no Maven |
| [C# (.NET)](https://github.com/jdp5949/discord-alert-transport/blob/main/examples/csharp/Send.cs) | .NET 6+, stdlib `HttpClient` | typed payload + backoff |

## Minimal viable example (any language)

The simplest possible send — no embed, no backoff, no error handling.
Use this to verify wiring before going production.

### curl
```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"content":"hello"}' "$DISCORD_WEBHOOK"
```

### Python (one-liner, no package)
```python
import urllib.request, json
urllib.request.urlopen(urllib.request.Request(
    URL, data=json.dumps({"content": "hello"}).encode(),
    headers={"Content-Type": "application/json"}, method="POST"))
```

### Node.js
```js
await fetch(URL, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({content:'hello'})});
```

### Go
```go
http.Post(URL, "application/json", strings.NewReader(`{"content":"hello"}`))
```

### Bash
```bash
echo '{"content":"hello"}' | curl -d @- -H "Content-Type: application/json" "$URL"
```

## When to use the Python package vs raw HTTP

| Need | Use |
|------|-----|
| Just send a one-off | Any language, raw HTTP |
| Build a long-lived service | Either — port the package's ~150 LOC or `pip install discord-alert-transport` |
| Severity-routed channels + audit mirror | Python package (or port `sender.py`) |
| Embed length limits enforced | Python `build_embed` helper |
| Secret-safe `__repr__` / logging | Python package |
| Async/threaded fan-out | Wrap any of these in your own queue |

## Don't see your language?

The protocol is universal. Any HTTP client + JSON serializer works.
[PR welcome](https://github.com/jdp5949/discord-alert-transport/pulls) — add a sample
under `examples/<language>/`.

Next: [severity routing](severity-routing.html).
