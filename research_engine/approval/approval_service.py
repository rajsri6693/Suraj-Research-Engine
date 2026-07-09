"""
Approval Service

Implements ApprovalService, the approval persistence workflow, per
IMP-09C:

Review Result -> Save Approved Research -> Trigger Telegram Notification

When Human Review returns a ReviewResult whose decision is Approved,
this service persists it using the project's existing persistence layer
(research_database.database_manager.DatabaseManager), and only once
that persistence succeeds does it trigger a Telegram notification. If
the decision is not Approved, or persistence fails, no notification is
ever sent.

It does NOT generate scripts or videos, does NOT call any collector, and
does NOT modify Research Planner, Research Workflow, or Human Review
logic -- it only acts on a ReviewResult those layers already produced.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from research_database.database_manager import DatabaseError, DatabaseManager

from research_engine.notifications.telegram_notification import (
    NotificationResult,
    TelegramNotificationService,
)
from research_engine.review.review_decision import ReviewDecision
from research_engine.review.review_result import ReviewResult

_CREATE_APPROVED_RESEARCH_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS approved_research (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    research_id TEXT NOT NULL,
    reviewed_by TEXT,
    review_notes TEXT,
    review_time TEXT NOT NULL,
    reviewed_sections TEXT NOT NULL,
    approved_at TEXT NOT NULL,
    chart_available INTEGER NOT NULL DEFAULT 0,
    chart_type TEXT
)
"""


class ApprovalPersistenceError(Exception):
    """Raised when persisting an Approved ReviewResult fails for a
    reason other than the underlying database layer's own DatabaseError
    (for example, a malformed ReviewResult)."""


@dataclass
class ApprovalOutcome:
    """The outcome of processing one ReviewResult through the Approval
    Service."""

    persisted: bool
    notified: bool
    reason: str
    notification: Optional[NotificationResult] = None


class ApprovalService:
    """Persists Approved research and, only once persistence succeeds,
    triggers a Telegram notification.

    Owns one DatabaseManager and one TelegramNotificationService, both
    injectable so callers (and tests) can supply an isolated database
    and a stub notifier without ever touching the real project database
    file or a live Telegram bot.
    """

    def __init__(
        self,
        database_manager: Optional[DatabaseManager] = None,
        notifier: Optional[TelegramNotificationService] = None,
    ) -> None:
        self._database_manager = database_manager or DatabaseManager()
        self._notifier = notifier or TelegramNotificationService()
        self._table_ready = False

    def process(
        self,
        review_result: ReviewResult,
        research_topic: Optional[str] = None,
        research_category: Optional[str] = None,
        chart_available: bool = False,
        chart_type: Optional[str] = None,
    ) -> ApprovalOutcome:
        """Receive ReviewResult.

        If its decision is not Approved, stop -- nothing is persisted
        and no notification is sent. If Approved, persist it using the
        existing persistence layer, and only once persistence succeeds,
        trigger a Telegram notification.

        research_topic and research_category are optional context a
        caller may supply to enrich the notification message beyond
        what a ReviewResult alone carries; when omitted, the message
        states them as not provided rather than fabricating a value.

        chart_available and chart_type carry the Chart Generator's own
        output, per IMP-09D -- a caller passes chart_available=True and
        the Chart Type whenever this ReviewResult's Research Plan had
        chart_required=True; both are persisted together with the
        approved research, and chart_available also feeds the existing
        Telegram notification's own Chart Included line.
        """
        if review_result.review_decision != ReviewDecision.APPROVED:
            return ApprovalOutcome(
                persisted=False,
                notified=False,
                reason=(
                    f"Review decision is {review_result.review_decision.value}, "
                    "not Approved."
                ),
            )

        try:
            self._persist(review_result, chart_available, chart_type)
        except (DatabaseError, ApprovalPersistenceError) as error:
            return ApprovalOutcome(
                persisted=False,
                notified=False,
                reason=f"Persistence failed: {error}",
            )

        notification = self._notifier.send(
            research_id=review_result.research_id,
            topic=research_topic,
            category=research_category,
            approval_time=review_result.review_time,
            chart_included=chart_available,
        )

        return ApprovalOutcome(
            persisted=True,
            notified=notification.sent,
            reason="Approved research persisted.",
            notification=notification,
        )

    def _persist(
        self,
        review_result: ReviewResult,
        chart_available: bool,
        chart_type: Optional[str],
    ) -> None:
        """Save Approved Research, together with Chart Available and
        Chart Type per IMP-09D, using the existing persistence layer."""
        self._ensure_table()
        reviewed_sections = [
            section.value for section in review_result.reviewed_sections
        ]
        with self._database_manager.transaction() as tx:
            tx.execute(
                "INSERT INTO approved_research "
                "(research_id, reviewed_by, review_notes, review_time, "
                "reviewed_sections, approved_at, chart_available, chart_type) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    review_result.research_id,
                    review_result.reviewed_by,
                    review_result.review_notes,
                    review_result.review_time.isoformat(sep=" "),
                    json.dumps(reviewed_sections),
                    datetime.now().isoformat(sep=" "),
                    1 if chart_available else 0,
                    chart_type,
                ),
            )

    def _ensure_table(self) -> None:
        if not self._table_ready:
            self._database_manager.execute(_CREATE_APPROVED_RESEARCH_TABLE_SQL)
            self._table_ready = True
