"""Unit tests for research_engine.notifications.telegram_notification."""

import unittest
from datetime import datetime
from unittest.mock import patch

from research_engine.notifications.telegram_notification import (
    NotificationResult,
    TelegramConfig,
    TelegramNotificationError,
    TelegramNotificationService,
)


class RecordingTelegramNotificationService(TelegramNotificationService):
    """A TelegramNotificationService whose actual network-sending step is
    replaced with in-memory recording, so tests can exercise the full
    send() logic without ever making a real network call."""

    def __init__(self, config=None):
        super().__init__(config)
        self.sent_messages = []

    def _send_via_telegram_api(self, message: str) -> None:
        self.sent_messages.append(message)


class FailingTelegramNotificationService(TelegramNotificationService):
    """A TelegramNotificationService whose send step always fails, to
    test send()'s graceful failure handling."""

    def _send_via_telegram_api(self, message: str) -> None:
        raise TelegramNotificationError("Simulated network failure.")


class TestBuildMessage(unittest.TestCase):
    def test_message_contains_every_documented_field(self):
        service = TelegramNotificationService()
        message = service.build_message(
            research_id="RS-20260709-001",
            topic="Full analysis ahead of quarterly results next week.",
            category="Stock Analysis",
            approval_time=datetime(2026, 7, 9, 10, 30, 0),
            chart_included=True,
        )
        self.assertIn("Research Approved", message)
        self.assertIn("RS-20260709-001", message)
        self.assertIn("Full analysis ahead of quarterly results next week.", message)
        self.assertIn("Stock Analysis", message)
        self.assertIn("2026-07-09 10:30:00", message)
        self.assertIn("Chart Included: Yes", message)
        self.assertIn("Ready for Script Generation", message)

    def test_missing_topic_and_category_render_as_not_provided(self):
        service = TelegramNotificationService()
        message = service.build_message(
            research_id="RS-20260709-001",
            topic=None,
            category=None,
            approval_time=datetime(2026, 7, 9, 10, 30, 0),
            chart_included=False,
        )
        self.assertIn("Topic: Not provided", message)
        self.assertIn("Category: Not provided", message)
        self.assertIn("Chart Included: No", message)


class TestSendDisabledByDefault(unittest.TestCase):
    def test_default_config_never_sends(self):
        service = RecordingTelegramNotificationService()
        result = service.send(research_id="RS-20260709-001")
        self.assertFalse(result.sent)
        self.assertIn("disabled", result.reason.lower())
        self.assertEqual(service.sent_messages, [])

    def test_result_still_carries_the_would_be_message(self):
        service = RecordingTelegramNotificationService()
        result = service.send(research_id="RS-20260709-001", topic="Latest announcement.")
        self.assertIsInstance(result, NotificationResult)
        self.assertIn("RS-20260709-001", result.message)


class TestSendEnabledButUnconfigured(unittest.TestCase):
    def test_enabled_without_bot_token_does_not_send(self):
        config = TelegramConfig(enabled=True, bot_token=None, chat_id="12345")
        service = RecordingTelegramNotificationService(config)
        result = service.send(research_id="RS-20260709-001")
        self.assertFalse(result.sent)
        self.assertIn("not configured", result.reason.lower())
        self.assertEqual(service.sent_messages, [])

    def test_enabled_without_chat_id_does_not_send(self):
        config = TelegramConfig(enabled=True, bot_token="token", chat_id=None)
        service = RecordingTelegramNotificationService(config)
        result = service.send(research_id="RS-20260709-001")
        self.assertFalse(result.sent)
        self.assertEqual(service.sent_messages, [])


class TestSendEnabledAndConfigured(unittest.TestCase):
    def test_sends_when_fully_configured(self):
        config = TelegramConfig(enabled=True, bot_token="token", chat_id="12345")
        service = RecordingTelegramNotificationService(config)
        result = service.send(
            research_id="RS-20260709-001",
            topic="Full analysis ahead of quarterly results next week.",
            category="Stock Analysis",
        )
        self.assertTrue(result.sent)
        self.assertEqual(len(service.sent_messages), 1)
        self.assertIn("RS-20260709-001", service.sent_messages[0])

    def test_a_failed_send_is_reported_not_raised(self):
        config = TelegramConfig(enabled=True, bot_token="token", chat_id="12345")
        service = FailingTelegramNotificationService(config)
        result = service.send(research_id="RS-20260709-001")
        self.assertFalse(result.sent)
        self.assertIn("Simulated network failure", result.reason)


class TestRealTelegramApiCallIsMockedNotLive(unittest.TestCase):
    def test_send_via_telegram_api_uses_urllib_without_a_real_network_call(self):
        config = TelegramConfig(enabled=True, bot_token="token", chat_id="12345")
        service = TelegramNotificationService(config)
        with patch("urllib.request.urlopen") as mock_urlopen:
            result = service.send(research_id="RS-20260709-001")
        mock_urlopen.assert_called_once()
        self.assertTrue(result.sent)

    def test_send_via_telegram_api_reports_failure_when_urlopen_raises(self):
        config = TelegramConfig(enabled=True, bot_token="token", chat_id="12345")
        service = TelegramNotificationService(config)
        with patch("urllib.request.urlopen", side_effect=OSError("network down")):
            result = service.send(research_id="RS-20260709-001")
        self.assertFalse(result.sent)
        self.assertIn("network down", result.reason)


if __name__ == "__main__":
    unittest.main()
