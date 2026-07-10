"""Unit/integration tests for research_engine.api_manager.api_manager.

Exercises Provider Selection Logic (Section 6) and the five-step
Failover Rules (Section 7) end to end. Finnhub, Twelve Data, and
NewsAPI are still IMP-10B placeholders and are driven with
`simulate_failure` to force deterministic outcomes. FMP
(Claude-Prompts/IMP_10C_FMP_Integration.md) and Alpha Vantage
(Claude-Prompts/IMP_10D_Alpha_Vantage_Integration.md) are now real --
wherever this suite needs one of their real Primary-path plumbing
(auth, request build, response parse) to trivially succeed,
`_mocked_fmp_provider()`/`_mocked_alpha_vantage_provider()` below
replace their `_send_request` seam with a canned, in-memory response.
No network call is made anywhere in this test module either way.
"""

import unittest

from research_engine.api_manager.api_health import HealthStatus
from research_engine.api_manager.api_logging import CallOutcome
from research_engine.api_manager.api_manager import (
    APIManager,
    APIManagerResult,
    InvalidRequestError,
)
from research_engine.api_manager.api_provider import Category, ProviderName, ProviderRole
from research_engine.api_manager.api_registry import APIRegistry
from research_engine.api_manager.provider_interface import (
    ProviderDownError,
    ProviderInvalidKeyError,
    ProviderRateLimitedError,
    ProviderTimeoutError,
)
from research_engine.api_manager.providers import AlphaVantageProvider, FinnhubProvider, FMPProvider


def _mocked_fmp_provider(**overrides) -> FMPProvider:
    """A real FMPProvider whose HTTP layer is replaced with a canned
    success response -- used wherever this suite needs FMP's Primary
    path to trivially succeed without a live network call. Distinct
    from `simulate_failure`, which forces a failure before any request
    logic runs at all."""
    provider = FMPProvider(api_key="test-key", **overrides)
    provider._send_request = lambda url: (  # type: ignore[method-assign]
        200,
        b'{"symbol": "AAPL", "companyName": "Apple Inc."}',
    )
    return provider


def _mocked_alpha_vantage_provider(**overrides) -> AlphaVantageProvider:
    """An AlphaVantageProvider counterpart to _mocked_fmp_provider()."""
    provider = AlphaVantageProvider(api_key="test-key", **overrides)
    provider._send_request = lambda url: (  # type: ignore[method-assign]
        200,
        b'{"Global Quote": {"01. symbol": "AAPL", "05. price": "316.22"}}',
    )
    return provider


class TestSuccessfulPrimaryPath(unittest.TestCase):
    def test_each_category_defaults_to_its_primary_provider(self):
        manager = APIManager()
        manager.adapters[ProviderName.FMP] = _mocked_fmp_provider()
        manager.adapters[ProviderName.ALPHA_VANTAGE] = _mocked_alpha_vantage_provider()
        expectations = {
            Category.FUNDAMENTAL_DATA: (ProviderName.FMP, "Company Profile", {"symbol": "AAPL"}),
            Category.MARKET_TECHNICAL: (
                ProviderName.ALPHA_VANTAGE,
                "Real-time Price",
                {"symbol": "AAPL"},
            ),
            Category.NEWS: (ProviderName.NEWSAPI, "Some Operation", {}),
        }
        for category, (expected_provider, operation, parameters) in expectations.items():
            result = manager.request(category, operation, parameters)
            self.assertIsInstance(result, APIManagerResult)
            self.assertTrue(result.success)
            self.assertEqual(result.served_by, ProviderRole.PRIMARY)
            self.assertEqual(result.provider_name, expected_provider)
            if expected_provider is ProviderName.FMP:
                self.assertEqual(result.data["payload"]["symbol"], "AAPL")
            elif expected_provider is ProviderName.ALPHA_VANTAGE:
                self.assertEqual(result.data["series"]["01. symbol"], "AAPL")
            else:
                self.assertTrue(result.data["placeholder"])

    def test_health_is_online_after_a_successful_call(self):
        manager = APIManager()
        manager.adapters[ProviderName.FMP] = _mocked_fmp_provider()
        manager.request(Category.FUNDAMENTAL_DATA, "Company Profile", {"symbol": "AAPL"})
        health = manager.health_tracker.get(ProviderName.FMP, Category.FUNDAMENTAL_DATA)
        self.assertEqual(health.status, HealthStatus.ONLINE)

    def test_a_successful_primary_call_never_touches_the_backup(self):
        manager = APIManager()
        manager.adapters[ProviderName.FMP] = _mocked_fmp_provider()
        manager.request(Category.FUNDAMENTAL_DATA, "Company Profile", {"symbol": "AAPL"})
        self.assertEqual(
            manager.logger.usage_count(ProviderName.FINNHUB, Category.FUNDAMENTAL_DATA), 0
        )


class TestFailoverRules(unittest.TestCase):
    """The exact five-step sequence: record failure, mark DOWN, call
    Backup, return Backup response, log which provider served."""

    def test_primary_failure_fails_over_to_backup_and_succeeds(self):
        manager = APIManager()
        manager.adapters[ProviderName.FMP] = FMPProvider(
            simulate_failure=ProviderDownError("simulated outage")
        )

        result = manager.request(Category.FUNDAMENTAL_DATA, "Company Profile")

        self.assertTrue(result.success)
        self.assertEqual(result.served_by, ProviderRole.BACKUP)
        self.assertEqual(result.provider_name, ProviderName.FINNHUB)

    def test_step_1_and_2_primary_failure_is_recorded_and_marked(self):
        manager = APIManager()
        manager.adapters[ProviderName.FMP] = FMPProvider(
            simulate_failure=ProviderDownError("simulated outage")
        )
        manager.request(Category.FUNDAMENTAL_DATA, "Company Profile")

        health = manager.health_tracker.get(ProviderName.FMP, Category.FUNDAMENTAL_DATA)
        self.assertEqual(health.status, HealthStatus.DOWN)
        self.assertEqual(health.last_error, "simulated outage")

        primary_entries = manager.logger.entries_for(
            ProviderName.FMP, Category.FUNDAMENTAL_DATA, ProviderRole.PRIMARY
        )
        self.assertEqual(len(primary_entries), 1)
        self.assertEqual(primary_entries[0].outcome, CallOutcome.FAILURE)
        self.assertIsNone(primary_entries[0].served_by)

    def test_step_5_log_records_which_provider_actually_served(self):
        manager = APIManager()
        manager.adapters[ProviderName.FMP] = FMPProvider(
            simulate_failure=ProviderDownError("simulated outage")
        )
        manager.request(Category.FUNDAMENTAL_DATA, "Company Profile")

        self.assertEqual(
            manager.logger.most_recent_served_by(Category.FUNDAMENTAL_DATA), ProviderRole.BACKUP
        )
        backup_entries = manager.logger.entries_for(
            ProviderName.FINNHUB, Category.FUNDAMENTAL_DATA, ProviderRole.BACKUP
        )
        self.assertEqual(len(backup_entries), 1)
        self.assertEqual(backup_entries[0].served_by, ProviderRole.BACKUP)

    def test_error_type_maps_to_the_correct_health_status(self):
        cases = (
            (ProviderDownError("x"), HealthStatus.DOWN),
            (ProviderRateLimitedError("x"), HealthStatus.RATE_LIMITED),
            (ProviderInvalidKeyError("x"), HealthStatus.INVALID_KEY),
            (ProviderTimeoutError("x"), HealthStatus.TIMEOUT),
        )
        for error, expected_status in cases:
            manager = APIManager()
            manager.adapters[ProviderName.FMP] = FMPProvider(simulate_failure=error)
            manager.request(Category.FUNDAMENTAL_DATA, "Company Profile")
            health = manager.health_tracker.get(ProviderName.FMP, Category.FUNDAMENTAL_DATA)
            self.assertEqual(health.status, expected_status)

    def test_both_primary_and_backup_failing_returns_explicit_failure_never_fabricated_data(self):
        manager = APIManager()
        manager.adapters[ProviderName.FMP] = FMPProvider(
            simulate_failure=ProviderDownError("primary down")
        )
        manager.adapters[ProviderName.FINNHUB] = FinnhubProvider(
            simulate_failure=ProviderInvalidKeyError("backup key invalid")
        )

        result = manager.request(Category.FUNDAMENTAL_DATA, "Company Profile")

        self.assertFalse(result.success)
        self.assertIsNone(result.data)
        self.assertIsNone(result.served_by)
        self.assertEqual(result.error, "backup key invalid")

    def test_collector_never_needs_to_know_which_provider_served(self):
        """A Collector's request()/result shape is identical whether
        the Primary or Backup answered -- only `served_by` differs."""
        manager = APIManager()
        primary_result = manager.request(Category.NEWS, "Company News")

        manager2 = APIManager()
        manager2.adapters[ProviderName.NEWSAPI] = manager2.adapters[
            ProviderName.NEWSAPI
        ].__class__(simulate_failure=ProviderDownError("down"))
        backup_result = manager2.request(Category.NEWS, "Company News")

        self.assertEqual(type(primary_result), type(backup_result))
        self.assertTrue(primary_result.success)
        self.assertTrue(backup_result.success)


class TestCoolDownGatesRepeatedAttempts(unittest.TestCase):
    def test_primary_is_skipped_not_re_attempted_while_still_in_cool_down(self):
        manager = APIManager()
        manager.adapters[ProviderName.FMP] = FMPProvider(
            simulate_failure=ProviderDownError("down")
        )

        manager.request(Category.FUNDAMENTAL_DATA, "Company Profile")  # marks FMP DOWN
        manager.request(Category.FUNDAMENTAL_DATA, "Company Profile")  # should skip FMP entirely

        primary_entries = manager.logger.entries_for(
            ProviderName.FMP, Category.FUNDAMENTAL_DATA, ProviderRole.PRIMARY
        )
        self.assertEqual(len(primary_entries), 1)

    def test_primary_is_retried_automatically_once_cool_down_elapses(self):
        manager = APIManager()
        manager.health_tracker.cool_down_seconds = 0.0
        manager.adapters[ProviderName.FMP] = FMPProvider(
            simulate_failure=ProviderDownError("down")
        )

        manager.request(Category.FUNDAMENTAL_DATA, "Company Profile", {"symbol": "AAPL"})
        manager.adapters[ProviderName.FMP] = _mocked_fmp_provider()  # recovers
        result = manager.request(Category.FUNDAMENTAL_DATA, "Company Profile", {"symbol": "AAPL"})

        self.assertTrue(result.success)
        self.assertEqual(result.served_by, ProviderRole.PRIMARY)


class TestInvalidKeyRequiresManualHealthCheck(unittest.TestCase):
    def test_invalid_key_is_never_auto_retried(self):
        manager = APIManager()
        manager.health_tracker.cool_down_seconds = 0.0
        manager.adapters[ProviderName.FMP] = FMPProvider(
            simulate_failure=ProviderInvalidKeyError("bad key")
        )

        manager.request(Category.FUNDAMENTAL_DATA, "Company Profile")
        manager.adapters[ProviderName.FMP] = FMPProvider()  # key "fixed" in adapter terms
        result = manager.request(Category.FUNDAMENTAL_DATA, "Company Profile")

        # Even though the adapter would now succeed, is_usable() still
        # refuses INVALID_KEY without a manual Health Check.
        self.assertEqual(result.served_by, ProviderRole.BACKUP)

    def test_manual_health_check_clears_invalid_key(self):
        manager = APIManager()
        manager.adapters[ProviderName.FMP] = FMPProvider(
            simulate_failure=ProviderInvalidKeyError("bad key")
        )
        manager.request(Category.FUNDAMENTAL_DATA, "Company Profile")

        manager.adapters[ProviderName.FMP] = _mocked_fmp_provider()
        status = manager.health_check(Category.FUNDAMENTAL_DATA, ProviderRole.PRIMARY)

        self.assertEqual(status, HealthStatus.ONLINE)
        result = manager.request(Category.FUNDAMENTAL_DATA, "Company Profile", {"symbol": "AAPL"})
        self.assertEqual(result.served_by, ProviderRole.PRIMARY)

    def test_manual_health_check_logs_an_entry(self):
        manager = APIManager()
        manager.health_check(Category.FUNDAMENTAL_DATA, ProviderRole.PRIMARY)
        entries = manager.logger.entries_for(ProviderName.FMP, Category.FUNDAMENTAL_DATA)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].operation, "HealthCheck")


class TestDisabledProviders(unittest.TestCase):
    def test_disabled_primary_skips_straight_to_backup(self):
        manager = APIManager()
        manager.registry.set_active(Category.FUNDAMENTAL_DATA, ProviderRole.PRIMARY, False)
        result = manager.request(Category.FUNDAMENTAL_DATA, "Company Profile")
        self.assertTrue(result.success)
        self.assertEqual(result.served_by, ProviderRole.BACKUP)

    def test_both_disabled_fails_explicitly(self):
        manager = APIManager()
        manager.registry.set_active(Category.FUNDAMENTAL_DATA, ProviderRole.PRIMARY, False)
        manager.registry.set_active(Category.FUNDAMENTAL_DATA, ProviderRole.BACKUP, False)
        result = manager.request(Category.FUNDAMENTAL_DATA, "Company Profile")
        self.assertFalse(result.success)
        self.assertIn("disabled", result.error)


class TestInputValidation(unittest.TestCase):
    def test_empty_operation_raises(self):
        manager = APIManager()
        with self.assertRaises(InvalidRequestError):
            manager.request(Category.FUNDAMENTAL_DATA, "")

    def test_whitespace_only_operation_raises(self):
        manager = APIManager()
        with self.assertRaises(InvalidRequestError):
            manager.request(Category.FUNDAMENTAL_DATA, "   ")


class TestManualProviderSwitchAffectsSelection(unittest.TestCase):
    def test_swapping_roles_changes_which_provider_is_tried_first(self):
        registry = APIRegistry()
        registry.swap_roles(Category.FUNDAMENTAL_DATA)
        manager = APIManager(registry=registry)

        result = manager.request(Category.FUNDAMENTAL_DATA, "Company Profile")

        self.assertEqual(result.provider_name, ProviderName.FINNHUB)
        self.assertEqual(result.served_by, ProviderRole.PRIMARY)

    def test_health_persists_across_a_role_swap(self):
        registry = APIRegistry()
        manager = APIManager(registry=registry)
        manager.adapters[ProviderName.FMP] = FMPProvider(
            simulate_failure=ProviderDownError("down")
        )
        manager.request(Category.FUNDAMENTAL_DATA, "Company Profile")  # marks FMP DOWN as Primary

        registry.swap_roles(Category.FUNDAMENTAL_DATA)  # FMP is now Backup

        health = manager.health_tracker.get(ProviderName.FMP, Category.FUNDAMENTAL_DATA)
        self.assertEqual(health.status, HealthStatus.DOWN)


if __name__ == "__main__":
    unittest.main()
