"""discord-alert-transport — portable Discord webhook transport.

Zero runtime dependencies (stdlib only). Drop-in for any Python 3.10+ project
that needs severity-routed alerting through Discord.

Quick start::

    from discord_alert_transport import DiscordSender, Channel, Severity, build_embed

    sender = DiscordSender(
        webhooks={
            Channel.ALERTS: "https://discord.com/api/webhooks/.../...",
            Channel.AUDIT:  "https://discord.com/api/webhooks/.../...",
        },
        enabled=True,
    )

    sender.send_embed(
        Channel.ALERTS,
        build_embed(
            title="Service degraded",
            description="API p99 over 500ms for 5min",
            color=0xff8800,
            fields=[{"name": "Service", "value": "api", "inline": True}],
        ),
        content="<@&123>",
    )
"""
from __future__ import annotations

from discord_alert_transport.channels import (
    COLOR_AUDIT,
    COLOR_DEV,
    COLOR_P0,
    COLOR_P1,
    COLOR_P2,
    COLOR_P3_INFO,
    COLOR_P3_TRADE,
    Channel,
    Severity,
    channel_for,
    color_for,
    severity_label,
)
from discord_alert_transport.embed import build_embed
from discord_alert_transport.sender import DiscordSender

__all__ = [
    "DiscordSender",
    "Channel",
    "Severity",
    "channel_for",
    "color_for",
    "severity_label",
    "build_embed",
    "COLOR_P0",
    "COLOR_P1",
    "COLOR_P2",
    "COLOR_P3_INFO",
    "COLOR_P3_TRADE",
    "COLOR_DEV",
    "COLOR_AUDIT",
]
__version__ = "0.1.0"
