"""Unit tests for research_engine.api_manager.api_health."""

import unittest
from datetime import datetime, timedelta

from research_engine.api_manager.api_health import (
    FAILURE_STATUSES,
    HealthStatus,
    HealthTracker,
    InvalidHealthStatusError,
)
from research_engine.api_manager.api_provider import Category, ProviderName


class TestDefaultStatus(unittest.TestCase):
    def test_unknown_is_the_default_for_an_unseen_provider(self):
        tracker = HealthTracker()
        health = tracker.get(ProviderName.FMP, Category.FUNDAMENTAL_DATA)
        self.assertEqual(health.status, HealthStatus.UNKNOWN)
        self.assertIsNone(health.last_health_check)
        self.assertEqual(health.consecutive_failures, 0)

    def test_unknown_is_always_usable(self):
        tracker = HealthTracker()
        self.assertTrue(tracker.is_usable(ProviderName.FMP, Category.FUNDAMENTAL_DATA))


class TestRecordSuccess(unittest.TestCase):
    def test_success_sets_online_and_clears_failures(self):
        tracker = HealthTracker()
        tracker.record_failure(
            ProviderName.FMP, Category.FUNDAMENTAL_DATA, HealthStatus.DOWN, "boom"
        )
        health = tracker.record_success(ProviderName.FMP, Category.FUNDAMENTAL_DATA, 12.5)
        self.assertEqual(health.status, HealthStatus.ONLINE)
        self.assertEqual(health.consecutive_failures, 0)
        self.assertIsNone(health.last_error)
        self.assertEqual(health.response_time_ms, 12.5)


class TestRecordFailure(unittest.TestCase):
    def test_rejects_non_failure_statuses(self):
        tracker = HealthTracker()
        with self.assertRaises(InvalidHealthStatusError):
            tracker.record_failure(
                ProviderName.FMP, Category.FUNDAMENTAL_DATA, HealthStatus.ONLINE, "not a failure"
            )
        with self.assertRaises(InvalidHealthStatusError):
            tracker.record_failure(
                ProviderName.FMP, Category.FUNDAMENTAL_DATA, HealthStatus.UNKNOWN, "not a failure"
            )

    def test_accepts_every_failure_status(self):
        tracker = HealthTracker()
        for status in FAILURE_STATUSES:
            health = tracker.record_failure(
                ProviderName.FMP, Category.FUNDAMENTAL_DATA, status, "err"
            )
            self.assertEqual(health.status, status)

    def test_consecutive_failures_accumulate(self):
        tracker = HealthTracker()
        tracker.record_failure(
            ProviderName.FMP, Category.FUNDAMENTAL_DATA, HealthStatus.DOWN, "err1"
        )
        health = tracker.record_failure(
            ProviderName.FMP, Category.FUNDAMENTAL_DATA, HealthStatus.DOWN, "err2"
        )
        self.assertEqual(health.consecutive_failures, 2)
        self.assertEqual(health.last_error, "err2")


class TestIsUsableCoolDown(unittest.TestCase):
    def test_down_is_unusable_immediately_after_failure(self):
        tracker = HealthTracker(cool_down_seconds=60.0)
        now = datetime(2026, 1, 1, 12, 0, 0)
        tracker.record_failure(
            ProviderName.FMP,
            Category.FUNDAMENTAL_DATA,
            HealthStatus.DOWN,
            "err",
            checked_at=now,
        )
        self.assertFalse(
            tracker.is_usable(ProviderName.FMP, Category.FUNDAMENTAL_DATA, now=now)
        )

    def test_down_becomes_usable_again_after_cool_down_elapses(self):
        tracker = HealthTracker(cool_down_seconds=60.0)
        now = datetime(2026, 1, 1, 12, 0, 0)
        tracker.record_failure(
            ProviderName.FMP,
            Category.FUNDAMENTAL_DATA,
            HealthStatus.DOWN,
            "err",
            checked_at=now,
        )
        later = now + timedelta(seconds=61)
        self.assertTrue(
            tracker.is_usable(ProviderName.FMP, Category.FUNDAMENTAL_DATA, now=later)
        )

    def test_exactly_at_cool_down_boundary_is_usable(self):
        tracker = HealthTracker(cool_down_seconds=60.0)
        now = datetime(2026, 1, 1, 12, 0, 0)
        tracker.record_failure(
            ProviderName.FMP,
            Category.FUNDAMENTAL_DATA,
            HealthStatus.DOWN,
            "err",
            checked_at=now,
        )
        boundary = now + timedelta(seconds=60)
        self.assertTrue(
            tracker.is_usable(ProviderName.FMP, Category.FUNDAMENTAL_DATA, now=boundary)
        )

    def test_rate_limited_and_timeout_follow_the_same_cool_down(self):
        for status in (HealthStatus.RATE_LIMITED, HealthStatus.TIMEOUT):
            tracker = HealthTracker(cool_down_seconds=10.0)
            now = datetime(2026, 1, 1, 12, 0, 0)
            tracker.record_failure(
                ProviderName.FMP, Category.FUNDAMENTAL_DATA, status, "err", checked_at=now
            )
            self.assertFalse(
                tracker.is_usable(ProviderName.FMP, Category.FUNDAMENTAL_DATA, now=now)
            )
            self.assertTrue(
                tracker.is_usable(
                    ProviderName.FMP,
                    Category.FUNDAMENTAL_DATA,
                    now=now + timedelta(seconds=11),
                )
            )


class TestInvalidKeyNeverAutoClears(unittest.TestCase):
    def test_invalid_key_stays_unusable_regardless_of_elapsed_time(self):
        tracker = HealthTracker(cool_down_seconds=1.0, invalid_key_cool_down_seconds=1.0)
        now = datetime(2026, 1, 1, 12, 0, 0)
        tracker.record_failure(
            ProviderName.FMP,
            Category.FUNDAMENTAL_DATA,
            HealthStatus.INVALID_KEY,
            "bad key",
            checked_at=now,
        )
        far_future = now + timedelta(days=365)
        self.assertFalse(
            tracker.is_usable(ProviderName.FMP, Category.FUNDAMENTAL_DATA, now=far_future)
        )

    def test_invalid_key_clears_only_via_a_fresh_recorded_success(self):
        tracker = HealthTracker()
        tracker.record_failure(
            ProviderName.FMP, Category.FUNDAMENTAL_DATA, HealthStatus.INVALID_KEY, "bad key"
        )
        tracker.record_success(ProviderName.FMP, Category.FUNDAMENTAL_DATA, 5.0)
        self.assertTrue(tracker.is_usable(ProviderName.FMP, Category.FUNDAMENTAL_DATA))


class TestIndependentHealthPerCategory(unittest.TestCase):
    def test_finnhub_categories_track_health_independently(self):
        tracker = HealthTracker()
        tracker.record_failure(
            ProviderName.FINNHUB, Category.FUNDAMENTAL_DATA, HealthStatus.DOWN, "err"
        )
        fundamental_health = tracker.get(ProviderName.FINNHUB, Category.FUNDAMENTAL_DATA)
        news_health = tracker.get(ProviderName.FINNHUB, Category.NEWS)
        self.assertEqual(fundamental_health.status, HealthStatus.DOWN)
        self.assertEqual(news_health.status, HealthStatus.UNKNOWN)


if __name__ == "__main__":
    unittest.main()
