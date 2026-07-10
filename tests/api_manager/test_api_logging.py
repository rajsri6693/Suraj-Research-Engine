"""Unit tests for research_engine.api_manager.api_logging."""

import unittest
from datetime import datetime

from research_engine.api_manager.api_health import HealthStatus
from research_engine.api_manager.api_logging import APILogEntry, APILogger, CallOutcome
from research_engine.api_manager.api_provider import Category, ProviderName, ProviderRole


def _entry(
    provider_name=ProviderName.FMP,
    category=Category.FUNDAMENTAL_DATA,
    role=ProviderRole.PRIMARY,
    outcome=CallOutcome.SUCCESS,
    served_by=None,
) -> APILogEntry:
    return APILogEntry(
        timestamp=datetime.now(),
        category=category,
        operation="Company Profile",
        provider_name=provider_name,
        role_attempted=role,
        outcome=outcome,
        health_status=HealthStatus.ONLINE if outcome == CallOutcome.SUCCESS else HealthStatus.DOWN,
        served_by=served_by,
        error=None if outcome == CallOutcome.SUCCESS else "boom",
    )


class TestRecordAndEntries(unittest.TestCase):
    def test_starts_empty(self):
        logger = APILogger()
        self.assertEqual(logger.entries(), [])

    def test_record_appends_never_overwrites(self):
        logger = APILogger()
        logger.record(_entry())
        logger.record(_entry())
        self.assertEqual(len(logger.entries()), 2)

    def test_entries_returns_a_copy_not_the_internal_list(self):
        logger = APILogger()
        logger.record(_entry())
        snapshot = logger.entries()
        snapshot.append(_entry())
        self.assertEqual(len(logger.entries()), 1)


class TestUsageAndSuccessCounts(unittest.TestCase):
    def test_usage_count_filters_by_provider_and_category(self):
        logger = APILogger()
        logger.record(_entry(provider_name=ProviderName.FMP, category=Category.FUNDAMENTAL_DATA))
        logger.record(_entry(provider_name=ProviderName.FMP, category=Category.FUNDAMENTAL_DATA))
        logger.record(_entry(provider_name=ProviderName.FINNHUB, category=Category.FUNDAMENTAL_DATA))
        self.assertEqual(
            logger.usage_count(ProviderName.FMP, Category.FUNDAMENTAL_DATA), 2
        )
        self.assertEqual(
            logger.usage_count(ProviderName.FINNHUB, Category.FUNDAMENTAL_DATA), 1
        )

    def test_usage_count_can_filter_by_role_too(self):
        logger = APILogger()
        logger.record(_entry(role=ProviderRole.PRIMARY))
        logger.record(_entry(role=ProviderRole.BACKUP))
        self.assertEqual(
            logger.usage_count(ProviderName.FMP, Category.FUNDAMENTAL_DATA, ProviderRole.PRIMARY),
            1,
        )

    def test_success_rate_is_none_when_never_called(self):
        logger = APILogger()
        self.assertIsNone(
            logger.success_rate(ProviderName.FMP, Category.FUNDAMENTAL_DATA)
        )

    def test_success_rate_computed_correctly(self):
        logger = APILogger()
        logger.record(_entry(outcome=CallOutcome.SUCCESS, served_by=ProviderRole.PRIMARY))
        logger.record(_entry(outcome=CallOutcome.FAILURE))
        logger.record(_entry(outcome=CallOutcome.FAILURE))
        logger.record(_entry(outcome=CallOutcome.FAILURE))
        self.assertEqual(
            logger.success_rate(ProviderName.FMP, Category.FUNDAMENTAL_DATA), 0.25
        )

    def test_zero_percent_success_is_distinct_from_never_called(self):
        logger = APILogger()
        logger.record(_entry(outcome=CallOutcome.FAILURE))
        self.assertEqual(
            logger.success_rate(ProviderName.FMP, Category.FUNDAMENTAL_DATA), 0.0
        )


class TestMostRecentServedBy(unittest.TestCase):
    def test_none_when_nothing_ever_succeeded(self):
        logger = APILogger()
        logger.record(_entry(outcome=CallOutcome.FAILURE))
        self.assertIsNone(logger.most_recent_served_by(Category.FUNDAMENTAL_DATA))

    def test_returns_the_role_of_the_most_recent_success(self):
        logger = APILogger()
        logger.record(
            _entry(
                role=ProviderRole.PRIMARY,
                outcome=CallOutcome.SUCCESS,
                served_by=ProviderRole.PRIMARY,
            )
        )
        logger.record(
            _entry(
                provider_name=ProviderName.FINNHUB,
                role=ProviderRole.BACKUP,
                outcome=CallOutcome.SUCCESS,
                served_by=ProviderRole.BACKUP,
            )
        )
        self.assertEqual(
            logger.most_recent_served_by(Category.FUNDAMENTAL_DATA), ProviderRole.BACKUP
        )

    def test_a_failed_attempt_after_a_success_does_not_change_current_provider(self):
        logger = APILogger()
        logger.record(
            _entry(outcome=CallOutcome.SUCCESS, served_by=ProviderRole.PRIMARY)
        )
        logger.record(_entry(outcome=CallOutcome.FAILURE))
        self.assertEqual(
            logger.most_recent_served_by(Category.FUNDAMENTAL_DATA), ProviderRole.PRIMARY
        )

    def test_scoped_per_category(self):
        logger = APILogger()
        logger.record(
            _entry(
                category=Category.NEWS,
                outcome=CallOutcome.SUCCESS,
                served_by=ProviderRole.PRIMARY,
            )
        )
        self.assertIsNone(logger.most_recent_served_by(Category.FUNDAMENTAL_DATA))


class TestLastError(unittest.TestCase):
    def test_returns_the_most_recent_failure_message(self):
        logger = APILogger()
        entry = _entry(outcome=CallOutcome.FAILURE)
        entry.error = "first failure"
        logger.record(entry)
        entry2 = _entry(outcome=CallOutcome.FAILURE)
        entry2.error = "second failure"
        logger.record(entry2)
        self.assertEqual(
            logger.last_error(ProviderName.FMP, Category.FUNDAMENTAL_DATA, ProviderRole.PRIMARY),
            "second failure",
        )

    def test_none_when_no_failure_recorded(self):
        logger = APILogger()
        logger.record(_entry(outcome=CallOutcome.SUCCESS, served_by=ProviderRole.PRIMARY))
        self.assertIsNone(
            logger.last_error(ProviderName.FMP, Category.FUNDAMENTAL_DATA, ProviderRole.PRIMARY)
        )


if __name__ == "__main__":
    unittest.main()
