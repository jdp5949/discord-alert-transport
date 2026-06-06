# discord-alert-transport — Portability Playbook

Step-by-step for dropping this package into a new Python project and getting
phone notifications within 15 minutes.

## 1. Install (3 options)

### A. Git submodule (recommended for monorepos)

```bash
cd my-new-project
git submodule add https://github.com/jdp5949/dhan-market-data \
    vendor/dhan-market-data
pip install -e vendor/dhan-market-data/packages/discord-alert-transport
```

### B. Vendor copy (no git history)

```bash
cp -R /path/to/dhan-market-data/packages/discord-alert-transport vendor/discord-alert-transport
pip install -e vendor/discord-alert-transport
```

### C. Direct copy of `src/discord_alert_transport/` into your project

If you don't want a pip install at all, copy the four files into your tree:

```
your_project/discord_alert_transport/
    __init__.py
    channels.py
    embed.py
    sender.py
```

Add a `py.typed` next to them if you want mypy to pick up the types.

## 2. Discord server setup (10 min, one-time)

1. Discord app → `+` icon → **Create My Own** → name it (e.g.
   `my-app-prod`).
2. Create 5 text channels (or fewer — only those you'll wire matter):
   `alerts`, `info`, `trades` (skip for non-trading apps), `dev`, `audit`.
3. For each channel: **Edit Channel → Integrations → Webhooks → New
   Webhook → Copy Webhook URL**.
4. Drop the URLs into your env file (NOT a tracked file):

   ```dotenv
   DISCORD_WEBHOOK_ALERTS=https://discord.com/api/webhooks/.../...
   DISCORD_WEBHOOK_INFO=https://discord.com/api/webhooks/.../...
   DISCORD_WEBHOOK_DEV=https://discord.com/api/webhooks/.../...
   DISCORD_WEBHOOK_AUDIT=https://discord.com/api/webhooks/.../...
   NOTIFY_DISCORD_ENABLED=1
   ```

5. Install the Discord mobile app, join the server, set per-channel
   notification levels:
   - `alerts` → **All Messages** + override mute
   - `info` → **Only @mentions**
   - `dev` / `audit` → **Nothing** (mute)
6. (iOS only) Settings → Notifications → Discord → enable.
7. (Optional) Disable "Push Notification Inactive Timeout" in mobile
   Discord settings so phone push fires even when desktop is active.

## 3. Wire the sender

```python
# my_project/notify.py
import os
from discord_alert_transport import Channel, DiscordSender, Severity, build_embed, channel_for, color_for

_sender = DiscordSender(
    webhooks={
        Channel.ALERTS: os.getenv("DISCORD_WEBHOOK_ALERTS", ""),
        Channel.INFO:   os.getenv("DISCORD_WEBHOOK_INFO", ""),
        Channel.DEV:    os.getenv("DISCORD_WEBHOOK_DEV", ""),
        Channel.AUDIT:  os.getenv("DISCORD_WEBHOOK_AUDIT", ""),
    },
    enabled=os.getenv("NOTIFY_DISCORD_ENABLED", "0") == "1",
    username="my-app",
)


def notify(severity: Severity, title: str, description: str, **fields):
    embed = build_embed(
        title=title,
        description=description,
        color=color_for(severity),
        fields=[{"name": k, "value": str(v)} for k, v in fields.items()],
    )
    mention = "@everyone" if severity == Severity.P0 else ""
    _sender.send_embed(channel_for(severity), embed, content=mention)
```

Call it anywhere:

```python
from my_project.notify import notify, Severity

notify(Severity.P1, "Auth failure", "JWT signature mismatch", user_id=42, ip="1.2.3.4")
notify(Severity.P3, "Deploy complete", "v1.4.7 → prod", duration_s=23)
```

## 4. Async fire-and-forget queue (optional but recommended)

The package send is **synchronous** by design (so the caller decides the
threading model). For request handlers / hot loops, wrap with a daemon
thread + queue so callers never block on HTTP:

```python
# my_project/notify_async.py
import queue
import threading
from my_project.notify import _sender, build_embed, channel_for, color_for, Severity

_Q = queue.Queue(maxsize=500)

def _worker():
    while True:
        task = _Q.get()
        if task is None:
            return
        try:
            task()
        finally:
            _Q.task_done()

threading.Thread(target=_worker, daemon=True).start()


def anotify(severity: Severity, title: str, description: str, **fields):
    def _t():
        embed = build_embed(
            title=title, description=description, color=color_for(severity),
            fields=[{"name": k, "value": str(v)} for k, v in fields.items()],
        )
        _sender.send_embed(channel_for(severity), embed)
    try:
        _Q.put_nowait(_t)
    except queue.Full:
        pass  # drop on overflow
```

For asyncio projects, run `send_embed` in a thread-pool executor:

```python
import asyncio

async def anotify(sev, title, desc, **fields):
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, notify, sev, title, desc, **fields)
```

## 5. Pre-commit hook (block leaked webhook URLs)

Copy `scripts/git-hooks/pre-commit-discord-leak.sh` from this repo into the
target project and install:

```bash
cp scripts/git-hooks/pre-commit-discord-leak.sh \
    target-project/scripts/git-hooks/
chmod +x target-project/scripts/git-hooks/pre-commit-discord-leak.sh
cd target-project
ln -s ../../scripts/git-hooks/pre-commit-discord-leak.sh .git/hooks/pre-commit
```

The hook blocks any staged diff line containing a real-shape Discord
webhook URL (17+ digit ID, 50+ char token). Short test stubs are allowed.

## 6. Smoke test

Quickest verification:

```python
# scripts/discord_smoke.py
from discord_alert_transport import Channel, DiscordSender, Severity, build_embed, channel_for, color_for
import os

s = DiscordSender(
    webhooks={
        Channel.ALERTS: os.getenv("DISCORD_WEBHOOK_ALERTS", ""),
        Channel.INFO:   os.getenv("DISCORD_WEBHOOK_INFO", ""),
        Channel.DEV:    os.getenv("DISCORD_WEBHOOK_DEV", ""),
        Channel.AUDIT:  os.getenv("DISCORD_WEBHOOK_AUDIT", ""),
    },
    enabled=True,
)

for sev in (Severity.P0, Severity.P1, Severity.P2, Severity.P3, Severity.DEV):
    s.send_embed(
        channel_for(sev),
        build_embed(title=f"SMOKE {sev.name}", description="ignore", color=color_for(sev)),
        content="@everyone" if sev == Severity.P0 else "",
    )
print("done — check Discord")
```

```bash
python scripts/discord_smoke.py
```

You should see five embeds — one per channel — colour-coded.

## 7. Rotate webhooks

Discord webhook URLs leaked into chat or commits should be rotated. Each
channel → **Edit Channel → Integrations → Webhooks → Delete** the leaked
one and create a new one. URLs are not user-tied; rotation has no other
side effect.

## 8. Real-world tips

- **Throttle/dedup at your edge.** This package does not dedupe identical
  messages — wrap with a `key → last_ts` map and skip if you fire the same
  alert in <60s.
- **Use threads for P0 follow-up.** Reply to the alert message inside
  Discord to keep postmortem discussion attached.
- **Audit channel = source of truth.** Build dashboards / search off
  `#audit` rather than scrolling other channels.
- **Don't enable on local dev.** Set `NOTIFY_DISCORD_ENABLED=0` in dev
  `.env` to keep your prod Discord clean.
- **Periodic webhook hygiene.** Rotate URLs quarterly even without
  leaks — easy practice.

## 9. Need phone-rings-from-silent-mode?

This package does push notifications only — it can't make a phone ring.
For genuine wake-up on silent / DND, layer one of:

- **Twilio** voice call — official, ~$3/mo + per-call
- **Pushover** Pro — iOS Critical Alerts entitlement, $4.99/yr
- **CallMeBot** — free WhatsApp/Telegram voice call (unofficial, no SLA)

These integrate alongside this package — fire Discord for visual, plus
one of the above for audible. See the parent repo's `docs/todo/` for
example wiring.
