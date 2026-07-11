"""Integration tests for the Alpha Vantage Integration (IMP-10D): a
Market & Technical Category Collector talking to a real (HTTP-mocked)
APIManager wired to a real AlphaVantageProvider.

Twelve Data is also real as of IMP-10E
(Claude-Prompts/IMP_10E_Twelve_Data_Integration.md) -- wherever this
suite needs its Backup path to trivially succeed,
`_td_returning()`/`_mocked_twelve_data_provider()` below replace its
`_send_request` seam with a canned, in-memory response, the same
pattern `_av_returning()` uses for Alpha Vantage. Twelve Data's own
dedicated real-behavior coverage lives in
test_twelve_data_api_manager_integration.py, not here.

Every HTTP interaction is mocked at each provider's `_send_request` --
no test in this module ever performs a live internet call, per
Claude-Prompts/IMP_10D_Alpha_Vantage_Integration.md's Testing
requirement.
"""

import ast
import pathlib
import unittest

from research_engine.api_manager import (
    APIManager,
    APIRegistry,
    Category,
    HealthStatus,
    ProviderName,
    ProviderRole,
)
from research_engine.api_manager.provider_interface import (
    ProviderDownError,
    ProviderInvalidKeyError,
    ProviderRateLimitedError,
    ProviderTimeoutError,
)
from research_engine.api_manager.providers.alpha_vantage_provider import AlphaVantageProvider
from research_engine.api_manager.providers.twelve_data_provider import TwelveDataProvider
from research_engine.collectors.historical_price.historical_price_collector import (
    HistoricalPriceCollector,
)
from research_engine.collectors.technical_analysis.technical_analysis_collector import (
    TechnicalAnalysisCollector,
)

MARKET_TECHNICAL_COLLECTOR_CLASSES = (HistoricalPriceCollector, TechnicalAnalysisCollector)


def _av_returning(payload_json: bytes) -> AlphaVantageProvider:
    provider = AlphaVantageProvider(api_key="test-key")
    provider._send_request = lambda url: (200, payload_json)  # type: ignore[method-assign]
    return provider


def _mocked_twelve_data_provider(**overrides) -> TwelveDataProvider:
    """A real TwelveDataProvider whose HTTP layer is replaced with a
    canned success response -- used wherever this suite needs Twelve
    Data's Backup path to trivially succeed without a live network
    call."""
    provider = TwelveDataProvider(api_key="test-key", **overrides)
    provider._send_request = lambda url: (  # type: ignore[method-assign]
        200,
        b'{"price": "1.0"}',
    )
    return provider


_DAILY_PAYLOAD = (
    b'{"Meta Data": {"2. Symbol": "INFY"}, "Time Series (Daily)": {'
    b'"2026-07-09": {"1. open": "1500.0", "2. high": "1520.0", "3. low": "1490.0", '
    b'"4. close": "1510.0", "5. volume": "100000"},'
    b'"2026-07-08": {"1. open": "1480.0", "2. high": "1505.0", "3. low": "1470.0", '
    b'"4. close": "1500.0", "5. volume": "90000"}'
    b"}}"
)

_RSI_PAYLOAD = (
    b'{"Meta Data": {}, "Technical Analysis: RSI": {'
    b'"2026-07-09": {"RSI": "63.8614"}, "2026-07-08": {"RSI": "62.2477"}'
    b"}}"
)


class TestBackupProviderIsCorrectlyIdentified(unittest.TestCase):
    """Per IMP-10D's Backup Provider rule: verify the API Manager
    correctly identifies Twelve Data as the configured Backup Provider
    -- Twelve Data itself is never implemented in this phase."""

    def test_twelve_data_is_the_registered_backup_for_market_technical(self):
        registry = APIRegistry()
        backup = registry.get_backup(Category.MARKET_TECHNICAL)
        self.assertEqual(backup.provider_name, ProviderName.TWELVE_DATA)
        self.assertEqual(backup.role, ProviderRole.BACKUP)

    def test_alpha_vantage_is_the_registered_primary_for_market_technical(self):
        registry = APIRegistry()
        primary = registry.get_primary(Category.MARKET_TECHNICAL)
        self.assertEqual(primary.provider_name, ProviderName.ALPHA_VANTAGE)
        self.assertEqual(primary.role, ProviderRole.PRIMARY)

    def test_twelve_data_is_never_actually_called_when_alpha_vantage_succeeds(self):
        manager = APIManager()
        manager.adapters[ProviderName.ALPHA_VANTAGE] = _av_returning(_DAILY_PAYLOAD)
        collector = HistoricalPriceCollector(api_manager=manager)
        collector.collect("INFY")
        self.assertEqual(
            manager.logger.usage_count(ProviderName.TWELVE_DATA, Category.MARKET_TECHNICAL), 0
        )


class TestEachCollectorReachesAlphaVantageThroughAPIManager(unittest.TestCase):
    """End to end: Collector.collect() -> APIManager.request() ->
    AlphaVantageProvider.call() (HTTP mocked) -> back up through
    APIManager to the Collector's Result."""

    def test_historical_price_collector_succeeds_through_a_real_api_manager(self):
        manager = APIManager()
        manager.adapters[ProviderName.ALPHA_VANTAGE] = _av_returning(_DAILY_PAYLOAD)
        result = HistoricalPriceCollector(api_manager=manager).collect("INFY")

        self.assertEqual(result.collector_status.value, "Success")
        self.assertEqual(len(result.sources), 1)
        self.assertIn("Alpha Vantage", result.sources[0])
        self.assertIn("Primary", result.sources[0])

    def test_technical_analysis_collector_succeeds_through_a_real_api_manager(self):
        manager = APIManager()
        manager.adapters[ProviderName.ALPHA_VANTAGE] = _av_returning(_RSI_PAYLOAD)
        result = TechnicalAnalysisCollector(api_manager=manager).collect("INFY")

        self.assertEqual(result.collector_status.value, "Success")
        self.assertEqual(len(result.sources), 1)
        self.assertIn("Alpha Vantage", result.sources[0])
        self.assertIn("Primary", result.sources[0])

    def test_api_manager_actually_recorded_the_attempt(self):
        manager = APIManager()
        manager.adapters[ProviderName.ALPHA_VANTAGE] = _av_returning(_DAILY_PAYLOAD)
        HistoricalPriceCollector(api_manager=manager).collect("INFY")

        entries = manager.logger.entries_for(ProviderName.ALPHA_VANTAGE, Category.MARKET_TECHNICAL)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].collector_name, "Historical Price Collector")

    def test_without_an_api_manager_every_collector_still_returns_placeholder_success(self):
        """Backward compatibility: omitting api_manager entirely (the
        default) must behave exactly as every prior IMP-08 phase."""
        for collector_class in MARKET_TECHNICAL_COLLECTOR_CLASSES:
            collector = collector_class()
            result = collector.collect("Sample Manufacturing Ltd (SMFG, NSE)")
            self.assertEqual(result.collector_status.value, "Success")
            self.assertIn("(placeholder)", result.sources[0])


class TestDataMapsOntoResearchEngineModels(unittest.TestCase):
    """IMP-10D's checklist: real Alpha Vantage data must map onto the
    existing Result dataclasses' typed fields, including chart_dataset
    / chart_data, not just flow through as an opaque success flag."""

    def test_daily_ohlc_maps_onto_historical_price_result(self):
        manager = APIManager()
        manager.adapters[ProviderName.ALPHA_VANTAGE] = _av_returning(_DAILY_PAYLOAD)
        result = HistoricalPriceCollector(api_manager=manager).collect("INFY")

        self.assertEqual(result.symbol, "INFY")
        self.assertEqual(len(result.ohlc_records), 2)
        self.assertEqual(result.total_trading_days, 2)
        newest = result.ohlc_records[-1]
        self.assertEqual(newest.close, 1510.0)
        self.assertEqual(newest.volume, 100_000)
        # Chart Dataset rebuilt from the same real records.
        self.assertEqual(result.chart_dataset.labels, ["2026-07-08", "2026-07-09"])
        self.assertEqual(result.chart_dataset.close_values, [1500.0, 1510.0])

    def test_rsi_maps_onto_technical_analysis_result(self):
        manager = APIManager()
        manager.adapters[ProviderName.ALPHA_VANTAGE] = _av_returning(_RSI_PAYLOAD)
        result = TechnicalAnalysisCollector(api_manager=manager).collect("INFY")

        self.assertAlmostEqual(result.rsi, 63.8614)
        self.assertEqual(result.chart_data.indicator_labels, ["2026-07-08", "2026-07-09"])
        self.assertAlmostEqual(result.chart_data.indicator_values[-1], 63.8614)
        self.assertEqual(result.indicators_available, ["RSI"])

    def test_backup_twelve_data_response_never_triggers_alpha_vantage_field_mapping(self):
        manager = APIManager()
        manager.adapters[ProviderName.ALPHA_VANTAGE] = AlphaVantageProvider(
            simulate_failure=ProviderDownError("simulated Alpha Vantage outage")
        )
        manager.adapters[ProviderName.TWELVE_DATA] = _mocked_twelve_data_provider()
        result = HistoricalPriceCollector(api_manager=manager).collect(
            "Sample Manufacturing Ltd (SMFG, NSE)"
        )

        self.assertEqual(result.collector_status.value, "Success")
        self.assertEqual(result.symbol, "SMFG")  # placeholder, untouched
        self.assertIn("Twelve Data", result.sources[0])


class TestInvalidSymbolHandling(unittest.TestCase):
    """Alpha Vantage succeeds (HTTP 200) but returns an empty series
    for a symbol it has no data for -- confirmed live during IMP-10D
    validation."""

    def test_empty_series_reports_collector_failed(self):
        manager = APIManager()
        manager.adapters[ProviderName.ALPHA_VANTAGE] = _av_returning(
            b'{"Meta Data": {}, "Time Series (Daily)": {}}'
        )
        result = HistoricalPriceCollector(api_manager=manager).collect("NOSUCHSYMBOL")

        self.assertEqual(result.collector_status.value, "Failed")
        self.assertEqual(result.sources, [])

    def test_empty_series_never_triggers_failover(self):
        """An empty series is not itself a provider failure -- Alpha
        Vantage's own call genuinely succeeded (HTTP 200, just no data
        for this symbol)."""
        manager = APIManager()
        manager.adapters[ProviderName.ALPHA_VANTAGE] = _av_returning(
            b'{"Meta Data": {}, "Time Series (Daily)": {}}'
        )
        HistoricalPriceCollector(api_manager=manager).collect("NOSUCHSYMBOL")
        self.assertEqual(
            manager.logger.usage_count(ProviderName.TWELVE_DATA, Category.MARKET_TECHNICAL), 0
        )


class TestMockedFailureModesAtTheCollectorLevel(unittest.TestCase):
    """Invalid API key, Timeout, and Rate Limit handling, mocked only,
    verified end to end from a Collector's perspective."""

    def test_invalid_api_key_fails_over_and_collector_still_succeeds(self):
        manager = APIManager()
        manager.adapters[ProviderName.ALPHA_VANTAGE] = AlphaVantageProvider(
            simulate_failure=ProviderInvalidKeyError("simulated invalid key")
        )
        manager.adapters[ProviderName.TWELVE_DATA] = _mocked_twelve_data_provider()
        result = TechnicalAnalysisCollector(api_manager=manager).collect("AAPL")

        self.assertEqual(result.collector_status.value, "Success")
        self.assertIn("Twelve Data", result.sources[0])
        health = manager.health_tracker.get(ProviderName.ALPHA_VANTAGE, Category.MARKET_TECHNICAL)
        self.assertEqual(health.status, HealthStatus.INVALID_KEY)

    def test_timeout_fails_over_and_collector_still_succeeds(self):
        manager = APIManager()
        manager.adapters[ProviderName.ALPHA_VANTAGE] = AlphaVantageProvider(
            simulate_failure=ProviderTimeoutError("simulated timeout")
        )
        manager.adapters[ProviderName.TWELVE_DATA] = _mocked_twelve_data_provider()
        result = TechnicalAnalysisCollector(api_manager=manager).collect("AAPL")

        self.assertEqual(result.collector_status.value, "Success")
        health = manager.health_tracker.get(ProviderName.ALPHA_VANTAGE, Category.MARKET_TECHNICAL)
        self.assertEqual(health.status, HealthStatus.TIMEOUT)

    def test_rate_limit_fails_over_and_collector_still_succeeds(self):
        manager = APIManager()
        manager.adapters[ProviderName.ALPHA_VANTAGE] = AlphaVantageProvider(
            simulate_failure=ProviderRateLimitedError("simulated rate limit")
        )
        manager.adapters[ProviderName.TWELVE_DATA] = _mocked_twelve_data_provider()
        result = TechnicalAnalysisCollector(api_manager=manager).collect("AAPL")

        self.assertEqual(result.collector_status.value, "Success")
        health = manager.health_tracker.get(ProviderName.ALPHA_VANTAGE, Category.MARKET_TECHNICAL)
        self.assertEqual(health.status, HealthStatus.RATE_LIMITED)


class TestOtherCategoriesUntouched(unittest.TestCase):
    """Only Market & Technical collectors were updated in IMP-10D/10E;
    Fundamental Data is byte-identical to before this phase. News
    (Market News Collector) gained its own api_manager parameter in a
    later phase, IMP-10F -- see test_newsapi_api_manager_integration.py
    for its dedicated coverage, not here."""

    def test_company_collector_unaffected(self):
        from research_engine.collectors.company.company_collector import CompanyCollector

        collector = CompanyCollector()
        self.assertTrue(hasattr(collector, "api_manager"))  # updated in IMP-10C, not this phase


class TestCollectorsNeverImportAlphaVantageOrNetworkDirectly(unittest.TestCase):
    """AST-based structural proof, mirroring
    test_fmp_api_manager_integration.py's equivalent -- every updated
    Market & Technical collector's only new dependency is
    `research_engine.api_manager` (via a relative import), never
    alpha_vantage_provider, urllib, http, or socket directly."""

    UPDATED_COLLECTOR_FILES = (
        ("historical_price", "historical_price_collector.py"),
        ("technical_analysis", "technical_analysis_collector.py"),
    )

    FORBIDDEN_SUBSTRINGS = (
        "alpha_vantage_provider",
        "AlphaVantageProvider",
        "import urllib",
        "import socket",
        "import http",
        "import requests",
    )

    def _collectors_dir(self) -> pathlib.Path:
        return pathlib.Path(__file__).resolve().parents[2] / "research_engine" / "collectors"

    def test_no_forbidden_substring_appears_in_any_updated_collector(self):
        for package, filename in self.UPDATED_COLLECTOR_FILES:
            path = self._collectors_dir() / package / filename
            source = path.read_text(encoding="utf-8")
            for forbidden in self.FORBIDDEN_SUBSTRINGS:
                self.assertNotIn(forbidden, source, f"{path}: found forbidden '{forbidden}'")

    def test_only_relative_imports_reach_outside_the_collector_s_own_package(self):
        allowed_stdlib = {"dataclasses", "datetime", "enum", "typing", "__future__"}
        for package, filename in self.UPDATED_COLLECTOR_FILES:
            path = self._collectors_dir() / package / filename
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.level == 0:
                    self.assertIn(
                        node.module,
                        allowed_stdlib,
                        f"{path}: unexpected absolute import '{node.module}'",
                    )
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        top = alias.name.split(".")[0]
                        self.assertIn(
                            top, allowed_stdlib, f"{path}: unexpected import '{alias.name}'"
                        )

    def test_relative_api_manager_import_resolves_to_the_package_not_a_submodule(self):
        allowed_names = {"APIManager", "Category", "ProviderName"}
        for package, filename in self.UPDATED_COLLECTOR_FILES:
            path = self._collectors_dir() / package / filename
            tree = ast.parse(path.read_text(encoding="utf-8"))
            relative_imports = [
                node
                for node in ast.walk(tree)
                if isinstance(node, ast.ImportFrom) and node.level > 0
            ]
            api_manager_imports = [
                node for node in relative_imports if node.module == "api_manager"
            ]
            self.assertEqual(
                len(api_manager_imports),
                1,
                f"{path}: expected exactly one `from ...api_manager import ...`",
            )
            imported_names = {alias.name for alias in api_manager_imports[0].names}
            self.assertTrue(
                {"APIManager", "Category"}.issubset(imported_names),
                f"{path}: missing required APIManager/Category import",
            )
            self.assertTrue(
                imported_names.issubset(allowed_names),
                f"{path}: unexpected api_manager import(s) {imported_names - allowed_names}",
            )


if __name__ == "__main__":
    unittest.main()
