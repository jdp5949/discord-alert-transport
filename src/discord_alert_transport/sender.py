"""Discord webhook transport.

Stdlib-only HTTP client with 429 Retry-After backoff, optional audit mirror,
secret-safe ``__repr__``, and warning-only failure mode (never raises).

Typical usage::

    from discord_alert_transport import Channel, DiscordSender, build_embed

    sender = DiscordSender(
        webhooks={
            Channel.ALERTS: "https://discord.com/api/webhooks/.../...",
            Channel.AUDIT:  "https://discord.com/api/webhooks/.../...",
        },
        enabled=True,
        username="my-app",
        audit_channel=Channel.AUDIT,
    )

    sender.send_embed(
        Channel.ALERTS,
        build_embed(title="Error", description="...", color=0xff0000),
    )
"""
from __future__ import annotations

import json
import logging
import time
from typing import Any, Mapping
from urllib import error as urlerror
from urllib import request as urlrequest

from discord_alert_transport.channels import Channel

logger = logging.getLogger(__name__)

DEFAULT_MAX_RETRIES = 5
DEFAULT_MAX_RETRY_AFTER_S = 30.0
DEFAULT_HTTP_TIMEOUT_S = 10.0
DEFAULT_USERNAME = "notifier-bot"
_AUDIT_TITLE_MAX = 80


class DiscordSender:
    """Discord webhook transport with 429 Retry-After backoff + audit mirror.

    Failures never propagate — only logged at warning level. Webhook URLs are
    treated as secrets; ``__repr__`` reveals only which channels are wired,
    never the URLs themselves.

    Args:
        webhooks: Mapping of ``Channel`` (or any string-coercible key) to
            webhook URL. Empty strings or missing entries are treated as
            "channel disabled".
        enabled: Master switch. When False, all sends become no-ops returning
            False. Useful for env-driven on/off.
        username: ``username`` field shown next to each posted message
            ("bot" name). Defaults to ``notifier-bot``.
        audit_channel: Channel that receives compact mirror lines for every
            successful non-audit send. Pass ``None`` to disable mirroring.
        max_retries: How many times to retry on 429 (default 5).
        http_timeout_s: Per-request HTTP timeout (default 10s).
        max_retry_after_s: Cap on Retry-After sleep (default 30s).
    """

    def __init__(
        self,
        webhooks: Mapping[Channel | str, str],
        *,
        enabled: bool = True,
        username: str = DEFAULT_USERNAME,
        audit_channel: Channel | str | None = Channel.AUDIT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        http_timeout_s: float = DEFAULT_HTTP_TIMEOUT_S,
        max_retry_after_s: float = DEFAULT_MAX_RETRY_AFTER_S,
    ) -> None:
        self._webhooks: dict[str, str] = {
            self._key(k): (v or "").strip()
            for k, v in webhooks.items()
        }
        self._enabled_flag = bool(enabled)
        self._username = username
        self._audit_key = self._key(audit_channel) if audit_channel is not None else None
        self._max_retries = max(1, int(max_retries))
        self._http_timeout_s = float(http_timeout_s)
        self._max_retry_after_s = float(max_retry_after_s)

    @staticmethod
    def _key(channel: Channel | str) -> str:
        return channel.value if isinstance(channel, Channel) else str(channel)

    def __repr__(self) -> str:
        return "DiscordSender(enabled=%s, channels=%s)" % (
            self.enabled,
            sorted(k for k, v in self._webhooks.items() if v),
        )

    @property
    def enabled(self) -> bool:
        return self._enabled_flag and any(self._webhooks.values())

    def send_embed(
        self,
        channel: Channel | str,
        embed: dict[str, Any],
        *,
        content: str = "",
        mirror_to_audit: bool = True,
        allowed_mentions: dict[str, Any] | None = None,
    ) -> bool:
        """POST an embed to a channel webhook. Returns True on 2xx.

        Side effects:
          * Retries up to ``max_retries`` on 429, honouring Retry-After.
          * Mirrors a compact line to the configured audit channel on success
            (skipped when target == audit or ``mirror_to_audit=False``).

        Args:
            channel: Channel enum member or matching string key.
            embed: Discord embed dict (use ``build_embed`` for safety).
            content: Optional plain content above the embed. If non-empty and
                ``allowed_mentions`` is None, the default permits
                ``everyone``/``users``/``roles`` mentions. **Footgun**:
                this means *any* non-empty ``content`` that contains
                ``@everyone``/``@here``/``<@&...>``/``<@...>`` will
                actually mass-ping. Pass an explicit
                ``allowed_mentions={"parse": []}`` to suppress, or pass
                only the mention types you intend (e.g.
                ``{"parse": ["users"]}``).
            mirror_to_audit: Whether to mirror a compact line to the audit
                channel. Recursive audit mirroring is always suppressed.
            allowed_mentions: Optional override of the ``allowed_mentions``
                payload field. Required if you want to disable the
                permissive default described above.
        """
        if not self.enabled:
            return False

        key = self._key(channel)
        url = self._webhooks.get(key, "")
        if not url:
            logger.warning("Discord webhook missing for channel=%s — skip", key)
            return False

        payload: dict[str, Any] = {"username": self._username, "embeds": [embed]}
        if content:
            payload["content"] = content
            payload["allowed_mentions"] = allowed_mentions or {
                "parse": ["everyone", "users", "roles"]
            }
        elif allowed_mentions is not None:
            payload["allowed_mentions"] = allowed_mentions

        ok = self._post_with_backoff(url, payload, key)
        if ok and mirror_to_audit and self._audit_key and key != self._audit_key:
            self._send_audit_mirror(key, embed)
        return ok

    def send_text(self, channel: Channel | str, content: str) -> bool:
        """POST a plain text message (no embed). Returns True on 2xx."""
        if not self.enabled:
            return False
        key = self._key(channel)
        url = self._webhooks.get(key, "")
        if not url:
            return False
        payload = {"username": self._username, "content": content[:2000]}
        return self._post_with_backoff(url, payload, key)

    def _send_audit_mirror(self, source: str, embed: dict[str, Any]) -> None:
        if self._audit_key is None:
            return
        url = self._webhooks.get(self._audit_key, "")
        if not url:
            return
        title = str(embed.get("title", ""))[:_AUDIT_TITLE_MAX]
        color = embed.get("color", 0xFFFFFF)
        line = f"`[{source}]` {title}"
        mirror = {
            "username": self._username,
            "embeds": [{"description": line, "color": color}],
        }
        self._post_with_backoff(url, mirror, self._audit_key, max_retries=2)

    def _post_with_backoff(
        self,
        url: str,
        payload: dict[str, Any],
        channel_name: str,
        *,
        max_retries: int | None = None,
    ) -> bool:
        retries = max_retries if max_retries is not None else self._max_retries
        body = json.dumps(payload).encode()
        headers = {"Content-Type": "application/json"}
        for attempt in range(1, retries + 1):
            try:
                req = urlrequest.Request(url, data=body, headers=headers, method="POST")
                with urlrequest.urlopen(req, timeout=self._http_timeout_s) as resp:
                    code = getattr(resp, "status", 200)
                    if 200 <= code < 300:
                        return True
                    logger.warning(
                        "Discord %s unexpected %d (attempt %d)",
                        channel_name, code, attempt,
                    )
                    return False
            except urlerror.HTTPError as e:
                code = e.code
                if code == 429:
                    wait = self._parse_retry_after(e)
                    if attempt < retries:
                        time.sleep(min(wait + 0.05, self._max_retry_after_s))
                        continue
                    logger.warning(
                        "Discord %s rate-limited %d attempts — dropping",
                        channel_name, retries,
                    )
                    return False
                if 500 <= code < 600:
                    if attempt < retries:
                        time.sleep(1.0)
                        continue
                    logger.warning(
                        "Discord %s HTTP %d after %d attempts — dropping",
                        channel_name, code, retries,
                    )
                    return False
                logger.warning(
                    "Discord %s HTTP %d (attempt %d) — dropping",
                    channel_name, code, attempt,
                )
                return False
            except Exception as exc:
                logger.warning(
                    "Discord %s send failed (attempt %d): %s",
                    channel_name, attempt, type(exc).__name__,
                )
                if attempt < retries:
                    time.sleep(1.0)
                    continue
                return False
        return False

    @staticmethod
    def _parse_retry_after(err: urlerror.HTTPError) -> float:
        try:
            body = json.loads(err.read().decode("utf-8") or "{}")
            return float(body.get("retry_after", 1.0))
        except Exception:
            return 1.0
