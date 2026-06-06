"""Minimal usage example.

Run:
    DISCORD_WEBHOOK_ALERTS=https://discord.com/api/webhooks/.../... \
    DISCORD_WEBHOOK_AUDIT=https://discord.com/api/webhooks/.../...  \
    python examples/basic.py
"""
from __future__ import annotations

import os

from discord_alert_transport import Channel, DiscordSender, Severity, build_embed, channel_for, color_for


def main() -> None:
    sender = DiscordSender(
        webhooks={
            Channel.ALERTS: os.environ.get("DISCORD_WEBHOOK_ALERTS", ""),
            Channel.AUDIT: os.environ.get("DISCORD_WEBHOOK_AUDIT", ""),
        },
        enabled=True,
        username="example-bot",
    )

    if not sender.enabled:
        print("Set DISCORD_WEBHOOK_ALERTS and DISCORD_WEBHOOK_AUDIT env vars first.")
        return

    sev = Severity.P1
    sender.send_embed(
        channel_for(sev),
        build_embed(
            title="Example P1 event",
            description="discord-alert-transport basic example fired this embed.",
            color=color_for(sev),
            fields=[
                {"name": "Source", "value": "examples/basic.py", "inline": True},
                {"name": "Severity", "value": sev.name, "inline": True},
            ],
            footer="discord-alert-transport example",
        ),
    )
    print("sent — check #alerts")


if __name__ == "__main__":
    main()
