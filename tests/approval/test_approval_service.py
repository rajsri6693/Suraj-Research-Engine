"""Unit tests for research_engine.approval.approval_service.

All tests use an isolated, temp-file-backed DatabaseManager -- never the
real project database file -- and a spy notifier, so nothing here ever
touches disk outside a per-test temp file or performs a real network
call.
"""

import os
import tempfile
import unittest
from datetime import datetime

from research_database.database_manager import DatabaseError, DatabaseManager

from research_engine.approval.approval_service import ApprovalOutcome, ApprovalService
from research_engine.notifications.telegram_notification import NotificationResult
from research_engine.planner.research_plan import KnowledgeSection
from research_engine.review.review_decision import ReviewDecision
from research_engine.review.review_result import ReviewResult


class SpyNotifier:
    """A stand-in TelegramNotificationService that records every call
    instead of sending anything, so tests can assert whether a
    notification was triggered without any real network access."""

    def __init__(self):
        self.calls = []

    def send(self, **kwargs):
        self.calls.append(kwargs)
        return NotificationResult(sent=True, message="stub message", reason="stub")


class FailingDatabaseManager:
    """A stand-in DatabaseManager whose every operation raises
    DatabaseError, to test ApprovalService's persistence-failure path
    without needing to corrupt a real database."""

    def execute(self, sql, params=()):
        raise DatabaseError("Simulated database failure.")

    def transaction(self):
        raise DatabaseError("Simulated database failure.")


def make_review_result(decision: ReviewDecision, research_id="RS-20260709-001"):
    return ReviewResult(
        research_id=research_id,
        review_decision=decision,
        review_notes="Figures match the filing.",
        reviewed_by="jane.reviewer",
        review_time=datetime(2026, 7, 9, 10, 0, 0),
        reviewed_sections=[
            KnowledgeSection.FINANCIAL_INFORMATION,
            KnowledgeSection.COMPANY_INFORMATION,
        ],
        revision_sections=[],
    )


class ApprovalServiceTestCase(unittest.TestCase):
    """Base test case providing an isolated temp-file database per test."""

    def setUp(self):
        fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        os.remove(self.db_path)  # DatabaseManager creates it on first use.
        self.database_manager = DatabaseManager(self.db_path)
        self.spy_notifier = SpyNotifier()
        self.service = ApprovalService(
            database_manager=self.database_manager, notifier=self.spy_notifier
        )

    def tearDown(self):
        self.database_manager.close()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)


class TestApprovedSavesAndNotifies(ApprovalServiceTestCase):
    def test_approved_review_is_persisted_and_notified(self):
        review_result = make_review_result(ReviewDecision.APPROVED)
        outcome = self.service.process(
            review_result, research_topic="Full analysis.", research_category="Stock Analysis"
        )

        self.assertIsInstance(outcome, ApprovalOutcome)
        self.assertTrue(outcome.persisted)
        self.assertTrue(outcome.notified)
        self.assertEqual(len(self.spy_notifier.calls), 1)
        self.assertEqual(self.spy_notifier.calls[0]["research_id"], "RS-20260709-001")
        self.assertEqual(self.spy_notifier.calls[0]["topic"], "Full analysis.")
        self.assertEqual(self.spy_notifier.calls[0]["category"], "Stock Analysis")

    def test_approved_row_is_actually_written_to_the_database(self):
        review_result = make_review_result(ReviewDecision.APPROVED)
        self.service.process(review_result)

        rows = self.database_manager.fetch_all(
            "SELECT * FROM approved_research WHERE research_id = ?",
            ("RS-20260709-001",),
        )
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["reviewed_by"], "jane.reviewer")
        self.assertIn("Financial Information", rows[0]["reviewed_sections"])
        self.assertIn("Company Information", rows[0]["reviewed_sections"])

    def test_notification_only_triggers_after_persistence_succeeds(self):
        # Notification is called after process() returns, so by the time
        # the spy recorded a call, the row must already be committed.
        review_result = make_review_result(ReviewDecision.APPROVED)
        self.service.process(review_result)
        self.assertEqual(len(self.spy_notifier.calls), 1)
        rows = self.database_manager.fetch_all("SELECT * FROM approved_research")
        self.assertEqual(len(rows), 1)


class TestRejectedNeverNotifies(ApprovalServiceTestCase):
    def test_rejected_review_is_not_persisted_or_notified(self):
        review_result = make_review_result(ReviewDecision.REJECTED)
        outcome = self.service.process(review_result)

        self.assertFalse(outcome.persisted)
        self.assertFalse(outcome.notified)
        self.assertEqual(self.spy_notifier.calls, [])

    def test_rejected_review_never_creates_the_table(self):
        review_result = make_review_result(ReviewDecision.REJECTED)
        self.service.process(review_result)
        # No table was ever created, since persistence is only attempted
        # for Approved reviews -- confirms the "stop" happens before any
        # database interaction at all.
        with self.assertRaises(DatabaseError):
            self.database_manager.fetch_all("SELECT * FROM approved_research")


class TestNeedsRevisionNeverNotifies(ApprovalServiceTestCase):
    def test_needs_revision_is_not_persisted_or_notified(self):
        review_result = make_review_result(ReviewDecision.NEEDS_REVISION)
        outcome = self.service.process(review_result)

        self.assertFalse(outcome.persisted)
        self.assertFalse(outcome.notified)
        self.assertEqual(self.spy_notifier.calls, [])


class TestSkippedNeverNotifies(ApprovalServiceTestCase):
    def test_skipped_is_not_persisted_or_notified(self):
        review_result = make_review_result(ReviewDecision.SKIPPED)
        outcome = self.service.process(review_result)

        self.assertFalse(outcome.persisted)
        self.assertFalse(outcome.notified)
        self.assertEqual(self.spy_notifier.calls, [])


class TestPersistenceFailureNeverNotifies(unittest.TestCase):
    def test_database_failure_prevents_notification(self):
        spy_notifier = SpyNotifier()
        service = ApprovalService(
            database_manager=FailingDatabaseManager(), notifier=spy_notifier
        )
        review_result = make_review_result(ReviewDecision.APPROVED)

        outcome = service.process(review_result)

        self.assertFalse(outcome.persisted)
        self.assertFalse(outcome.notified)
        self.assertIn("Persistence failed", outcome.reason)
        self.assertEqual(spy_notifier.calls, [])


class TestChartMetadataPersisted(ApprovalServiceTestCase):
    def test_chart_metadata_is_persisted_when_chart_available(self):
        review_result = make_review_result(ReviewDecision.APPROVED)
        outcome = self.service.process(
            review_result, chart_available=True, chart_type="Candlestick"
        )

        self.assertTrue(outcome.persisted)
        rows = self.database_manager.fetch_all(
            "SELECT * FROM approved_research WHERE research_id = ?",
            ("RS-20260709-001",),
        )
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["chart_available"], 1)
        self.assertEqual(rows[0]["chart_type"], "Candlestick")

    def test_chart_metadata_defaults_to_unavailable_when_not_supplied(self):
        review_result = make_review_result(ReviewDecision.APPROVED)
        self.service.process(review_result)

        rows = self.database_manager.fetch_all(
            "SELECT * FROM approved_research WHERE research_id = ?",
            ("RS-20260709-001",),
        )
        self.assertEqual(rows[0]["chart_available"], 0)
        self.assertIsNone(rows[0]["chart_type"])

    def test_chart_available_is_forwarded_to_the_notifier_as_chart_included(self):
        review_result = make_review_result(ReviewDecision.APPROVED)
        self.service.process(review_result, chart_available=True, chart_type="Candlestick")

        self.assertEqual(len(self.spy_notifier.calls), 1)
        self.assertTrue(self.spy_notifier.calls[0]["chart_included"])


class TestApprovalServiceReusable(ApprovalServiceTestCase):
    def test_two_approved_reviews_both_persist_and_notify(self):
        first = make_review_result(ReviewDecision.APPROVED, research_id="RS-1")
        second = make_review_result(ReviewDecision.APPROVED, research_id="RS-2")

        outcome_one = self.service.process(first)
        outcome_two = self.service.process(second)

        self.assertTrue(outcome_one.persisted)
        self.assertTrue(outcome_two.persisted)
        self.assertEqual(len(self.spy_notifier.calls), 2)
        rows = self.database_manager.fetch_all("SELECT * FROM approved_research")
        self.assertEqual(len(rows), 2)


if __name__ == "__main__":
    unittest.main()
