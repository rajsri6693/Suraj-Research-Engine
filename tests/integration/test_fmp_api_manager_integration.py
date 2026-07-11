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
    """VERIFY items 3-5, as of IMP-10C: only Fundamental Data collectors
    were updated by *this* phase.

    historical_price, technical_analysis, and market_news are
    deliberately NOT asserted parameter-free here any more -- IMP-10D
    (Claude-Prompts/IMP_10D_Alpha_Vantage_Integration.md) wires an
    api_manager parameter into the first two, and IMP-10F
    (Claude-Prompts/IMP_10F_NewsAPI_Integration.md) wires one into
    market_news, since each is exactly the collector its own phase is
    scoped to update. Their own dedicated coverage lives in
    test_alpha_vantage_api_manager_integration.py and
    test_newsapi_api_manager_integration.py, respectively."""


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
        """Every updated collector imports from the api_manager
        package's public surface (3 dots + api_manager), never reaching
        into a submodule like `...api_manager.providers.fmp_provider`.
        APIManager and Category are always required; ProviderName is
        permitted (only Company and Financial collectors use it, to
        recognize when a live FMP record is available to map) -- no
        other name may be imported this way."""
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


def _fmp_returning(payload_json: bytes) -> FMPProvider:
    provider = FMPProvider(api_key="test-key")
    provider._send_request = lambda url: (200, payload_json)  # type: ignore[method-assign]
    return provider


class TestDataMapsOntoResearchEngineModels(unittest.TestCase):
    """IMP-10C's checklist item 10: real FMP data must map onto the
    existing Result dataclasses' typed fields, not just flow through
    as an opaque success flag."""

    def test_company_profile_maps_onto_company_result(self):
        manager = APIManager()
        manager.adapters[ProviderName.FMP] = _fmp_returning(
            b'[{"symbol": "INFY", "companyName": "Infosys Limited", '
            b'"sector": "Technology", "industry": "Information Technology Services", '
            b'"isin": "US4567881085", "website": "https://www.infosys.com", '
            b'"description": "Infosys Limited provides consulting services.", '
            b'"city": "Bangalore", "state": "Karnataka", "country": "IN", '
            b'"exchange": "NSE", "price": 18.5}]'
        )
        collector = CompanyCollector(api_manager=manager)

        result = collector.collect("INFY")

        self.assertEqual(result.collector_status.value, "Success")
        self.assertEqual(result.company_name, "Infosys Limited")
        self.assertEqual(result.sector, "Technology")
        self.assertEqual(result.industry, "Information Technology Services")
        self.assertEqual(result.isin, "US4567881085")
        self.assertEqual(result.official_website, "https://www.infosys.com")
        self.assertEqual(
            result.business_description, "Infosys Limited provides consulting services."
        )
        self.assertEqual(result.headquarters, "Bangalore, Karnataka, IN")
        self.assertEqual(result.nse_symbol, "INFY")
        # founded_year is deliberately NOT overwritten -- FMP has no
        # founding-year field, only IPO date, and substituting one for
        # the other would be a data-integrity error.
        self.assertEqual(result.founded_year, 1998)

    def test_financial_statements_maps_onto_financial_result(self):
        manager = APIManager()
        manager.adapters[ProviderName.FMP] = _fmp_returning(
            b'[{"symbol": "AAPL", "revenue": 416161000000, "netIncome": 112010000000, '
            b'"eps": 7.02, "fiscalYear": "2025"}]'
        )
        collector = FinancialCollector(api_manager=manager)

        result = collector.collect("AAPL")

        self.assertEqual(result.collector_status.value, "Success")
        self.assertEqual(result.revenue, 416161000000.0)
        self.assertEqual(result.net_profit, 112010000000.0)
        self.assertEqual(result.eps, 7.02)
        self.assertEqual(result.financial_year, "FY2025")
        # Fields FMP's income-statement does not carry (book_value,
        # pe_ratio, roe, roce, debt_to_equity, market_capitalization,
        # dividend_yield) are left at their placeholder values, per
        # this module's docstring -- never fabricated.
        self.assertEqual(result.pe_ratio, 21.6)

    def test_backup_finnhub_response_never_triggers_fmp_field_mapping(self):
        """When Finnhub (still a placeholder) serves the request, its
        differently-shaped response must never be misinterpreted as an
        FMP payload."""
        manager = APIManager()
        manager.adapters[ProviderName.FMP] = FMPProvider(
            simulate_failure=ProviderDownError("simulated FMP outage")
        )
        collector = CompanyCollector(api_manager=manager)

        result = collector.collect("Sample Manufacturing Ltd (SMFG, NSE)")

        self.assertEqual(result.collector_status.value, "Success")
        self.assertEqual(result.company_name, "Sample Manufacturing Ltd")  # placeholder, untouched
        self.assertIn("Finnhub", result.sources[0])


class TestInvalidSymbolHandling(unittest.TestCase):
    """FMP succeeds (HTTP 200) but returns an empty payload for a
    symbol it has no coverage for -- confirmed live against the real
    API for several NSE symbols during IMP-10C validation."""

    def test_empty_fmp_payload_reports_collector_failed(self):
        manager = APIManager()
        manager.adapters[ProviderName.FMP] = _fmp_returning(b"[]")
        collector = CompanyCollector(api_manager=manager)

        result = collector.collect("NOSUCHSYMBOL")

        self.assertEqual(result.collector_status.value, "Failed")
        self.assertEqual(result.sources, [])

    def test_empty_fmp_payload_still_fails_over_correctly_if_backup_also_empty(self):
        """An empty FMP payload is not itself a provider failure -- it
        never triggers Failover to Finnhub, since FMP's own call
        genuinely succeeded (HTTP 200, just no data for this symbol)."""
        manager = APIManager()
        manager.adapters[ProviderName.FMP] = _fmp_returning(b"[]")
        collector = CompanyCollector(api_manager=manager)

        collector.collect("NOSUCHSYMBOL")

        self.assertEqual(
            manager.logger.usage_count(ProviderName.FINNHUB, Category.FUNDAMENTAL_DATA), 0
        )


class TestMockedFailureModesAtTheCollectorLevel(unittest.TestCase):
    """Invalid API key, Timeout, and Rate Limit handling, mocked only
    (per IMP-10C's Testing requirement), verified end to end from a
    Collector's perspective, not just FMPProvider's."""

    def test_invalid_api_key_fails_over_and_collector_still_succeeds(self):
        from research_engine.api_manager.provider_interface import ProviderInvalidKeyError

        manager = APIManager()
        manager.adapters[ProviderName.FMP] = FMPProvider(
            simulate_failure=ProviderInvalidKeyError("simulated invalid key")
        )
        collector = FinancialCollector(api_manager=manager)

        result = collector.collect("AAPL")

        self.assertEqual(result.collector_status.value, "Success")
        self.assertIn("Finnhub", result.sources[0])
        health = manager.health_tracker.get(ProviderName.FMP, Category.FUNDAMENTAL_DATA)
        from research_engine.api_manager import HealthStatus

        self.assertEqual(health.status, HealthStatus.INVALID_KEY)

    def test_timeout_fails_over_and_collector_still_succeeds(self):
        from research_engine.api_manager.provider_interface import ProviderTimeoutError

        manager = APIManager()
        manager.adapters[ProviderName.FMP] = FMPProvider(
            simulate_failure=ProviderTimeoutError("simulated timeout")
        )
        collector = FinancialCollector(api_manager=manager)

        result = collector.collect("AAPL")

        self.assertEqual(result.collector_status.value, "Success")
        health = manager.health_tracker.get(ProviderName.FMP, Category.FUNDAMENTAL_DATA)
        from research_engine.api_manager import HealthStatus

        self.assertEqual(health.status, HealthStatus.TIMEOUT)

    def test_rate_limit_fails_over_and_collector_still_succeeds(self):
        from research_engine.api_manager.provider_interface import ProviderRateLimitedError

        manager = APIManager()
        manager.adapters[ProviderName.FMP] = FMPProvider(
            simulate_failure=ProviderRateLimitedError("simulated rate limit")
        )
        collector = FinancialCollector(api_manager=manager)

        result = collector.collect("AAPL")

        self.assertEqual(result.collector_status.value, "Success")
        health = manager.health_tracker.get(ProviderName.FMP, Category.FUNDAMENTAL_DATA)
        from research_engine.api_manager import HealthStatus

        self.assertEqual(health.status, HealthStatus.RATE_LIMITED)

    def test_both_fmp_and_finnhub_failing_all_four_modes(self):
        """Belt-and-suspenders: whichever way FMP fails, if Finnhub
        also fails, the Collector reports Failed -- never fabricated
        data, regardless of which of the four failure modes hit FMP."""
        from research_engine.api_manager import HealthStatus
        from research_engine.api_manager.provider_interface import (
            ProviderInvalidKeyError,
            ProviderRateLimitedError,
            ProviderTimeoutError,
        )
        from research_engine.api_manager.providers import FinnhubProvider

        for fmp_error in (
            ProviderDownError("down"),
            ProviderInvalidKeyError("bad key"),
            ProviderRateLimitedError("rate limited"),
            ProviderTimeoutError("timed out"),
        ):
            manager = APIManager()
            manager.adapters[ProviderName.FMP] = FMPProvider(simulate_failure=fmp_error)
            manager.adapters[ProviderName.FINNHUB] = FinnhubProvider(
                simulate_failure=ProviderDownError("backup also down")
            )
            collector = FinancialCollector(api_manager=manager)

            result = collector.collect("AAPL")

            self.assertEqual(result.collector_status.value, "Failed")
            self.assertEqual(result.sources, [])


if __name__ == "__main__":
    unittest.main()
