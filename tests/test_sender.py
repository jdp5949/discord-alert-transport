from __future__ import annotations

import io
import json
import logging
from typing import Any
from unittest.mock import patch
from urllib import error as urlerror

from discord_alert_transport import Channel, DiscordSender, build_embed


WEBHOOK_ALERTS = "https://discord.test/webhooks/111111111/aaaa-test-token-1"
WEBHOOK_INFO = "https://discord.test/webhooks/222222222/bbbb-test-token-2"
WEBHOOK_TRADES = "https://discord.test/webhooks/333333333/cccc-test-token-3"
WEBHOOK_DEV = "https://discord.test/webhooks/444444444/dddd-test-token-4"
WEBHOOK_AUDIT = "https://discord.test/webhooks/555555555/eeee-test-token-5"


def _sender(**overrides: Any) -> DiscordSender:
    kwargs: dict[str, Any] = dict(
        webhooks={
            Channel.ALERTS: WEBHOOK_ALERTS,
            Channel.INFO: WEBHOOK_INFO,
            Channel.TRADES: WEBHOOK_TRADES,
            Channel.DEV: WEBHOOK_DEV,
            Channel.AUDIT: WEBHOOK_AUDIT,
        },
        enabled=True,
    )
    kwargs.update(overrides)
    return DiscordSender(**kwargs)


class _FakeResp:
    def __init__(self, status: int = 204) -> None:
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def _http_error(code: int, body: dict[str, Any]) -> urlerror.HTTPError:
    return urlerror.HTTPError(
        url="https://discord.test",
        code=code,
        msg="rate",
        hdrs=None,
        fp=io.BytesIO(json.dumps(body).encode()),
    )


# ------------------------------------------------------------------ #


def test_enabled_requires_flag_and_webhooks():
    assert DiscordSender(webhooks={Channel.ALERTS: WEBHOOK_ALERTS}, enabled=False).enabled is False
    assert DiscordSender(webhooks={Channel.ALERTS: ""}, enabled=True).enabled is False


def test_send_embed_success_204():
    sender = _sender()
    calls: list[str] = []

    def fake_urlopen(req, timeout):
        calls.append(req.full_url)
        return _FakeResp(204)

    with patch("discord_alert_transport.sender.urlrequest.urlopen", side_effect=fake_urlopen):
        ok = sender.send_embed(Channel.ALERTS, build_embed(title="t", description="d", color=0xFF0000))
    assert ok is True
    assert WEBHOOK_ALERTS in calls
    assert WEBHOOK_AUDIT in calls  # audit mirror


def test_send_embed_disabled_flag():
    sender = _sender(enabled=False)
    with patch("discord_alert_transport.sender.urlrequest.urlopen") as up:
        ok = sender.send_embed(Channel.ALERTS, build_embed(title="t", description="d", color=0))
    assert ok is False
    up.assert_not_called()


def test_send_embed_missing_webhook():
    sender = DiscordSender(
        webhooks={Channel.AUDIT: WEBHOOK_AUDIT},  # alerts missing
        enabled=True,
    )
    with patch("discord_alert_transport.sender.urlrequest.urlopen") as up:
        ok = sender.send_embed(Channel.ALERTS, build_embed(title="t", description="d", color=0))
    assert ok is False
    up.assert_not_called()


def test_send_embed_429_backoff_then_success():
    sender = _sender()
    seq = [
        _http_error(429, {"retry_after": 0.01}),
        _http_error(429, {"retry_after": 0.01}),
        _FakeResp(204),
        _FakeResp(204),  # audit mirror
    ]

    def fake_urlopen(req, timeout):
        item = seq.pop(0)
        if isinstance(item, urlerror.HTTPError):
            raise item
        return item

    slept: list[float] = []
    with patch("discord_alert_transport.sender.urlrequest.urlopen", side_effect=fake_urlopen), \
         patch("discord_alert_transport.sender.time.sleep", side_effect=lambda s: slept.append(s)):
        ok = sender.send_embed(Channel.INFO, build_embed(title="t", description="d", color=0))
    assert ok is True
    assert any(s > 0 for s in slept), "Retry-After must trigger sleep"


def test_send_embed_429_exhausted():
    sender = _sender()

    def fake_urlopen(req, timeout):
        raise _http_error(429, {"retry_after": 0.01})

    with patch("discord_alert_transport.sender.urlrequest.urlopen", side_effect=fake_urlopen), \
         patch("discord_alert_transport.sender.time.sleep"):
        ok = sender.send_embed(Channel.DEV, build_embed(title="t", description="d", color=0))
    assert ok is False


def test_send_embed_4xx_drops():
    sender = _sender()

    def fake_urlopen(req, timeout):
        raise _http_error(400, {"message": "Invalid form body"})

    with patch("discord_alert_transport.sender.urlrequest.urlopen", side_effect=fake_urlopen):
        ok = sender.send_embed(Channel.ALERTS, build_embed(title="t", description="d", color=0))
    assert ok is False


def test_send_embed_5xx_retries_once_then_succeeds():
    sender = _sender()
    seq = [
        _http_error(503, {}),
        _FakeResp(204),
        _FakeResp(204),  # audit mirror
    ]

    def fake_urlopen(req, timeout):
        item = seq.pop(0)
        if isinstance(item, urlerror.HTTPError):
            raise item
        return item

    with patch("discord_alert_transport.sender.urlrequest.urlopen", side_effect=fake_urlopen), \
         patch("discord_alert_transport.sender.time.sleep"):
        ok = sender.send_embed(Channel.ALERTS, build_embed(title="t", description="d", color=0))
    assert ok is True


def test_audit_mirror_not_recursive():
    sender = _sender()
    calls: list[str] = []

    def fake_urlopen(req, timeout):
        calls.append(req.full_url)
        return _FakeResp(204)

    with patch("discord_alert_transport.sender.urlrequest.urlopen", side_effect=fake_urlopen):
        sender.send_embed(Channel.AUDIT, build_embed(title="t", description="d", color=0))
    assert calls == [WEBHOOK_AUDIT]


def test_audit_mirror_disabled_via_constructor():
    sender = _sender(audit_channel=None)
    calls: list[str] = []

    def fake_urlopen(req, timeout):
        calls.append(req.full_url)
        return _FakeResp(204)

    with patch("discord_alert_transport.sender.urlrequest.urlopen", side_effect=fake_urlopen):
        sender.send_embed(Channel.ALERTS, build_embed(title="t", description="d", color=0))
    assert calls == [WEBHOOK_ALERTS]


def test_webhook_url_not_in_logs(caplog):
    sender = _sender()
    caplog.set_level(logging.WARNING, logger="discord_alert_transport.sender")

    def fake_urlopen(req, timeout):
        raise _http_error(400, {})

    with patch("discord_alert_transport.sender.urlrequest.urlopen", side_effect=fake_urlopen):
        sender.send_embed(Channel.ALERTS, build_embed(title="t", description="d", color=0))

    secret_token = "aaaa-test-token-1"
    for rec in caplog.records:
        assert secret_token not in rec.getMessage()
        assert WEBHOOK_ALERTS not in rec.getMessage()


def test_repr_does_not_leak_url():
    sender = _sender()
    rep = repr(sender)
    assert "discord.test" not in rep
    assert WEBHOOK_ALERTS not in rep
    assert "alerts" in rep


def test_payload_shape_includes_embed_and_username():
    sender = _sender(username="my-bot")
    captured: list[dict[str, Any]] = []

    def fake_urlopen(req, timeout):
        captured.append(json.loads(req.data.decode()))
        return _FakeResp(204)

    with patch("discord_alert_transport.sender.urlrequest.urlopen", side_effect=fake_urlopen):
        sender.send_embed(
            Channel.ALERTS,
            build_embed(title="HALT", description="loss", color=0xFF0000),
            content="<@everyone>",
        )

    main = captured[0]
    assert main["username"] == "my-bot"
    assert main["embeds"][0]["title"] == "HALT"
    assert main["embeds"][0]["color"] == 0xFF0000
    assert main["content"] == "<@everyone>"
    assert main["allowed_mentions"]["parse"] == ["everyone", "users", "roles"]


def test_send_text_plain():
    sender = _sender()
    captured: list[dict[str, Any]] = []

    def fake_urlopen(req, timeout):
        captured.append(json.loads(req.data.decode()))
        return _FakeResp(204)

    with patch("discord_alert_transport.sender.urlrequest.urlopen", side_effect=fake_urlopen):
        ok = sender.send_text(Channel.DEV, "hello world")
    assert ok is True
    assert captured[0]["content"] == "hello world"
    assert "embeds" not in captured[0]


def test_send_embed_5xx_exhausts_max_retries():
    sender = _sender(max_retries=3)

    def fake_urlopen(req, timeout):
        raise _http_error(503, {})

    sleeps: list[float] = []
    with patch("discord_alert_transport.sender.urlrequest.urlopen", side_effect=fake_urlopen), \
         patch("discord_alert_transport.sender.time.sleep", side_effect=lambda s: sleeps.append(s)):
        ok = sender.send_embed(Channel.ALERTS, build_embed(title="t", description="d", color=0))
    assert ok is False
    # With max_retries=3, two retries happen before final drop (attempts 1,2 sleep; attempt 3 returns False).
    assert len(sleeps) == 2


def test_retry_after_malformed_body_defaults_to_1s():
    sender = _sender(max_retries=2)

    def fake_urlopen(req, timeout):
        # Body is invalid JSON — _parse_retry_after must fall back to 1.0
        raise urlerror.HTTPError(
            url="https://discord.test",
            code=429,
            msg="rate",
            hdrs=None,
            fp=io.BytesIO(b"not-json"),
        )

    sleeps: list[float] = []
    with patch("discord_alert_transport.sender.urlrequest.urlopen", side_effect=fake_urlopen), \
         patch("discord_alert_transport.sender.time.sleep", side_effect=lambda s: sleeps.append(s)):
        ok = sender.send_embed(Channel.ALERTS, build_embed(title="t", description="d", color=0))
    assert ok is False
    assert sleeps and all(0.9 < s < 1.5 for s in sleeps), f"fallback sleep should be ~1s, got {sleeps}"


def test_explicit_allowed_mentions_with_empty_content():
    sender = _sender()
    captured: list[dict[str, Any]] = []

    def fake_urlopen(req, timeout):
        captured.append(json.loads(req.data.decode()))
        return _FakeResp(204)

    with patch("discord_alert_transport.sender.urlrequest.urlopen", side_effect=fake_urlopen):
        sender.send_embed(
            Channel.ALERTS,
            build_embed(title="t", description="d", color=0),
            allowed_mentions={"parse": []},
        )
    # Without content, default branch should still attach explicit allowed_mentions
    assert captured[0].get("allowed_mentions") == {"parse": []}
    assert "content" not in captured[0]


def test_explicit_allowed_mentions_overrides_default_when_content_set():
    sender = _sender()
    captured: list[dict[str, Any]] = []

    def fake_urlopen(req, timeout):
        captured.append(json.loads(req.data.decode()))
        return _FakeResp(204)

    with patch("discord_alert_transport.sender.urlrequest.urlopen", side_effect=fake_urlopen):
        sender.send_embed(
            Channel.ALERTS,
            build_embed(title="t", description="d", color=0),
            content="hello",
            allowed_mentions={"parse": []},  # suppress mass-ping
        )
    assert captured[0]["content"] == "hello"
    assert captured[0]["allowed_mentions"] == {"parse": []}


def test_str_channel_keys_supported():
    sender = DiscordSender(
        webhooks={"alerts": WEBHOOK_ALERTS, "audit": WEBHOOK_AUDIT},
        enabled=True,
    )
    calls: list[str] = []

    def fake_urlopen(req, timeout):
        calls.append(req.full_url)
        return _FakeResp(204)

    with patch("discord_alert_transport.sender.urlrequest.urlopen", side_effect=fake_urlopen):
        ok = sender.send_embed("alerts", build_embed(title="t", description="d", color=0))
    assert ok is True
    assert WEBHOOK_ALERTS in calls
