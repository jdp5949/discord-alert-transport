"""Embed construction helper.

Wraps the awkward Discord embed JSON shape into a single callable that
enforces Discord's length limits (title <=256, description <=4096,
fields <=25, etc).
"""
from __future__ import annotations

import time
from typing import Any


def build_embed(
    *,
    title: str,
    description: str,
    color: int,
    fields: list[dict[str, Any]] | None = None,
    footer: str | None = None,
    timestamp: str | None = None,
) -> dict[str, Any]:
    """Construct a Discord embed dict ready for the webhook ``embeds`` array.

    Args:
        title: <=256 chars (truncated).
        description: <=4096 chars (truncated).
        color: 24-bit RGB int (e.g. ``0xff0000``).
        fields: optional list of ``{"name", "value", "inline"}`` dicts.
            Max 25 entries; name/value clipped to 256/1024 chars.
        footer: optional <=2048 char footer text.
        timestamp: ISO-8601 timestamp string; defaults to ``now`` (UTC).

    Returns:
        A dict suitable for inclusion in the webhook payload's ``embeds`` list.
    """
    embed: dict[str, Any] = {
        "title": title[:256],
        "description": description[:4096],
        "color": int(color),
        "timestamp": timestamp or time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime()),
    }
    if fields:
        embed["fields"] = [
            {
                "name": str(f["name"])[:256],
                "value": str(f["value"])[:1024],
                "inline": bool(f.get("inline", True)),
            }
            for f in fields[:25]
        ]
    if footer:
        embed["footer"] = {"text": str(footer)[:2048]}
    return embed
