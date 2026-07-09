"""
Telegram Notification module.

Public entry point for the Notifications package, implementing IMP-09C's
Telegram Notification responsibilities.
"""

from .telegram_notification import (
    NotificationResult,
    TelegramConfig,
    TelegramNotificationError,
    TelegramNotificationService,
)

__all__ = [
    "TelegramNotificationService",
    "TelegramConfig",
    "NotificationResult",
    "TelegramNotificationError",
]
