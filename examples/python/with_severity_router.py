"""Severity-driven routing example.

Demonstrates how to map an arbitrary application event onto the standard
severity → channel routing supplied by discord_alert_transport.
"""
from __future__ import annotations

import os

from discord_alert_transport import (
    Channel,
    DiscordSender,
    Severity,
    build_embed,
    channel_for,
    color_for,
)


def main() -> None:
    sender = DiscordSender(
        webhooks={
            Channel.ALERTS: os.environ["DISCORD_WEBHOOK_ALERTS"],
            Channel.INFO: os.environ.get("DISCORD_WEBHOOK_INFO", ""),
            Channel.TRADES: os.environ.get("DISCORD_WEBHOOK_TRADES", ""),
            Channel.DEV: os.environ.get("DISCORD_WEBHOOK_DEV", ""),
            Channel.AUDIT: os.environ.get("DISCORD_WEBHOOK_AUDIT", ""),
        },
        enabled=True,
        username="severity-demo",
    )

    events = [
        (Severity.P0, "Database down", "Primary RDS instance unreachable for 5 min"),
        (Severity.P1, "Auth service degraded", "Login p99 over 2s"),
        (Severity.P2, "Cache miss spike", "Redis hit-rate 60% (normally 95%)"),
        (Severity.P3, "Daily report ready", "Sales dashboard refreshed"),
        (Severity.DEV, "Deploy complete", "v2.1.0 promoted to prod"),
    ]

    for sev, title, desc in events:
        sender.send_embed(
            channel_for(sev),
            build_embed(
                title=title,
                description=desc,
                color=color_for(sev),
                fields=[{"name": "Severity", "value": sev.name, "inline": True}],
                footer="severity-demo",
            ),
            content="@everyone" if sev == Severity.P0 else "",
        )


if __name__ == "__main__":
    main()
