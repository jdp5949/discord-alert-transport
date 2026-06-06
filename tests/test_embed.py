from __future__ import annotations

from discord_alert_transport import build_embed


def test_basic_embed():
    e = build_embed(title="t", description="d", color=0xFF0000)
    assert e["title"] == "t"
    assert e["description"] == "d"
    assert e["color"] == 0xFF0000
    assert "timestamp" in e


def test_title_truncated_to_256():
    e = build_embed(title="x" * 1000, description="d", color=0)
    assert len(e["title"]) == 256


def test_description_truncated_to_4096():
    e = build_embed(title="t", description="x" * 5000, color=0)
    assert len(e["description"]) == 4096


def test_fields_truncated_to_25():
    fields = [{"name": str(i), "value": "v"} for i in range(100)]
    e = build_embed(title="t", description="d", color=0, fields=fields)
    assert len(e["fields"]) == 25


def test_field_value_truncated():
    e = build_embed(
        title="t", description="d", color=0,
        fields=[{"name": "n", "value": "x" * 2000}],
    )
    assert len(e["fields"][0]["value"]) == 1024


def test_footer_truncated_to_2048():
    e = build_embed(title="t", description="d", color=0, footer="x" * 5000)
    assert len(e["footer"]["text"]) == 2048


def test_field_inline_default_true():
    e = build_embed(
        title="t", description="d", color=0,
        fields=[{"name": "n", "value": "v"}],
    )
    assert e["fields"][0]["inline"] is True


def test_field_inline_explicit_false():
    e = build_embed(
        title="t", description="d", color=0,
        fields=[{"name": "n", "value": "v", "inline": False}],
    )
    assert e["fields"][0]["inline"] is False


def test_explicit_timestamp_kept():
    e = build_embed(title="t", description="d", color=0, timestamp="2026-01-01T00:00:00.000Z")
    assert e["timestamp"] == "2026-01-01T00:00:00.000Z"
