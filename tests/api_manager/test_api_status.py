"""Unit tests for research_engine.api_manager.api_status."""

import unittest
from datetime import datetime

from research_engine.api_manager.api_health import HealthStatus, HealthTracker
from research_engine.api_manager.api_logging import APILogEntry, APILogger, CallOutcome
from research_engine.api_manager.api_provider import Category, ProviderName, ProviderRole
from research_engine.api_manager.api_registry import APIRegistry
from research_engine.api_manager.api_status import APIStatus


class TestBeforeAnyCalls(unittest.TestCase):
    def setUp(self):
        self.status = APIStatus(APIRegistry(), HealthTracker(), APILogger())

    def test_primary_and_backup_are_populated_with_the_right_providers(self):
        category_status = self.status.get_category_status(Category.FUNDAMENTAL_DATA)
        self.assertEqual(category_status.primary.provider_name, ProviderName.FMP)
        self.assertEqual(category_status.backup.provider_name, ProviderName.FINNHUB)

    def test_status_is_unknown_and_usage_is_zero_before_any_call(self):
        category_status = self.status.get_category_status(Category.FUNDAMENTAL_DATA)
        self.assertEqual(category_status.primary.status, HealthStatus.UNKNOWN)
        self.assertEqual(category_status.primary.usage_count, 0)
        self.assertIsNone(category_status.primary.success_rate)

    def test_current_provider_in_use_is_none_before_any_call(self):
        category_status = self.status.get_category_status(Category.FUNDAMENTAL_DATA)
        self.assertIsNone(category_status.current_provider_in_use)

    def test_get_all_status_covers_every_category(self):
        all_status = self.status.get_all_status()
        self.assertEqual({s.category for s in all_status}, set(Category))


class TestAfterActivity(unittest.TestCase):
    def test_reflects_health_and_usage_updates(self):
        registry = APIRegistry()
        health_tracker = HealthTracker()
        logger = APILogger()
        status = APIStatus(registry, health_tracker, logger)

        health_tracker.record_success(ProviderName.FMP, Category.FUNDAMENTAL_DATA, 42.0)
        logger.record(
            APILogEntry(
                timestamp=datetime.now(),
                category=Category.FUNDAMENTAL_DATA,
                operation="Company Profile",
                provider_name=ProviderName.FMP,
                role_attempted=ProviderRole.PRIMARY,
                outcome=CallOutcome.SUCCESS,
                health_status=HealthStatus.ONLINE,
                response_time_ms=42.0,
                served_by=ProviderRole.PRIMARY,
            )
        )

        category_status = status.get_category_status(Category.FUNDAMENTAL_DATA)
        self.assertEqual(category_status.primary.status, HealthStatus.ONLINE)
        self.assertEqual(category_status.primary.response_time_ms, 42.0)
        self.assertEqual(category_status.primary.usage_count, 1)
        self.assertEqual(category_status.primary.success_rate, 1.0)
        self.assertEqual(category_status.current_provider_in_use, ProviderRole.PRIMARY)

    def test_disabled_provider_is_reflected_in_active_flag(self):
        registry = APIRegistry()
        registry.set_active(Category.NEWS, ProviderRole.BACKUP, False)
        status = APIStatus(registry, HealthTracker(), APILogger())
        category_status = status.get_category_status(Category.NEWS)
        self.assertFalse(category_status.backup.active)


if __name__ == "__main__":
    unittest.main()
