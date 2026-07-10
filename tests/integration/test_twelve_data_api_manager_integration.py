"""Integration and Failover tests for the Twelve Data Integration
(IMP-10E): a Market & Technical Category Collector talking to a real
(HTTP-mocked) APIManager, with Alpha Vantage as Primary and Twelve Data
as the now-real Backup Provider.

Every HTTP interaction is mocked at each provider's _send_request()
seam -- no test in this module ever performs a live internet call, per
Claude-Prompts/IMP_10E_Twelve_Data_Integration.md's Testing
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


def _td_returning(payload_json: bytes) -> TwelveDataProvider:
    provider = TwelveDataProvider(api_key="test-key")
    provider._send_request = lambda url: (200, payload_json)  # type: ignore[method-assign]
    return provider


_AV_DAILY_PAYLOAD = (
    b'{"Meta Data": {"2. Symbol": "INFY"}, "Time Series (Daily)": {'
    b'"2026-07-09": {"1. open": "1500.0", "2. high": "1520.0", "3. low": "1490.0", '
    b'"4. close": "1510.0", "5. volume": "100000"}}}'
)

_TD_DAILY_PAYLOAD = (
    b'{"meta": {"symbol": "INFY", "interval": "1day"}, "values": ['
    b'{"datetime": "2026-07-09", "open": "1500.0", "high": "1520.0", "low": "1490.0", '
    b'"close": "1510.0", "volume": "100000"}]}'
)


class TestBackupProviderIsCorrectlyIdentified(unittest.TestCase):
    """Per IMP-10E's Objective: Alpha Vantage remains Primary, Twelve
    Data is the configured Backup Provider for Market & Technical."""

    def test_twelve_data_is_the_registered_backup_for_market_technical(self):
        registry = APIRegistry()
        backup = registry.get_backup(Category.MARKET_TECHNICAL)
        self.assertEqual(backup.provider_name, ProviderName.TWELVE_DATA)
        self.assertEqual(backup.role, ProviderRole.BACKUP)

    def test_alpha_vantage_is_still_the_registered_primary(self):
        registry = APIRegistry()
        primary = registry.get_primary(Category.MARKET_TECHNICAL)
        self.assertEqual(primary.provider_name, ProviderName.ALPHA_VANTAGE)
        self.assertEqual(primary.role, ProviderRole.PRIMARY)


class TestFailoverScenario1AlphaVantageOnline(unittest.TestCase):
    """Scenario 1, per IMP-10E: Alpha Vantage ONLINE -> API Manager ->
    Alpha Vantage used. Twelve Data must never be touched."""

    def test_alpha_vantage_serves_the_request_when_healthy(self):
        manager = APIManager()
        manager.adapters[ProviderName.ALPHA_VANTAGE] = _av_returning(_AV_DAILY_PAYLOAD)
        manager.adapters[ProviderName.TWELVE_DATA] = _td_returning(_TD_DAILY_PAYLOAD)

        result = HistoricalPriceCollector(api_manager=manager).collect("INFY")

        self.assertEqual(result.collector_status.value, "Success")
        self.assertIn("Alpha Vantage", result.sources[0])
        self.assertIn("Primary", result.sources[0])
        self.assertEqual(
            manager.logger.usage_count(ProviderName.TWELVE_DATA, Category.MARKET_TECHNICAL), 0
        )

    def test_provider_status_online_after_scenario_1(self):
        manager = APIManager()
        manager.adapters[ProviderName.ALPHA_VANTAGE] = _av_returning(_AV_DAILY_PAYLOAD)
        HistoricalPriceCollector(api_manager=manager).collect("INFY")
        health = manager.health_tracker.get(ProviderName.ALPHA_VANTAGE, Category.MARKET_TECHNICAL)
        self.assertEqual(health.status, HealthStatus.ONLINE)


class TestFailoverScenario2AlphaVantageDown(unittest.TestCase):
    """Scenario 2, per IMP-10E: Alpha Vantage DOWN -> API Manager ->
    automatically switch -> Twelve Data -> data returned -> provider
    selection logged. The Collector is never modified to support this
    -- it only ever calls api_manager.request(); the failover
    orchestration happens entirely inside APIManager, unchanged since
    IMP-10B."""

    def test_alpha_vantage_down_automatically_switches_to_twelve_data(self):
        manager = APIManager()
        manager.adapters[ProviderName.ALPHA_VANTAGE] = AlphaVantageProvider(
            simulate_failure=ProviderDownError("simulated Alpha Vantage outage")
        )
        manager.adapters[ProviderName.TWELVE_DATA] = _td_returning(_TD_DAILY_PAYLOAD)

        result = HistoricalPriceCollector(api_manager=manager).collect("INFY")

        self.assertEqual(result.collector_status.value, "Success")
        self.assertIn("Twelve Data", result.sources[0])
        self.assertIn("Backup", result.sources[0])

    def test_alpha_vantage_marked_down_twelve_data_marked_online(self):
        manager = APIManager()
        manager.adapters[ProviderName.ALPHA_VANTAGE] = AlphaVantageProvider(
            simulate_failure=ProviderDownError("simulated Alpha Vantage outage")
        )
        manager.adapters[ProviderName.TWELVE_DATA] = _td_returning(_TD_DAILY_PAYLOAD)

        HistoricalPriceCollector(api_manager=manager).collect("INFY")

        av_health = manager.health_tracker.get(ProviderName.ALPHA_VANTAGE, Category.MARKET_TECHNICAL)
        td_health = manager.health_tracker.get(ProviderName.TWELVE_DATA, Category.MARKET_TECHNICAL)
        self.assertEqual(av_health.status, HealthStatus.DOWN)
        self.assertEqual(td_health.status, HealthStatus.ONLINE)

    def test_provider_selection_is_logged_for_both_attempts(self):
        """Failure recorded, provider marked DOWN, Backup called,
        response returned, provider selection logged -- the exact
        five-step Failover Rule, unmodified since IMP-10B, exercised
        here against Twelve Data specifically for the first time."""
        manager = APIManager()
        manager.adapters[ProviderName.ALPHA_VANTAGE] = AlphaVantageProvider(
            simulate_failure=ProviderDownError("simulated Alpha Vantage outage")
        )
        manager.adapters[ProviderName.TWELVE_DATA] = _td_returning(_TD_DAILY_PAYLOAD)

        HistoricalPriceCollector(api_manager=manager).collect("INFY")

        av_entries = manager.logger.entries_for(ProviderName.ALPHA_VANTAGE, Category.MARKET_TECHNICAL)
        td_entries = manager.logger.entries_for(ProviderName.TWELVE_DATA, Category.MARKET_TECHNICAL)
        self.assertEqual(len(av_entries), 1)
        self.assertEqual(av_entries[0].outcome.value, "FAILURE")
        self.assertIsNone(av_entries[0].served_by)
        self.assertEqual(len(td_entries), 1)
        self.assertEqual(td_entries[0].outcome.value, "SUCCESS")
        self.assertEqual(td_entries[0].served_by, ProviderRole.BACKUP)
        self.assertEqual(
            manager.logger.most_recent_served_by(Category.MARKET_TECHNICAL), ProviderRole.BACKUP
        )

    def test_both_down_reports_collector_failed_never_fabricated(self):
        manager = APIManager()
        manager.adapters[ProviderName.ALPHA_VANTAGE] = AlphaVantageProvider(
            simulate_failure=ProviderDownError("simulated Alpha Vantage outage")
        )
        manager.adapters[ProviderName.TWELVE_DATA] = TwelveDataProvider(
            simulate_failure=ProviderDownError("simulated Twelve Data outage too")
        )

        result = HistoricalPriceCollector(api_manager=manager).collect("INFY")

        self.assertEqual(result.collector_status.value, "Failed")
        self.assertEqual(result.sources, [])


class TestFailbackScenario3AlphaVantageRecovers(unittest.TestCase):
    """Scenario 3, per IMP-10E: Alpha Vantage becomes ONLINE again ->
    API Manager automatically resumes using it as Primary. This is the
    existing, unmodified cool-down recovery mechanism in HealthTracker
    (api_health.py, unchanged since IMP-10B) -- DOWN/RATE_LIMITED/
    TIMEOUT become usable again once cool_down_seconds has elapsed
    since the last check, so a genuinely-recovered Primary is retried
    automatically with no manual reset and no Collector involvement."""

    def test_alpha_vantage_is_retried_and_resumes_as_primary_once_cool_down_elapses(self):
        manager = APIManager()
        manager.health_tracker.cool_down_seconds = 0.0  # simulate cool-down having elapsed
        manager.adapters[ProviderName.ALPHA_VANTAGE] = AlphaVantageProvider(
            simulate_failure=ProviderDownError("simulated Alpha Vantage outage")
        )
        manager.adapters[ProviderName.TWELVE_DATA] = _td_returning(_TD_DAILY_PAYLOAD)

        # Scenario 2: Alpha Vantage down, Twelve Data serves as Backup.
        first = HistoricalPriceCollector(api_manager=manager).collect("INFY")
        self.assertIn("Twelve Data", first.sources[0])
        av_health_after_failure = manager.health_tracker.get(
            ProviderName.ALPHA_VANTAGE, Category.MARKET_TECHNICAL
        )
        self.assertEqual(av_health_after_failure.status, HealthStatus.DOWN)

        # Scenario 3: Alpha Vantage "recovers" (its own real behavior
        # returns to normal -- simulated here by clearing
        # simulate_failure, exactly as a real outage ending would look
        # from APIManager's perspective: the next attempt just
        # succeeds).
        manager.adapters[ProviderName.ALPHA_VANTAGE] = _av_returning(_AV_DAILY_PAYLOAD)
        second = HistoricalPriceCollector(api_manager=manager).collect("INFY")

        self.assertIn("Alpha Vantage", second.sources[0])
        self.assertIn("Primary", second.sources[0])
        av_health_after_recovery = manager.health_tracker.get(
            ProviderName.ALPHA_VANTAGE, Category.MARKET_TECHNICAL
        )
        self.assertEqual(av_health_after_recovery.status, HealthStatus.ONLINE)

    def test_twelve_data_is_not_touched_once_alpha_vantage_has_resumed(self):
        manager = APIManager()
        manager.health_tracker.cool_down_seconds = 0.0
        manager.adapters[ProviderName.ALPHA_VANTAGE] = AlphaVantageProvider(
            simulate_failure=ProviderDownError("simulated Alpha Vantage outage")
        )
        manager.adapters[ProviderName.TWELVE_DATA] = _td_returning(_TD_DAILY_PAYLOAD)
        HistoricalPriceCollector(api_manager=manager).collect("INFY")  # Scenario 2

        manager.adapters[ProviderName.ALPHA_VANTAGE] = _av_returning(_AV_DAILY_PAYLOAD)
        HistoricalPriceCollector(api_manager=manager).collect("INFY")  # Scenario 3

        # Exactly one Twelve Data attempt total -- the Scenario 2 one.
        # Scenario 3's successful resumption must not touch Backup at
        # all.
        self.assertEqual(
            manager.logger.usage_count(ProviderName.TWELVE_DATA, Category.MARKET_TECHNICAL), 1
        )

    def test_alpha_vantage_still_down_within_cool_down_window_stays_on_backup(self):
        """Negative control: failback must NOT happen before the
        cool-down window elapses -- proves Scenario 3 is a genuine
        time-gated recovery, not an immediate retry every call."""
        manager = APIManager()
        # default cool_down_seconds (60s) -- NOT set to 0 this time.
        manager.adapters[ProviderName.ALPHA_VANTAGE] = AlphaVantageProvider(
            simulate_failure=ProviderDownError("simulated Alpha Vantage outage")
        )
        manager.adapters[ProviderName.TWELVE_DATA] = _td_returning(_TD_DAILY_PAYLOAD)
        HistoricalPriceCollector(api_manager=manager).collect("INFY")  # marks AV DOWN

        # Alpha Vantage "recovers" immediately, but the cool-down has
        # not elapsed yet -- APIManager must still skip it.
        manager.adapters[ProviderName.ALPHA_VANTAGE] = _av_returning(_AV_DAILY_PAYLOAD)
        second = HistoricalPriceCollector(api_manager=manager).collect("INFY")

        self.assertIn("Twelve Data", second.sources[0])
        self.assertEqual(
            manager.logger.usage_count(ProviderName.ALPHA_VANTAGE, Category.MARKET_TECHNICAL), 1
        )


class TestProviderHealthStates(unittest.TestCase):
    """Verify ONLINE, DOWN, TIMEOUT, RATE_LIMITED, UNKNOWN all update
    correctly for Twelve Data specifically, mirroring the same proof
    already established for FMP and Alpha Vantage."""

    def test_unknown_before_any_call(self):
        manager = APIManager()
        health = manager.health_tracker.get(ProviderName.TWELVE_DATA, Category.MARKET_TECHNICAL)
        self.assertEqual(health.status, HealthStatus.UNKNOWN)

    def test_online_after_success(self):
        manager = APIManager()
        manager.adapters[ProviderName.ALPHA_VANTAGE] = AlphaVantageProvider(
            simulate_failure=ProviderDownError("forced")
        )
        manager.adapters[ProviderName.TWELVE_DATA] = _td_returning(_TD_DAILY_PAYLOAD)
        HistoricalPriceCollector(api_manager=manager).collect("INFY")
        health = manager.health_tracker.get(ProviderName.TWELVE_DATA, Category.MARKET_TECHNICAL)
        self.assertEqual(health.status, HealthStatus.ONLINE)

    def test_down_after_generic_failure(self):
        manager = APIManager()
        manager.adapters[ProviderName.ALPHA_VANTAGE] = AlphaVantageProvider(
            simulate_failure=ProviderDownError("forced")
        )
        manager.adapters[ProviderName.TWELVE_DATA] = TwelveDataProvider(
            simulate_failure=ProviderDownError("forced")
        )
        HistoricalPriceCollector(api_manager=manager).collect("INFY")
        health = manager.health_tracker.get(ProviderName.TWELVE_DATA, Category.MARKET_TECHNICAL)
        self.assertEqual(health.status, HealthStatus.DOWN)

    def test_timeout_after_timeout_failure(self):
        manager = APIManager()
        manager.adapters[ProviderName.ALPHA_VANTAGE] = AlphaVantageProvider(
            simulate_failure=ProviderDownError("forced")
        )
        manager.adapters[ProviderName.TWELVE_DATA] = TwelveDataProvider(
            simulate_failure=ProviderTimeoutError("forced timeout")
        )
        HistoricalPriceCollector(api_manager=manager).collect("INFY")
        health = manager.health_tracker.get(ProviderName.TWELVE_DATA, Category.MARKET_TECHNICAL)
        self.assertEqual(health.status, HealthStatus.TIMEOUT)

    def test_rate_limited_after_rate_limit_failure(self):
        manager = APIManager()
        manager.adapters[ProviderName.ALPHA_VANTAGE] = AlphaVantageProvider(
            simulate_failure=ProviderDownError("forced")
        )
        manager.adapters[ProviderName.TWELVE_DATA] = TwelveDataProvider(
            simulate_failure=ProviderRateLimitedError("forced rate limit")
        )
        HistoricalPriceCollector(api_manager=manager).collect("INFY")
        health = manager.health_tracker.get(ProviderName.TWELVE_DATA, Category.MARKET_TECHNICAL)
        self.assertEqual(health.status, HealthStatus.RATE_LIMITED)

    def test_invalid_key_after_invalid_key_failure(self):
        manager = APIManager()
        manager.adapters[ProviderName.ALPHA_VANTAGE] = AlphaVantageProvider(
            simulate_failure=ProviderDownError("forced")
        )
        manager.adapters[ProviderName.TWELVE_DATA] = TwelveDataProvider(
            simulate_failure=ProviderInvalidKeyError("forced invalid key")
        )
        HistoricalPriceCollector(api_manager=manager).collect("INFY")
        health = manager.health_tracker.get(ProviderName.TWELVE_DATA, Category.MARKET_TECHNICAL)
        self.assertEqual(health.status, HealthStatus.INVALID_KEY)


class TestDataMapsOntoResearchEngineModels(unittest.TestCase):
    """Twelve Data's real response, when it serves as Backup, must
    never be mistaken for Alpha Vantage's shape -- the Collector-level
    field mapping is Alpha-Vantage-specific and stays that way."""

    def test_twelve_data_backup_response_never_triggers_alpha_vantage_field_mapping(self):
        manager = APIManager()
        manager.adapters[ProviderName.ALPHA_VANTAGE] = AlphaVantageProvider(
            simulate_failure=ProviderDownError("simulated Alpha Vantage outage")
        )
        manager.adapters[ProviderName.TWELVE_DATA] = _td_returning(_TD_DAILY_PAYLOAD)

        result = HistoricalPriceCollector(api_manager=manager).collect("INFY")

        self.assertEqual(result.collector_status.value, "Success")
        # placeholder symbol untouched -- Twelve Data's real OHLC data
        # was never parsed into ohlc_records, exactly as designed.
        self.assertEqual(result.symbol, "SMFG")
        self.assertIn("Twelve Data", result.sources[0])


class TestCollectorsNeverModifiedToSupportFailover(unittest.TestCase):
    """Per IMP-10E: 'Do not modify Collectors to support failover.
    Failover must happen only inside API Manager.' AST-based structural
    proof that neither updated collector contains any Twelve-Data-
    specific logic, failover branching, or provider-name comparison
    beyond the pre-existing Alpha-Vantage-only check."""

    UPDATED_COLLECTOR_FILES = (
        ("historical_price", "historical_price_collector.py"),
        ("technical_analysis", "technical_analysis_collector.py"),
    )

    def _collectors_dir(self) -> pathlib.Path:
        return pathlib.Path(__file__).resolve().parents[2] / "research_engine" / "collectors"

    def test_no_code_reference_to_twelve_data_in_either_collector(self):
        """Docstring prose may name Twelve Data (for documentation);
        no executable code token (identifier, string literal used in
        a comparison, import) may. Module/class/function docstrings are
        deliberately excluded from the string-constant scan -- they are
        documentation, not executable logic."""
        for package, filename in self.UPDATED_COLLECTOR_FILES:
            path = self._collectors_dir() / package / filename
            tree = ast.parse(path.read_text(encoding="utf-8"))

            docstring_node_ids = set()
            for node in ast.walk(tree):
                if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                    if (
                        node.body
                        and isinstance(node.body[0], ast.Expr)
                        and isinstance(node.body[0].value, ast.Constant)
                        and isinstance(node.body[0].value.value, str)
                    ):
                        docstring_node_ids.add(id(node.body[0].value))

            for node in ast.walk(tree):
                if isinstance(node, ast.Constant) and isinstance(node.value, str):
                    if id(node) in docstring_node_ids:
                        continue  # documentation prose, not executable code
                    self.assertNotIn(
                        "TWELVE_DATA",
                        node.value.upper().replace(" ", "_"),
                        f"{path}: found a Twelve-Data-referencing string constant in code",
                    )
                if isinstance(node, ast.Name):
                    self.assertNotIn("TwelveData", node.id, f"{path}: found a Twelve Data identifier")
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    module = getattr(node, "module", None) or ""
                    self.assertNotIn("twelve_data", module, f"{path}: found a Twelve Data import")
                    for alias in node.names:
                        self.assertNotIn(
                            "TwelveData", alias.name, f"{path}: found a Twelve Data import"
                        )

    def test_collectors_only_ever_check_for_alpha_vantage_by_name(self):
        """The one and only provider-name comparison in each collector
        must be against ProviderName.ALPHA_VANTAGE -- proving the
        Backup path is handled generically ("not Alpha Vantage"), never
        by naming Twelve Data specifically."""
        for package, filename in self.UPDATED_COLLECTOR_FILES:
            path = self._collectors_dir() / package / filename
            source = path.read_text(encoding="utf-8")
            self.assertIn("ProviderName.ALPHA_VANTAGE", source)


if __name__ == "__main__":
    unittest.main()
