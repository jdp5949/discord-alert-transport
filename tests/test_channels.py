from __future__ import annotations

from discord_alert_transport import (
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


def test_severity_ordering():
    assert Severity.DEV < Severity.P3 < Severity.P2 < Severity.P1 < Severity.P0


def test_channel_for_p0_p1_to_alerts():
    assert channel_for(Severity.P0) == Channel.ALERTS
    assert channel_for(Severity.P1) == Channel.ALERTS


def test_channel_for_p2_to_info():
    assert channel_for(Severity.P2) == Channel.INFO
    assert channel_for(Severity.P2, is_trade=True) == Channel.INFO


def test_channel_for_p3_split_on_is_trade():
    assert channel_for(Severity.P3, is_trade=True) == Channel.TRADES
    assert channel_for(Severity.P3, is_trade=False) == Channel.INFO


def test_channel_for_dev():
    assert channel_for(Severity.DEV) == Channel.DEV


def test_color_for_each_severity():
    assert color_for(Severity.P0) == COLOR_P0
    assert color_for(Severity.P1) == COLOR_P1
    assert color_for(Severity.P2) == COLOR_P2
    assert color_for(Severity.P3, is_trade=False) == COLOR_P3_INFO
    assert color_for(Severity.P3, is_trade=True) == COLOR_P3_TRADE
    assert color_for(Severity.DEV) == COLOR_DEV


def test_severity_label():
    assert severity_label(Severity.P0) == "P0"
    assert severity_label(Severity.DEV) == "DEV"
