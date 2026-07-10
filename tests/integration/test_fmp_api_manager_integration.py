"""Integration tests for the FMP Integration (IMP-10C): a Fundamental
Data Category Collector talking to a real (HTTP-mocked) APIManager
wired to a real FMPProvider, with Finnhub as its configured, untouched
placeholder Backup.

Every HTTP interaction is mocked at FMPProvider._send_request() -- no
test in this module ever performs a live internet call, per
Claude-Prompts/IMP_10C_FMP_Integration.md's Testing requirement.
"""

import ast
import pathlib
import unittest

from research_engine.api_manager import (
    APIManager,
    APIRegistry,
    Category,
    ProviderName,
    ProviderRole,
)
from research_engine.api_manager.provider_interface import ProviderDownError
from research_engine.api_manager.providers.fmp_provider import FMPProvider
from research_engine.collectors.company.company_collector import CompanyCollector
from research_engine.collectors.company.company_result import CollectorStatus
from research_engine.collectors.competitors.competitors_collector import CompetitorsCollector
from research_engine.collectors.corporate_actions.corporate_action_collector import (
    CorporateActionCollector,
)
from research_engine.collectors.financial.financial_collector import FinancialCollector
from research_engine.collectors.management.management_collector import ManagementCollector
from research_engine.collectors.orders_contracts.orders_contracts_collector import (
    OrdersContractsCollector,
)
from research_engine.collectors.products_services.products_services_collector import (
    ProductsServicesCollector,
)
from research_engine.collectors.shareholding.shareholding_collector import ShareholdingCollector

FUNDAMENTAL_DATA_COLLECTOR_CLASSES = (
    CompanyCollector,
    FinancialCollector,
    ManagementCollector,
    ShareholdingCollector,
    CompetitorsCollector,
    ProductsServicesCollector,
    CorporateActionCollector,
    OrdersContractsCollector,
)


def _mocked_fmp_manager(**overrides) -> APIManager:
    """A real APIManager wired to a real FMPProvider whose HTTP layer
    is a canned in-memory response -- Finnhub, Alpha Vantage, Twelve
    Data, and NewsAPI stay exactly the IMP-10B placeholders they
    already were. No network call is ever made."""
    manager = APIManager()
    fmp = FMPProvider(api_key="test-key")
    fmp._send_request = lambda url: (  # type: ignore[method-assign]
        200,
        b'[{"symbol": "AAPL", "companyName": "Apple Inc."}]',
    )
    manager.adapters[ProviderName.FMP] = fmp
    for key, value in overrides.items():
        setattr(manager, key, value)
    return manager


class TestBackupProviderIsCorrectlyIdentified(unittest.TestCase):
    """Per IMP-10C's Backup rule: 'Do NOT call Finnhub. Only verify
    that the API Manager correctly identifies Finnhub as the
    configured Backup Provider.'"""

    def test_finnhub_is_the_registered_backup_for_fundamental_data(self):
        registry = APIRegistry()
        backup = registry.get_backup(Category.FUNDAMENTAL_DATA)
        self.assertEqual(backup.provider_name, ProviderName.FINNHUB)
        self.assertEqual(backup.role, ProviderRole.BACKUP)

    def test_fmp_is_the_registered_primary_for_fundamental_data(self):
        registry = APIRegistry()
        primary = registry.get_primary(Category.FUNDAMENTAL_DATA)
        self.assertEqual(primary.provider_name, ProviderName.FMP)
        self.assertEqual(primary.role, ProviderRole.PRIMARY)

    def test_finnhub_is_never_actually_called_when_fmp_succeeds(self):
        manager = _mocked_fmp_manager()
        collector = FinancialCollector(api_manager=manager)
        collector.collect("Quarterly results for Sample Manufacturing Ltd")
        self.assertEqual(
            manager.logger.usage_count(ProviderName.FINNHUB, Category.FUNDAMENTAL_DATA), 0
        )


class TestEachCollectorReachesFMPThroughAPIManager(unittest.TestCase):
    """End to end: Collector.collect() -> APIManager.request() ->
    FMPProvider.call() (HTTP mocked) -> back up through APIManager to
    the Collector's Result -- for every Fundamental Data collector."""

    def test_every_fundamental_collector_succeeds_through_a_real_api_manager(self):
        # Each collector's *_result.py defines its own local
        # CollectorStatus Enum, per RESEARCH_COLLECTORS.md's
        # self-contained-result-module convention -- comparing by
        # `.value` (not enum identity) is required to check this
        # generically across different collector classes.
        for collector_class in FUNDAMENTAL_DATA_COLLECTOR_CLASSES:
            manager = _mocked_fmp_manager()
            collector = collector_class(api_manager=manager)
            result = collector.collect("Sample Manufacturing Ltd (SMFG, NSE)")

            self.assertEqual(
                result.collector_status.value,
                "Success",
                f"{collector_class.__name__} did not report Success",
            )
            self.assertEqual(len(result.sources), 1)
            self.assertIn("Financial Modeling Prep (FMP)", result.sources[0])
            self.assertIn("Primary", result.sources[0])

    def test_api_manager_actually_recorded_the_attempt(self):
        manager = _mocked_fmp_manager()
        collector = CompanyCollector(api_manager=manager)
        collector.collect("Sample Manufacturing Ltd (SMFG, NSE)")

        entries = manager.logger.entries_for(ProviderName.FMP, Category.FUNDAMENTAL_DATA)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].collector_name, "Company Information Collector")

    def test_without_an_api_manager_every_collector_still_returns_placeholder_success(self):
        """Backward compatibility: omitting api_manager entirely (the
        default) must behave exactly as every prior IMP-08 phase."""
        for collector_class in FUNDAMENTAL_DATA_COLLECTOR_CLASSES:
            collector = collector_class()
            result = collector.collect("Sample Manufacturing Ltd (SMFG, NSE)")
            self.assertEqual(result.collector_status.value, "Success")
            self.assertIn("(placeholder)", result.sources[0])


class TestFailoverFromRealFMPToPlaceholderFinnhub(unittest.TestCase):
    """FMP fails (mocked) -> APIManager's unchanged Failover Rules
    (Section 7) call the still-placeholder Finnhub Backup -- proving
    the real/placeholder boundary composes correctly through the
    unmodified API Manager."""

    def test_fmp_failure_fails_over_to_finnhub_and_collector_still_succeeds(self):
        manager = APIManager()
        manager.adapters[ProviderName.FMP] = FMPProvider(
            simulate_failure=ProviderDownError("simulated FMP outage")
        )
        collector = CompanyCollector(api_manager=manager)

        result = collector.collect("Sample Manufacturing Ltd (SMFG, NSE)")

        self.assertEqual(result.collector_status, CollectorStatus.SUCCESS)
        self.assertIn("Finnhub", result.sources[0])
        self.assertIn("Backup", result.sources[0])

    def test_fmp_and_finnhub_both_failing_reports_collector_failed(self):
        from research_engine.api_manager.provider_interface import ProviderInvalidKeyError
        from research_engine.api_manager.providers import FinnhubProvider

        manager = APIManager()
        manager.adapters[ProviderName.FMP] = FMPProvider(
            simulate_failure=ProviderDownError("simulated FMP outage")
        )
        manager.adapters[ProviderName.FINNHUB] = FinnhubProvider(
            simulate_failure=ProviderInvalidKeyError("simulated Finnhub key issue")
        )
        collector = CompanyCollector(api_manager=manager)

        result = collector.collect("Sample Manufacturing Ltd (SMFG, NSE)")

        self.assertEqual(result.collector_status, CollectorStatus.FAILED)
        self.assertEqual(result.sources, [])


class TestOtherCategoriesUntouched(unittest.TestCase):
    """VERIFY items 3-5: only Fundamental Data collectors were
    updated; Market & Technical and News collectors are byte-identical
    to before this phase and have no APIManager wiring at all."""

    def test_historical_price_collector_has_no_api_manager_parameter(self):
        from research_engine.collectors.historical_price.historical_price_collector import (
            HistoricalPriceCollector,
        )

        collector = HistoricalPriceCollector()
        self.assertFalse(hasattr(collector, "api_manager"))

    def test_technical_analysis_collector_has_no_api_manager_parameter(self):
        from research_engine.collectors.technical_analysis.technical_analysis_collector import (
            TechnicalAnalysisCollector,
        )

        collector = TechnicalAnalysisCollector()
        self.assertFalse(hasattr(collector, "api_manager"))

    def test_market_news_collector_has_no_api_manager_parameter(self):
        from research_engine.collectors.market_news.market_news_collector import (
            MarketNewsCollector,
        )

        collector = MarketNewsCollector()
        self.assertFalse(hasattr(collector, "api_manager"))


class TestCollectorsNeverImportFMPOrNetworkDirectly(unittest.TestCase):
    """AST-based structural proof, mirroring
    tests/collectors/financial/test_financial_collector.py's
    TestNoForeignDependencies -- every updated Fundamental Data
    collector's only new dependency is `research_engine.api_manager`
    (via a relative import), never fmp_provider, urllib, http, or
    socket directly."""

    UPDATED_COLLECTOR_FILES = (
        ("company", "company_collector.py"),
        ("financial", "financial_collector.py"),
        ("management", "management_collector.py"),
        ("shareholding", "shareholding_collector.py"),
        ("competitors", "competitors_collector.py"),
        ("products_services", "products_services_collector.py"),
        ("corporate_actions", "corporate_action_collector.py"),
        ("orders_contracts", "orders_contracts_collector.py"),
    )

    FORBIDDEN_SUBSTRINGS = (
        "fmp_provider",
        "FMPProvider",
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
        """Every absolute (non-relative) import in an updated collector
        must be standard library -- the only way to reach APIManager is
        the relative `from ...api_manager import APIManager, Category`,
        never an absolute import of a provider module."""
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
        """Every updated collector imports APIManager and Category
        directly from the api_manager package's public surface (3 dots
        + api_manager), never reaching into a submodule like
        `...api_manager.providers.fmp_provider`."""
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
            self.assertEqual(imported_names, {"APIManager", "Category"})


if __name__ == "__main__":
    unittest.main()
