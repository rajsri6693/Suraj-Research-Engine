"""Unit/integration tests for research_engine.api_manager.api_manager.

Exercises Provider Selection Logic (Section 6) and the five-step
Failover Rules (Section 7) end to end. All five providers are now real,
live-HTTP adapters -- FMP (Claude-Prompts/IMP_10C_FMP_Integration.md),
Alpha Vantage (Claude-Prompts/IMP_10D_Alpha_Vantage_Integration.md),
Twelve Data (Claude-Prompts/IMP_10E_Twelve_Data_Integration.md),
NewsAPI (Claude-Prompts/IMP_10F_NewsAPI_Integration.md), and Finnhub
(Claude-Prompts/IMP_10G_Finnhub_Integration.md). Wherever this suite
needs one of their real Primary-*or*-Backup-path plumbing (auth,
request build, response parse) to trivially succeed,
`_mocked_fmp_provider()`/`_mocked_alpha_vantage_provider()`/
`_mocked_newsapi_provider()`/`_mocked_finnhub_provider()` below replace
their `_send_request` seam with a canned, in-memory response. This
matters even for tests that only assert on the Primary's own health/log
entries -- APIManager's Failover Rules still actually call the Backup
adapter as a side effect of `request()`, so Finnhub must be mocked
every time a test drives FMP or NewsAPI into failing/being skipped, not
only when the test's own assertions inspect Finnhub's result. No
network call is made anywhere in this test module either way.
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
from research_engine.api_manager.providers.newsapi_provider import NewsAPIProvider


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


def _mocked_newsapi_provider(**overrides) -> NewsAPIProvider:
    """A NewsAPIProvider counterpart to _mocked_fmp_provider()."""
    provider = NewsAPIProvider(api_key="test-key", **overrides)
    provider._send_request = lambda url: (  # type: ignore[method-assign]
        200,
        b'{"status": "ok", "totalResults": 1, "articles": '
        b'[{"source": {"name": "Reuters"}, "title": "Apple unveils new product",'
        b' "url": "https://example.com/apple", "publishedAt": "2026-07-10T09:00:00Z"}]}',
    )
    return provider


def _mocked_finnhub_provider(**overrides) -> FinnhubProvider:
    """A FinnhubProvider counterpart to _mocked_fmp_provider() -- used
    every time this suite drives a Primary into failing/being skipped
    for Fundamental Data or News, since APIManager's Failover Rules
    then actually call Finnhub as Backup (or, after a role swap, as
    Primary) as a real side effect of request(), not only when a
    test's own assertions inspect its result."""
    provider = FinnhubProvider(api_key="test-key", **overrides)
    provider._send_request = lambda url: (  # type: ignore[method-assign]
        200,
        b'{"ticker": "AAPL", "name": "Apple Inc"}',
    )
    return provider


class TestSuccessfulPrimaryPath(unittest.TestCase):
    def test_each_category_defaults_to_its_primary_provider(self):
        manager = APIManager()
        manager.adapters[ProviderName.FMP] = _mocked_fmp_provider()
        manager.adapters[ProviderName.ALPHA_VANTAGE] = _mocked_alpha_vantage_provider()
        manager.adapters[ProviderName.NEWSAPI] = _mocked_newsapi_provider()
        expectations = {
            Category.FUNDAMENTAL_DATA: (ProviderName.FMP, "Company Profile", {"symbol": "AAPL"}),
            Category.MARKET_TECHNICAL: (
                ProviderName.ALPHA_VANTAGE,
                "Real-time Price",
                {"symbol": "AAPL"},
            ),
            Category.NEWS: (ProviderName.NEWSAPI, "Company News", {"query": "AAPL"}),
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
                self.assertEqual(result.data["articles"][0]["title"], "Apple unveils new product")

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
        manager.adapters[ProviderName.FINNHUB] = _mocked_finnhub_provider()

        result = manager.request(Category.FUNDAMENTAL_DATA, "Company Profile", {"symbol": "AAPL"})

        self.assertTrue(result.success)
        self.assertEqual(result.served_by, ProviderRole.BACKUP)
        self.assertEqual(result.provider_name, ProviderName.FINNHUB)

    def test_step_1_and_2_primary_failure_is_recorded_and_marked(self):
        manager = APIManager()
        manager.adapters[ProviderName.FMP] = FMPProvider(
            simulate_failure=ProviderDownError("simulated outage")
        )
        manager.adapters[ProviderName.FINNHUB] = _mocked_finnhub_provider()
        manager.request(Category.FUNDAMENTAL_DATA, "Company Profile", {"symbol": "AAPL"})

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
        manager.adapters[ProviderName.FINNHUB] = _mocked_finnhub_provider()
        manager.request(Category.FUNDAMENTAL_DATA, "Company Profile", {"symbol": "AAPL"})

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
            manager.adapters[ProviderName.FINNHUB] = _mocked_finnhub_provider()
            manager.request(Category.FUNDAMENTAL_DATA, "Company Profile", {"symbol": "AAPL"})
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
        manager.adapters[ProviderName.NEWSAPI] = _mocked_newsapi_provider()
        primary_result = manager.request(Category.NEWS, "Company News", {"query": "AAPL"})

        manager2 = APIManager()
        manager2.adapters[ProviderName.NEWSAPI] = NewsAPIProvider(
            simulate_failure=ProviderDownError("down")
        )
        manager2.adapters[ProviderName.FINNHUB] = _mocked_finnhub_provider()
        backup_result = manager2.request(Category.NEWS, "Company News", {"query": "AAPL"})

        self.assertEqual(type(primary_result), type(backup_result))
        self.assertTrue(primary_result.success)
        self.assertTrue(backup_result.success)


class TestCoolDownGatesRepeatedAttempts(unittest.TestCase):
    def test_primary_is_skipped_not_re_attempted_while_still_in_cool_down(self):
        manager = APIManager()
        manager.adapters[ProviderName.FMP] = FMPProvider(
            simulate_failure=ProviderDownError("down")
        )
        manager.adapters[ProviderName.FINNHUB] = _mocked_finnhub_provider()

        # marks FMP DOWN
        manager.request(Category.FUNDAMENTAL_DATA, "Company Profile", {"symbol": "AAPL"})
        # should skip FMP entirely
        manager.request(Category.FUNDAMENTAL_DATA, "Company Profile", {"symbol": "AAPL"})

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
        manager.adapters[ProviderName.FINNHUB] = _mocked_finnhub_provider()

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
        manager.adapters[ProviderName.FINNHUB] = _mocked_finnhub_provider()

        manager.request(Category.FUNDAMENTAL_DATA, "Company Profile", {"symbol": "AAPL"})
        manager.adapters[ProviderName.FMP] = FMPProvider()  # key "fixed" in adapter terms
        result = manager.request(Category.FUNDAMENTAL_DATA, "Company Profile", {"symbol": "AAPL"})

        # Even though the adapter would now succeed, is_usable() still
        # refuses INVALID_KEY without a manual Health Check.
        self.assertEqual(result.served_by, ProviderRole.BACKUP)

    def test_manual_health_check_clears_invalid_key(self):
        manager = APIManager()
        manager.adapters[ProviderName.FMP] = FMPProvider(
            simulate_failure=ProviderInvalidKeyError("bad key")
        )
        manager.adapters[ProviderName.FINNHUB] = _mocked_finnhub_provider()
        manager.request(Category.FUNDAMENTAL_DATA, "Company Profile", {"symbol": "AAPL"})

        manager.adapters[ProviderName.FMP] = _mocked_fmp_provider()
        status = manager.health_check(Category.FUNDAMENTAL_DATA, ProviderRole.PRIMARY)

        self.assertEqual(status, HealthStatus.ONLINE)
        result = manager.request(Category.FUNDAMENTAL_DATA, "Company Profile", {"symbol": "AAPL"})
        self.assertEqual(result.served_by, ProviderRole.PRIMARY)

    def test_manual_health_check_logs_an_entry(self):
        manager = APIManager()
        manager.adapters[ProviderName.FMP] = _mocked_fmp_provider()
        manager.health_check(Category.FUNDAMENTAL_DATA, ProviderRole.PRIMARY)
        entries = manager.logger.entries_for(ProviderName.FMP, Category.FUNDAMENTAL_DATA)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].operation, "HealthCheck")


class TestDisabledProviders(unittest.TestCase):
    def test_disabled_primary_skips_straight_to_backup(self):
        manager = APIManager()
        manager.adapters[ProviderName.FINNHUB] = _mocked_finnhub_provider()
        manager.registry.set_active(Category.FUNDAMENTAL_DATA, ProviderRole.PRIMARY, False)
        result = manager.request(Category.FUNDAMENTAL_DATA, "Company Profile", {"symbol": "AAPL"})
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
        manager.adapters[ProviderName.FINNHUB] = _mocked_finnhub_provider()

        result = manager.request(Category.FUNDAMENTAL_DATA, "Company Profile", {"symbol": "AAPL"})

        self.assertEqual(result.provider_name, ProviderName.FINNHUB)
        self.assertEqual(result.served_by, ProviderRole.PRIMARY)

    def test_health_persists_across_a_role_swap(self):
        registry = APIRegistry()
        manager = APIManager(registry=registry)
        manager.adapters[ProviderName.FMP] = FMPProvider(
            simulate_failure=ProviderDownError("down")
        )
        manager.adapters[ProviderName.FINNHUB] = _mocked_finnhub_provider()
        # marks FMP DOWN as Primary
        manager.request(Category.FUNDAMENTAL_DATA, "Company Profile", {"symbol": "AAPL"})

        registry.swap_roles(Category.FUNDAMENTAL_DATA)  # FMP is now Backup

        health = manager.health_tracker.get(ProviderName.FMP, Category.FUNDAMENTAL_DATA)
        self.assertEqual(health.status, HealthStatus.DOWN)


if __name__ == "__main__":
    unittest.main()
