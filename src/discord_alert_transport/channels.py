"""Channel + Severity enums + routing helpers.

These are conventions, not requirements. You can ignore them and pass any
string as a channel key to DiscordSender — but using the enums keeps
severity-to-channel routing consistent across projects.
"""
from __future__ import annotations

from enum import Enum, IntEnum


class Channel(str, Enum):
    """Conventional channel names. Map each to a webhook URL when constructing DiscordSender."""

    ALERTS = "alerts"
    INFO = "info"
    TRADES = "trades"
    DEV = "dev"
    AUDIT = "audit"


class Severity(IntEnum):
    """Numeric severity. Higher = more urgent."""

    DEV = 0
    P3 = 1
    P2 = 2
    P1 = 3
    P0 = 4


# Embed colour palette (override per-project if you like).
COLOR_P0 = 0xFF0000
COLOR_P1 = 0xFF8800
COLOR_P2 = 0xFFCC00
COLOR_P3_INFO = 0x00CC66
COLOR_P3_TRADE = 0x3399FF
COLOR_DEV = 0x808080
COLOR_AUDIT = 0xFFFFFF


def color_for(severity: Severity, *, is_trade: bool = False) -> int:
    """Return the embed colour for a given severity.

    `is_trade=True` distinguishes a positive trading/business event (blue)
    from a neutral informational P3 (green). Ignore for non-trading projects.
    """
    if severity == Severity.P0:
        return COLOR_P0
    if severity == Severity.P1:
        return COLOR_P1
    if severity == Severity.P2:
        return COLOR_P2
    if severity == Severity.P3:
        return COLOR_P3_TRADE if is_trade else COLOR_P3_INFO
    return COLOR_DEV


def channel_for(severity: Severity, *, is_trade: bool = False) -> Channel:
    """Route a severity to a conventional channel."""
    if severity >= Severity.P1:
        return Channel.ALERTS
    if severity == Severity.P2:
        return Channel.INFO
    if severity == Severity.P3:
        return Channel.TRADES if is_trade else Channel.INFO
    return Channel.DEV


def severity_label(severity: Severity) -> str:
    return {
        Severity.P0: "P0",
        Severity.P1: "P1",
        Severity.P2: "P2",
        Severity.P3: "P3",
        Severity.DEV: "DEV",
    }.get(severity, "?")
