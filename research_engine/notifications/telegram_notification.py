"""
Telegram Notification

Implements TelegramNotificationService, per IMP-09C. It formats, and
when enabled and configured, sends an "Approved Research" notification
via Telegram's Bot API, using only the Python standard library
(urllib.request) -- no external HTTP library is required.

Sending is gated behind Enabled (default False): with Enabled False, or
without a Bot Token and Chat ID configured, no network call is ever
made -- send() simply reports that nothing was sent, and the message it
would have sent is still returned so a caller (or a test) can inspect
it. This mirrors every other placeholder-era component in this project:
nothing here calls a live external service unless explicitly,
deliberately configured to.
"""

from __future__ import annotations

import json
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


class TelegramNotificationError(Exception):
    """Raised internally when an enabled, configured send attempt fails
    to reach Telegram's Bot API. Never propagates out of send() -- a
    failed notification is reported in the returned NotificationResult,
    not raised, since a notification is a best-effort side effect."""


_DEFAULT_MESSAGE_TEMPLATE = (
    "✅ Research Approved\n\n"
    "Research ID: {research_id}\n"
    "Topic: {topic}\n"
    "Category: {category}\n"
    "Approval Time: {approval_time}\n"
    "Chart Included: {chart_included}\n\n"
    "Ready for Script Generation"
)


@dataclass
class TelegramConfig:
    """Telegram Notification configuration, per IMP-09C: Enabled, Bot
    Token, Chat ID, Message Template."""

    enabled: bool = False
    bot_token: Optional[str] = None
    chat_id: Optional[str] = None
    message_template: str = field(default=_DEFAULT_MESSAGE_TEMPLATE)


@dataclass
class NotificationResult:
    """The outcome of one send() call."""

    sent: bool
    message: str
    reason: str


class TelegramNotificationService:
    """Formats and, when enabled and configured, sends an Approved
    Research notification over Telegram's Bot API."""

    def __init__(self, config: Optional[TelegramConfig] = None) -> None:
        self.config = config or TelegramConfig()

    def build_message(
        self,
        research_id: str,
        topic: Optional[str],
        category: Optional[str],
        approval_time: datetime,
        chart_included: bool,
    ) -> str:
        """Render the Notification Example's message shape, per IMP-09C:
        Research ID, Topic, Category, Approval Time, Chart Included,
        Ready for Script Generation."""
        return self.config.message_template.format(
            research_id=research_id,
            topic=topic or "Not provided",
            category=category or "Not provided",
            approval_time=approval_time.isoformat(sep=" "),
            chart_included="Yes" if chart_included else "No",
        )

    def send(
        self,
        research_id: str,
        topic: Optional[str] = None,
        category: Optional[str] = None,
        approval_time: Optional[datetime] = None,
        chart_included: bool = False,
    ) -> NotificationResult:
        """Trigger Telegram Notification.

        Always builds the message. Only actually sends it when Enabled
        is True and both Bot Token and Chat ID are configured; a failed
        send is reported, never raised.
        """
        message = self.build_message(
            research_id,
            topic,
            category,
            approval_time or datetime.now(),
            chart_included,
        )

        if not self.config.enabled:
            return NotificationResult(
                sent=False, message=message, reason="Notifications disabled."
            )
        if not self.config.bot_token or not self.config.chat_id:
            return NotificationResult(
                sent=False,
                message=message,
                reason="Bot Token or Chat ID not configured.",
            )

        try:
            self._send_via_telegram_api(message)
        except TelegramNotificationError as error:
            return NotificationResult(sent=False, message=message, reason=str(error))

        return NotificationResult(sent=True, message=message, reason="Sent.")

    def _send_via_telegram_api(self, message: str) -> None:
        """Send `message` via Telegram's Bot API. Isolated in its own
        method, using only urllib.request, so tests can override it
        without ever making a real network call."""
        url = f"https://api.telegram.org/bot{self.config.bot_token}/sendMessage"
        payload = json.dumps({"chat_id": self.config.chat_id, "text": message}).encode(
            "utf-8"
        )
        request = urllib.request.Request(
            url, data=payload, headers={"Content-Type": "application/json"}
        )
        try:
            urllib.request.urlopen(request, timeout=10)
        except Exception as error:
            raise TelegramNotificationError(
                f"Failed to send Telegram notification: {error}"
            ) from error
