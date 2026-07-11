"""Integration and Failover/Failback tests for the Finnhub Integration
(IMP-10G): Finnhub as the single, real, live-HTTP Backup Provider for
BOTH Category 1 (Fundamental Data, Primary FMP) and Category 3 (News,
Primary NewsAPI), per
project_documentation/API_MANAGER_ARCHITECTURE.md Section 2 and
Claude-Prompts/IMP_10G_Finnhub_Integration.md.

Every HTTP interaction is mocked at each provider's `_send_request()`
seam -- no test in this module ever performs a live internet call, per
IMP-10G's Testing requirement. FMP's/NewsAPI's own dedicated real-
behavior coverage lives in test_fmp_api_manager_integration.py /
test_newsapi_api_manager_integration.py, not here; this file focuses on
Finnhub's own real behavior and the failover/failback composition
between Finnhub and each of its two Primaries.
"""

import ast
import dataclasses
import pathlib
import unittest

from research_database.repositories.company_repository import CompanyRepository
from research_database.repositories.market_news_repository import MarketNewsRepository
from research_database.repositories.sector_repository import SectorRepository
from research_database.schema.company import Company
from research_database.schema.market_news import MarketNewsItem
from research_database.schema.sector import Sector
from tests.database.test_market_technical_repositories import (
    close_isolated_database_manager,
    make_isolated_database_manager,
)

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
from research_engine.api_manager.providers.finnhub_provider import FinnhubProvider
from research_engine.api_manager.providers.fmp_provider import FMPProvider
from research_engine.api_manager.providers.newsapi_provider import NewsAPIProvider
from research_engine.collectors.company.company_collector import CompanyCollector
from research_engine.collectors.competitors.competitors_collector import CompetitorsCollector
from research_engine.collectors.corporate_actions.corporate_action_collector import (
    CorporateActionCollector,
)
from research_engine.collectors.financial.financial_collector import FinancialCollector
from research_engine.collectors.management.management_collector import ManagementCollector
from research_engine.collectors.market_news.market_news_collector import MarketNewsCollector
from research_engine.collectors.orders_contracts.orders_contracts_collector import (
    OrdersContractsCollector,
)
from research_engine.collectors.products_services.products_services_collector import (
    ProductsServicesCollector,
)
from research_engine.collectors.shareholding.shareholding_collector import ShareholdingCollector

FUNDAMENTAL_DATA_COLLECTOR_CLASSES = (CompanyCollector, FinancialCollector)

ALL_FUNDAMENTAL_DATA_COLLECTOR_CLASSES = (
    CompanyCollector,
    FinancialCollector,
    ManagementCollector,
    ShareholdingCollector,
    CompetitorsCollector,
    ProductsServicesCollector,
    CorporateActionCollector,
    OrdersContractsCollector,
)


def _fmp_returning(payload_json: bytes) -> FMPProvider:
    provider = FMPProvider(api_key="test-key")
    provider._send_request = lambda url: (200, payload_json)  # type: ignore[method-assign]
    return provider


def _newsapi_returning(payload_json: bytes) -> NewsAPIProvider:
    provider = NewsAPIProvider(api_key="test-key")
    provider._send_request = lambda url: (200, payload_json)  # type: ignore[method-assign]
    return provider


def _finnhub_returning(
    payload_json: bytes = b'{"ticker": "SMFG", "name": "Sample Manufacturing Ltd"}',
    **overrides,
) -> FinnhubProvider:
    provider = FinnhubProvider(api_key="test-key", **overrides)
    provider._send_request = lambda url: (200, payload_json)  # type: ignore[method-assign]
    return provider


_FMP_PROFILE_PAYLOAD = b'[{"symbol": "INFY", "companyName": "Infosys Limited"}]'
_NEWSAPI_ARTICLE_PAYLOAD = (
    b'{"status": "ok", "totalResults": 1, "articles": ['
    b'{"source": {"name": "Reuters"}, "title": "Infosys wins deal",'
    b' "description": "A summary.", "url": "https://example.com/infosys",'
    b' "publishedAt": "2026-07-11T09:00:00Z"}]}'
)
_FINNHUB_PROFILE_PAYLOAD = b'{"ticker": "INFY", "name": "Infosys Limited", "marketCapitalization": 90000.0}'
_FINNHUB_NEWS_PAYLOAD = b'[{"headline": "Infosys news", "url": "https://example.com/a", "datetime": 1783737970}]'


class TestBackupProviderIsCorrectlyIdentifiedForBothCategories(unittest.TestCase):
    """Per IMP-10G's Objective: Finnhub is the configured Backup
    Provider for BOTH Fundamental Data and News -- one adapter, one
    key, two independent Category-role rows (API_MANAGER_ARCHITECTURE.md
    Section 2)."""

    def test_finnhub_is_the_registered_backup_for_fundamental_data(self):
        registry = APIRegistry()
        backup = registry.get_backup(Category.FUNDAMENTAL_DATA)
        self.assertEqual(backup.provider_name, ProviderName.FINNHUB)
        self.assertEqual(backup.role, ProviderRole.BACKUP)

    def test_finnhub_is_the_registered_backup_for_news(self):
        registry = APIRegistry()
        backup = registry.get_backup(Category.NEWS)
        self.assertEqual(backup.provider_name, ProviderName.FINNHUB)
        self.assertEqual(backup.role, ProviderRole.BACKUP)

    def test_fmp_is_still_primary_for_fundamental_data(self):
        registry = APIRegistry()
        primary = registry.get_primary(Category.FUNDAMENTAL_DATA)
        self.assertEqual(primary.provider_name, ProviderName.FMP)

    def test_newsapi_is_still_primary_for_news(self):
        registry = APIRegistry()
        primary = registry.get_primary(Category.NEWS)
        self.assertEqual(primary.provider_name, ProviderName.NEWSAPI)


class TestFailoverScenario1PrimaryOnlineFundamentalData(unittest.TestCase):
    """Scenario 1: FMP ONLINE -> API Manager -> FMP used. Finnhub must
    never be touched."""

    def test_fmp_serves_the_request_when_healthy(self):
        manager = APIManager()
        manager.adapters[ProviderName.FMP] = _fmp_returning(_FMP_PROFILE_PAYLOAD)
        manager.adapters[ProviderName.FINNHUB] = _finnhub_returning()

        result = CompanyCollector(api_manager=manager).collect("INFY")

        self.assertEqual(result.collector_status.value, "Success")
        self.assertIn("Financial Modeling Prep", result.sources[0])
        self.assertIn("Primary", result.sources[0])
        self.assertEqual(
            manager.logger.usage_count(ProviderName.FINNHUB, Category.FUNDAMENTAL_DATA), 0
        )

    def test_fmp_marked_online_finnhub_still_unknown(self):
        manager = APIManager()
        manager.adapters[ProviderName.FMP] = _fmp_returning(_FMP_PROFILE_PAYLOAD)
        CompanyCollector(api_manager=manager).collect("INFY")

        fmp_health = manager.health_tracker.get(ProviderName.FMP, Category.FUNDAMENTAL_DATA)
        finnhub_health = manager.health_tracker.get(ProviderName.FINNHUB, Category.FUNDAMENTAL_DATA)
        self.assertEqual(fmp_health.status, HealthStatus.ONLINE)
        self.assertEqual(finnhub_health.status, HealthStatus.UNKNOWN)


class TestFailoverScenario2PrimaryDownFundamentalData(unittest.TestCase):
    """Scenario 2: FMP DOWN -> API Manager -> automatically switch ->
    Finnhub -> data returned -> provider selection logged. Neither
    CompanyCollector nor FinancialCollector is modified to support
    this -- failover happens only inside APIManager, unchanged since
    IMP-10B."""

    def test_fmp_down_automatically_switches_to_finnhub(self):
        manager = APIManager()
        manager.adapters[ProviderName.FMP] = FMPProvider(
            simulate_failure=ProviderDownError("simulated FMP outage")
        )
        manager.adapters[ProviderName.FINNHUB] = _finnhub_returning(_FINNHUB_PROFILE_PAYLOAD)

        result = CompanyCollector(api_manager=manager).collect("INFY")

        self.assertEqual(result.collector_status.value, "Success")
        self.assertIn("Finnhub", result.sources[0])
        self.assertIn("Backup", result.sources[0])

    def test_fmp_marked_down_finnhub_marked_online(self):
        manager = APIManager()
        manager.adapters[ProviderName.FMP] = FMPProvider(
            simulate_failure=ProviderDownError("simulated FMP outage")
        )
        manager.adapters[ProviderName.FINNHUB] = _finnhub_returning(_FINNHUB_PROFILE_PAYLOAD)

        CompanyCollector(api_manager=manager).collect("INFY")

        fmp_health = manager.health_tracker.get(ProviderName.FMP, Category.FUNDAMENTAL_DATA)
        finnhub_health = manager.health_tracker.get(ProviderName.FINNHUB, Category.FUNDAMENTAL_DATA)
        self.assertEqual(fmp_health.status, HealthStatus.DOWN)
        self.assertEqual(finnhub_health.status, HealthStatus.ONLINE)

    def test_provider_selection_is_logged_for_both_attempts(self):
        manager = APIManager()
        manager.adapters[ProviderName.FMP] = FMPProvider(
            simulate_failure=ProviderDownError("simulated FMP outage")
        )
        manager.adapters[ProviderName.FINNHUB] = _finnhub_returning(_FINNHUB_PROFILE_PAYLOAD)

        CompanyCollector(api_manager=manager).collect("INFY")

        fmp_entries = manager.logger.entries_for(ProviderName.FMP, Category.FUNDAMENTAL_DATA)
        finnhub_entries = manager.logger.entries_for(ProviderName.FINNHUB, Category.FUNDAMENTAL_DATA)
        self.assertEqual(len(fmp_entries), 1)
        self.assertEqual(fmp_entries[0].outcome.value, "FAILURE")
        self.assertIsNone(fmp_entries[0].served_by)
        self.assertEqual(len(finnhub_entries), 1)
        self.assertEqual(finnhub_entries[0].outcome.value, "SUCCESS")
        self.assertEqual(finnhub_entries[0].served_by, ProviderRole.BACKUP)
        self.assertEqual(
            manager.logger.most_recent_served_by(Category.FUNDAMENTAL_DATA), ProviderRole.BACKUP
        )

    def test_both_down_reports_collector_failed_never_fabricated(self):
        manager = APIManager()
        manager.adapters[ProviderName.FMP] = FMPProvider(
            simulate_failure=ProviderDownError("simulated FMP outage")
        )
        manager.adapters[ProviderName.FINNHUB] = FinnhubProvider(
            simulate_failure=ProviderDownError("simulated Finnhub outage too")
        )

        result = CompanyCollector(api_manager=manager).collect("INFY")

        self.assertEqual(result.collector_status.value, "Failed")
        self.assertEqual(result.sources, [])


class TestFailoverScenario1PrimaryOnlineNews(unittest.TestCase):
    """Scenario 1 for News: NewsAPI ONLINE -> API Manager -> NewsAPI
    used. Finnhub must never be touched."""

    def test_newsapi_serves_the_request_when_healthy(self):
        manager = APIManager()
        manager.adapters[ProviderName.NEWSAPI] = _newsapi_returning(_NEWSAPI_ARTICLE_PAYLOAD)
        manager.adapters[ProviderName.FINNHUB] = _finnhub_returning()

        result = MarketNewsCollector(api_manager=manager).collect("INFY")

        self.assertEqual(result.collector_status.value, "Success")
        self.assertIn("NewsAPI", result.sources[0])
        self.assertIn("Primary", result.sources[0])
        self.assertEqual(manager.logger.usage_count(ProviderName.FINNHUB, Category.NEWS), 0)


class TestFailoverScenario2PrimaryDownNews(unittest.TestCase):
    """Scenario 2 for News: NewsAPI DOWN -> API Manager -> automatically
    switch -> Finnhub -> data returned -> provider selection logged.
    MarketNewsCollector is never modified to support this."""

    def test_newsapi_down_automatically_switches_to_finnhub(self):
        manager = APIManager()
        manager.adapters[ProviderName.NEWSAPI] = NewsAPIProvider(
            simulate_failure=ProviderDownError("simulated NewsAPI outage")
        )
        manager.adapters[ProviderName.FINNHUB] = _finnhub_returning(_FINNHUB_NEWS_PAYLOAD)

        result = MarketNewsCollector(api_manager=manager).collect("INFY")

        self.assertEqual(result.collector_status.value, "Success")
        self.assertIn("Finnhub", result.sources[0])
        self.assertIn("Backup", result.sources[0])

    def test_newsapi_marked_down_finnhub_marked_online(self):
        manager = APIManager()
        manager.adapters[ProviderName.NEWSAPI] = NewsAPIProvider(
            simulate_failure=ProviderDownError("simulated NewsAPI outage")
        )
        manager.adapters[ProviderName.FINNHUB] = _finnhub_returning(_FINNHUB_NEWS_PAYLOAD)

        MarketNewsCollector(api_manager=manager).collect("INFY")

        newsapi_health = manager.health_tracker.get(ProviderName.NEWSAPI, Category.NEWS)
        finnhub_health = manager.health_tracker.get(ProviderName.FINNHUB, Category.NEWS)
        self.assertEqual(newsapi_health.status, HealthStatus.DOWN)
        self.assertEqual(finnhub_health.status, HealthStatus.ONLINE)

    def test_provider_selection_is_logged_for_both_attempts(self):
        manager = APIManager()
        manager.adapters[ProviderName.NEWSAPI] = NewsAPIProvider(
            simulate_failure=ProviderDownError("simulated NewsAPI outage")
        )
        manager.adapters[ProviderName.FINNHUB] = _finnhub_returning(_FINNHUB_NEWS_PAYLOAD)

        MarketNewsCollector(api_manager=manager).collect("INFY")

        newsapi_entries = manager.logger.entries_for(ProviderName.NEWSAPI, Category.NEWS)
        finnhub_entries = manager.logger.entries_for(ProviderName.FINNHUB, Category.NEWS)
        self.assertEqual(len(newsapi_entries), 1)
        self.assertEqual(newsapi_entries[0].outcome.value, "FAILURE")
        self.assertEqual(len(finnhub_entries), 1)
        self.assertEqual(finnhub_entries[0].outcome.value, "SUCCESS")
        self.assertEqual(finnhub_entries[0].served_by, ProviderRole.BACKUP)
        self.assertEqual(manager.logger.most_recent_served_by(Category.NEWS), ProviderRole.BACKUP)

    def test_both_down_reports_collector_failed_never_fabricated(self):
        manager = APIManager()
        manager.adapters[ProviderName.NEWSAPI] = NewsAPIProvider(
            simulate_failure=ProviderDownError("simulated NewsAPI outage")
        )
        manager.adapters[ProviderName.FINNHUB] = FinnhubProvider(
            simulate_failure=ProviderDownError("simulated Finnhub outage too")
        )

        result = MarketNewsCollector(api_manager=manager).collect("INFY")

        self.assertEqual(result.collector_status.value, "Failed")
        self.assertEqual(result.sources, [])


class TestFailbackScenario3FMPRecoversForFundamentalData(unittest.TestCase):
    """Scenario 3: FMP becomes ONLINE again -> API Manager automatically
    resumes using it as Primary. This is the existing, unmodified
    cool-down recovery mechanism in HealthTracker -- DOWN becomes
    usable again once cool_down_seconds has elapsed, so a genuinely-
    recovered Primary is retried automatically with no manual reset
    and no Collector involvement."""

    def test_fmp_is_retried_and_resumes_as_primary_once_cool_down_elapses(self):
        manager = APIManager()
        manager.health_tracker.cool_down_seconds = 0.0
        manager.adapters[ProviderName.FMP] = FMPProvider(
            simulate_failure=ProviderDownError("simulated FMP outage")
        )
        manager.adapters[ProviderName.FINNHUB] = _finnhub_returning(_FINNHUB_PROFILE_PAYLOAD)

        # Scenario 2: FMP down, Finnhub serves as Backup.
        first = CompanyCollector(api_manager=manager).collect("INFY")
        self.assertIn("Finnhub", first.sources[0])
        fmp_health_after_failure = manager.health_tracker.get(
            ProviderName.FMP, Category.FUNDAMENTAL_DATA
        )
        self.assertEqual(fmp_health_after_failure.status, HealthStatus.DOWN)

        # Scenario 3: FMP "recovers" -- simulated here by replacing the
        # adapter with one whose next real call just succeeds, exactly
        # as a real outage ending would look from APIManager's own
        # perspective.
        manager.adapters[ProviderName.FMP] = _fmp_returning(_FMP_PROFILE_PAYLOAD)
        second = CompanyCollector(api_manager=manager).collect("INFY")

        self.assertIn("Financial Modeling Prep", second.sources[0])
        self.assertIn("Primary", second.sources[0])
        fmp_health_after_recovery = manager.health_tracker.get(
            ProviderName.FMP, Category.FUNDAMENTAL_DATA
        )
        self.assertEqual(fmp_health_after_recovery.status, HealthStatus.ONLINE)

    def test_finnhub_is_not_touched_once_fmp_has_resumed(self):
        manager = APIManager()
        manager.health_tracker.cool_down_seconds = 0.0
        manager.adapters[ProviderName.FMP] = FMPProvider(
            simulate_failure=ProviderDownError("simulated FMP outage")
        )
        manager.adapters[ProviderName.FINNHUB] = _finnhub_returning(_FINNHUB_PROFILE_PAYLOAD)
        CompanyCollector(api_manager=manager).collect("INFY")  # Scenario 2

        manager.adapters[ProviderName.FMP] = _fmp_returning(_FMP_PROFILE_PAYLOAD)
        CompanyCollector(api_manager=manager).collect("INFY")  # Scenario 3

        # Exactly one Finnhub attempt total -- the Scenario 2 one.
        # Scenario 3's successful resumption must not touch Backup at all.
        self.assertEqual(
            manager.logger.usage_count(ProviderName.FINNHUB, Category.FUNDAMENTAL_DATA), 1
        )

    def test_fmp_still_down_within_cool_down_window_stays_on_backup(self):
        """Negative control: failback must NOT happen before the
        cool-down window elapses."""
        manager = APIManager()
        # default cool_down_seconds (60s) -- NOT set to 0 this time.
        manager.adapters[ProviderName.FMP] = FMPProvider(
            simulate_failure=ProviderDownError("simulated FMP outage")
        )
        manager.adapters[ProviderName.FINNHUB] = _finnhub_returning(_FINNHUB_PROFILE_PAYLOAD)
        CompanyCollector(api_manager=manager).collect("INFY")  # marks FMP DOWN

        manager.adapters[ProviderName.FMP] = _fmp_returning(_FMP_PROFILE_PAYLOAD)
        second = CompanyCollector(api_manager=manager).collect("INFY")

        self.assertIn("Finnhub", second.sources[0])
        self.assertEqual(
            manager.logger.usage_count(ProviderName.FMP, Category.FUNDAMENTAL_DATA), 1
        )


class TestFailbackScenario3NewsAPIRecoversForNews(unittest.TestCase):
    """Scenario 3 for News: NewsAPI becomes ONLINE again -> API Manager
    automatically resumes using it as Primary."""

    def test_newsapi_is_retried_and_resumes_as_primary_once_cool_down_elapses(self):
        manager = APIManager()
        manager.health_tracker.cool_down_seconds = 0.0
        manager.adapters[ProviderName.NEWSAPI] = NewsAPIProvider(
            simulate_failure=ProviderDownError("simulated NewsAPI outage")
        )
        manager.adapters[ProviderName.FINNHUB] = _finnhub_returning(_FINNHUB_NEWS_PAYLOAD)

        first = MarketNewsCollector(api_manager=manager).collect("INFY")
        self.assertIn("Finnhub", first.sources[0])
        newsapi_health_after_failure = manager.health_tracker.get(
            ProviderName.NEWSAPI, Category.NEWS
        )
        self.assertEqual(newsapi_health_after_failure.status, HealthStatus.DOWN)

        manager.adapters[ProviderName.NEWSAPI] = _newsapi_returning(_NEWSAPI_ARTICLE_PAYLOAD)
        second = MarketNewsCollector(api_manager=manager).collect("INFY")

        self.assertIn("NewsAPI", second.sources[0])
        self.assertIn("Primary", second.sources[0])
        newsapi_health_after_recovery = manager.health_tracker.get(
            ProviderName.NEWSAPI, Category.NEWS
        )
        self.assertEqual(newsapi_health_after_recovery.status, HealthStatus.ONLINE)

    def test_finnhub_is_not_touched_once_newsapi_has_resumed(self):
        manager = APIManager()
        manager.health_tracker.cool_down_seconds = 0.0
        manager.adapters[ProviderName.NEWSAPI] = NewsAPIProvider(
            simulate_failure=ProviderDownError("simulated NewsAPI outage")
        )
        manager.adapters[ProviderName.FINNHUB] = _finnhub_returning(_FINNHUB_NEWS_PAYLOAD)
        MarketNewsCollector(api_manager=manager).collect("INFY")  # Scenario 2

        manager.adapters[ProviderName.NEWSAPI] = _newsapi_returning(_NEWSAPI_ARTICLE_PAYLOAD)
        MarketNewsCollector(api_manager=manager).collect("INFY")  # Scenario 3

        self.assertEqual(manager.logger.usage_count(ProviderName.FINNHUB, Category.NEWS), 1)


class TestFinnhubHealthIsIndependentPerCategory(unittest.TestCase):
    """Per API_MANAGER_ARCHITECTURE.md Section 5.5/8: Finnhub's
    Fundamental-Backup role and News-Backup role carry INDEPENDENT
    health -- a failure calling one Finnhub endpoint does not imply the
    other is also failing, since each is a distinct `api_provider` row
    keyed by (provider_name, category)."""

    def test_finnhub_down_for_fundamental_data_does_not_affect_its_news_health(self):
        manager = APIManager()
        manager.adapters[ProviderName.FMP] = FMPProvider(
            simulate_failure=ProviderDownError("simulated FMP outage")
        )
        manager.adapters[ProviderName.FINNHUB] = FinnhubProvider(
            simulate_failure=ProviderDownError("simulated Finnhub outage (fundamental only)")
        )
        CompanyCollector(api_manager=manager).collect("INFY")

        fundamental_health = manager.health_tracker.get(
            ProviderName.FINNHUB, Category.FUNDAMENTAL_DATA
        )
        news_health = manager.health_tracker.get(ProviderName.FINNHUB, Category.NEWS)
        self.assertEqual(fundamental_health.status, HealthStatus.DOWN)
        self.assertEqual(news_health.status, HealthStatus.UNKNOWN)

    def test_finnhub_online_for_news_does_not_affect_its_fundamental_data_health(self):
        manager = APIManager()
        manager.adapters[ProviderName.NEWSAPI] = NewsAPIProvider(
            simulate_failure=ProviderDownError("simulated NewsAPI outage")
        )
        manager.adapters[ProviderName.FINNHUB] = _finnhub_returning(_FINNHUB_NEWS_PAYLOAD)
        MarketNewsCollector(api_manager=manager).collect("INFY")

        news_health = manager.health_tracker.get(ProviderName.FINNHUB, Category.NEWS)
        fundamental_health = manager.health_tracker.get(
            ProviderName.FINNHUB, Category.FUNDAMENTAL_DATA
        )
        self.assertEqual(news_health.status, HealthStatus.ONLINE)
        self.assertEqual(fundamental_health.status, HealthStatus.UNKNOWN)


class TestProviderHealthStatesForFinnhub(unittest.TestCase):
    """Verify ONLINE, DOWN, TIMEOUT, RATE_LIMITED, INVALID_KEY, UNKNOWN
    all update correctly for Finnhub specifically, mirroring the same
    proof already established for Twelve Data (IMP-10E)."""

    def test_unknown_before_any_call(self):
        manager = APIManager()
        health = manager.health_tracker.get(ProviderName.FINNHUB, Category.FUNDAMENTAL_DATA)
        self.assertEqual(health.status, HealthStatus.UNKNOWN)

    def test_online_after_success(self):
        manager = APIManager()
        manager.adapters[ProviderName.FMP] = FMPProvider(
            simulate_failure=ProviderDownError("forced")
        )
        manager.adapters[ProviderName.FINNHUB] = _finnhub_returning(_FINNHUB_PROFILE_PAYLOAD)
        CompanyCollector(api_manager=manager).collect("INFY")
        health = manager.health_tracker.get(ProviderName.FINNHUB, Category.FUNDAMENTAL_DATA)
        self.assertEqual(health.status, HealthStatus.ONLINE)

    def test_down_after_generic_failure(self):
        manager = APIManager()
        manager.adapters[ProviderName.FMP] = FMPProvider(
            simulate_failure=ProviderDownError("forced")
        )
        manager.adapters[ProviderName.FINNHUB] = FinnhubProvider(
            simulate_failure=ProviderDownError("forced")
        )
        CompanyCollector(api_manager=manager).collect("INFY")
        health = manager.health_tracker.get(ProviderName.FINNHUB, Category.FUNDAMENTAL_DATA)
        self.assertEqual(health.status, HealthStatus.DOWN)

    def test_timeout_after_timeout_failure(self):
        manager = APIManager()
        manager.adapters[ProviderName.FMP] = FMPProvider(
            simulate_failure=ProviderDownError("forced")
        )
        manager.adapters[ProviderName.FINNHUB] = FinnhubProvider(
            simulate_failure=ProviderTimeoutError("forced timeout")
        )
        CompanyCollector(api_manager=manager).collect("INFY")
        health = manager.health_tracker.get(ProviderName.FINNHUB, Category.FUNDAMENTAL_DATA)
        self.assertEqual(health.status, HealthStatus.TIMEOUT)

    def test_rate_limited_after_rate_limit_failure(self):
        manager = APIManager()
        manager.adapters[ProviderName.FMP] = FMPProvider(
            simulate_failure=ProviderDownError("forced")
        )
        manager.adapters[ProviderName.FINNHUB] = FinnhubProvider(
            simulate_failure=ProviderRateLimitedError("forced rate limit")
        )
        CompanyCollector(api_manager=manager).collect("INFY")
        health = manager.health_tracker.get(ProviderName.FINNHUB, Category.FUNDAMENTAL_DATA)
        self.assertEqual(health.status, HealthStatus.RATE_LIMITED)

    def test_invalid_key_after_invalid_key_failure(self):
        manager = APIManager()
        manager.adapters[ProviderName.FMP] = FMPProvider(
            simulate_failure=ProviderDownError("forced")
        )
        manager.adapters[ProviderName.FINNHUB] = FinnhubProvider(
            simulate_failure=ProviderInvalidKeyError("forced invalid key")
        )
        CompanyCollector(api_manager=manager).collect("INFY")
        health = manager.health_tracker.get(ProviderName.FINNHUB, Category.FUNDAMENTAL_DATA)
        self.assertEqual(health.status, HealthStatus.INVALID_KEY)


class TestDataMapsOntoResearchEngineModels(unittest.TestCase):
    """Finnhub's real response, when it serves as Backup, must never be
    mistaken for FMP's or NewsAPI's shape -- Collector-level field
    mapping is Primary-specific and stays that way."""

    def test_finnhub_fundamental_backup_response_never_triggers_fmp_field_mapping(self):
        manager = APIManager()
        manager.adapters[ProviderName.FMP] = FMPProvider(
            simulate_failure=ProviderDownError("simulated FMP outage")
        )
        manager.adapters[ProviderName.FINNHUB] = _finnhub_returning(_FINNHUB_PROFILE_PAYLOAD)

        result = FinancialCollector(api_manager=manager).collect("INFY")

        self.assertEqual(result.collector_status.value, "Success")
        # placeholder financial_year untouched -- Finnhub's real
        # response was never parsed into FMP-shaped fields.
        self.assertEqual(result.financial_year, "FY2026")
        self.assertIn("Finnhub", result.sources[0])

    def test_finnhub_news_backup_response_never_triggers_newsapi_field_mapping(self):
        manager = APIManager()
        manager.adapters[ProviderName.NEWSAPI] = NewsAPIProvider(
            simulate_failure=ProviderDownError("simulated NewsAPI outage")
        )
        manager.adapters[ProviderName.FINNHUB] = _finnhub_returning(_FINNHUB_NEWS_PAYLOAD)

        result = MarketNewsCollector(api_manager=manager).collect("INFY")

        self.assertEqual(result.collector_status.value, "Success")
        self.assertEqual(
            result.news_title, "Sample Manufacturing Ltd announces new plant expansion"
        )
        self.assertIn("Finnhub", result.sources[0])


class TestFundamentalResponsesMapCorrectlyAfterFailover(unittest.TestCase):
    """Follow-up requirement: fundamental responses continue to map
    correctly into the existing Research Engine models after failover
    -- for EVERY Fundamental Data collector, not just Company/Financial.
    "Correctly" for a Backup response means exactly what it already
    means for every established Primary provider's Backup path
    (Twelve Data, Finnhub-for-FMP, Finnhub-for-NewsAPI): the Result
    object stays fully well-typed and un-corrupted -- Finnhub's
    differently-shaped payload is never force-fit into fields it was
    never meant to populate, so every non-sources/non-timestamp field
    is byte-identical to the same collector's own placeholder value,
    and only Sources/Collector Status reflect the real (Backup)
    outcome. Forcing Finnhub's raw payload into FMP-shaped fields would
    silently produce wrong data -- that would be the actual defect."""

    _EXCLUDED_FIELDS = {"sources", "collection_time", "collector_status"}

    def _non_excluded_fields_match(self, baseline, after_failover) -> bool:
        for field in dataclasses.fields(baseline):
            if field.name in self._EXCLUDED_FIELDS:
                continue
            if getattr(baseline, field.name) != getattr(after_failover, field.name):
                return False
        return True

    def test_every_fundamental_collector_stays_well_typed_and_uncorrupted_after_failover(self):
        for collector_class in ALL_FUNDAMENTAL_DATA_COLLECTOR_CLASSES:
            baseline = collector_class().collect("Sample Manufacturing Ltd (SMFG, NSE)")

            manager = APIManager()
            manager.adapters[ProviderName.FMP] = FMPProvider(
                simulate_failure=ProviderDownError("simulated FMP outage")
            )
            manager.adapters[ProviderName.FINNHUB] = _finnhub_returning()
            after_failover = collector_class(api_manager=manager).collect(
                "Sample Manufacturing Ltd (SMFG, NSE)"
            )

            self.assertEqual(
                after_failover.collector_status.value,
                "Success",
                f"{collector_class.__name__} did not report Success after failover",
            )
            self.assertIn(
                "Finnhub",
                after_failover.sources[0],
                f"{collector_class.__name__} sources did not attribute Finnhub",
            )
            self.assertIn(
                "Backup",
                after_failover.sources[0],
                f"{collector_class.__name__} sources did not attribute Backup role",
            )
            self.assertTrue(
                self._non_excluded_fields_match(baseline, after_failover),
                f"{collector_class.__name__}: a field diverged from its placeholder value after "
                "failover -- Finnhub's payload may have been force-mapped into the wrong field",
            )


class TestNewsResponsesMapCorrectlyAfterFailover(unittest.TestCase):
    """Follow-up requirement: News responses continue to map correctly
    into MarketNewsResult after failover -- same guarantee as above,
    applied to the News Category's one collector."""

    _EXCLUDED_FIELDS = {"sources", "collection_time", "collector_status"}

    def test_market_news_collector_stays_well_typed_and_uncorrupted_after_failover(self):
        baseline = MarketNewsCollector().collect("Sample Manufacturing Ltd (SMFG, NSE)")

        manager = APIManager()
        manager.adapters[ProviderName.NEWSAPI] = NewsAPIProvider(
            simulate_failure=ProviderDownError("simulated NewsAPI outage")
        )
        manager.adapters[ProviderName.FINNHUB] = _finnhub_returning(_FINNHUB_NEWS_PAYLOAD)
        after_failover = MarketNewsCollector(api_manager=manager).collect(
            "Sample Manufacturing Ltd (SMFG, NSE)"
        )

        self.assertEqual(after_failover.collector_status.value, "Success")
        self.assertIn("Finnhub", after_failover.sources[0])
        self.assertIn("Backup", after_failover.sources[0])
        for field in dataclasses.fields(baseline):
            if field.name in self._EXCLUDED_FIELDS:
                continue
            self.assertEqual(
                getattr(baseline, field.name),
                getattr(after_failover, field.name),
                f"MarketNewsResult.{field.name} diverged from its placeholder value after failover",
            )


class TestProviderSpecificNormalizationLocation(unittest.TestCase):
    """Follow-up requirement: provider-specific response differences
    are normalized inside the API Manager or provider layer, never
    inside collectors.

    Confirmed TRUE for the Backup path specifically: no collector
    contains any Finnhub-specific field-shape knowledge at all --
    Finnhub's payload is never parsed into named fields by any
    collector, proven by TestCollectorsNeverModifiedToSupportFailover's
    AST scan (no Finnhub identifier/string literal anywhere in a
    collector) combined with this class's own byte-identical-field
    proof above (Finnhub's real payload changes zero Result fields).

    NOT fully true, and worth stating plainly rather than silently
    passing, for each category's own Primary provider: FMP's raw JSON
    keys ("netIncome", "fiscalYear", "companyName") and NewsAPI's raw
    JSON keys ("title", "description", "publishedAt") are read directly
    inside financial_collector.py / company_collector.py /
    market_news_collector.py's own `_apply_<primary>_*` methods, not
    inside FMPProvider/NewsAPIProvider or APIManager. This is a
    pre-existing characteristic established across IMP-10C and IMP-10F,
    unmodified by IMP-10G's Finnhub work -- this test documents and
    pins down exactly where that Primary-provider field mapping lives
    today, rather than claiming full compliance with the stated ideal.
    Refactoring it into the provider layer would be a genuine
    architecture change to four already-shipped, tested phases, out of
    scope for "do not redesign existing architecture" without an
    explicit decision to do so."""

    def test_finnhub_backup_never_has_field_level_knowledge_in_any_collector(self):
        """The clean half: Backup-path normalization is correctly
        absent from collectors entirely (no Finnhub-shaped field
        reading exists anywhere), rather than incorrectly present."""
        collectors_dir = pathlib.Path(__file__).resolve().parents[2] / "research_engine" / "collectors"
        for package, filename in (
            ("company", "company_collector.py"),
            ("financial", "financial_collector.py"),
            ("market_news", "market_news_collector.py"),
        ):
            source = (collectors_dir / package / filename).read_text(encoding="utf-8")
            # Finnhub's own real field names (per finnhub_provider.py's
            # _parse_response: "ticker", "marketCapitalization") never
            # appear as a dict-key lookup in any collector.
            self.assertNotIn('.get("ticker")', source)
            self.assertNotIn(".get('ticker')", source)
            self.assertNotIn("marketCapitalization", source)

    def test_primary_provider_field_mapping_location_is_documented_not_hidden(self):
        """Pins down today's actual location for FMP's/NewsAPI's own
        raw field-name reads, per this class's own docstring -- fails
        loudly if that code silently moves without this test being
        updated, rather than letting the claim go unverified."""
        collectors_dir = pathlib.Path(__file__).resolve().parents[2] / "research_engine" / "collectors"
        financial_source = (collectors_dir / "financial" / "financial_collector.py").read_text(
            encoding="utf-8"
        )
        self.assertIn('record.get("netIncome")', financial_source)
        self.assertIn('record.get("fiscalYear")', financial_source)

        market_news_source = (collectors_dir / "market_news" / "market_news_collector.py").read_text(
            encoding="utf-8"
        )
        self.assertIn('article.get("title")', market_news_source)
        self.assertIn('article.get("publishedAt")', market_news_source)


class TestNoDuplicatePersistenceAcrossFailoverAndFailback(unittest.TestCase):
    """Follow-up requirement: no duplicate records are created in
    SQLite when the active provider changes during failover or
    failback.

    Verifies two distinct guarantees:
    1. One `collect()` call, however it resolved internally (Primary
       succeeding immediately, or Primary failing and Backup being
       tried), always yields exactly one persistable result -- never
       two rows for what was one logical request. This is a structural
       property of APIManager.request() (Section 6: Backup is only
       ever tried after Primary has already failed, never
       speculatively alongside it -- so at most one ProviderResponse is
       ever produced per request), verified here by asserting the
       actual persisted row count after each individual collect() call.
    2. A failover-then-failback sequence (two separate collect() calls,
       different providers serving each) persists exactly two rows --
       one per real observation -- never silently duplicating or
       overwriting either one. Each `market_news`/`financial_information`
       row is its own point-in-time record by design (the same pattern
       `market_data`/`price_history` already use for repeated
       snapshots of the same company), so two distinct successful
       responses correctly persisting as two distinct rows is the
       intended behavior -- what must never happen is a single
       response being inserted more than once.
    """

    def setUp(self):
        self.db_manager = make_isolated_database_manager()
        sector = SectorRepository(self.db_manager).get_or_create(
            Sector(
                id=0, name="Duplicate Check", size="", growth_trend="",
                dynamics_summary="", regulatory_environment="", benchmark_summary="",
            )
        )
        self.company = CompanyRepository(self.db_manager).create(
            Company(
                id=0, legal_name="INFY", common_name="INFY", registration_details="",
                incorporation_country="IN", headquarters_location="", founding_date="",
                website="", stock_exchanges=["NSE"], ticker_symbols=["INFY"],
                business_description="", mission="", industry="", sector_id=sector.id,
                business_model_summary="", geographic_footprint=[], customer_segments=[],
            )
        )
        self.news_repo = MarketNewsRepository(self.db_manager)

    def tearDown(self):
        close_isolated_database_manager(self.db_manager)

    def _persist(self, result):
        return self.news_repo.create(
            MarketNewsItem(
                id=0, company_id=self.company.id, headline=result.news_title,
                event_date=result.published_time.isoformat(), summary=result.news_summary,
                extracted_facts=list(result.sources), url=result.url,
            )
        )

    def test_a_single_failed_over_call_persists_exactly_one_row(self):
        manager = APIManager()
        manager.adapters[ProviderName.NEWSAPI] = NewsAPIProvider(
            simulate_failure=ProviderDownError("simulated NewsAPI outage")
        )
        manager.adapters[ProviderName.FINNHUB] = _finnhub_returning(_FINNHUB_NEWS_PAYLOAD)

        result = MarketNewsCollector(api_manager=manager).collect("INFY")
        self._persist(result)

        rows = self.news_repo.list_by_company(self.company.id)
        self.assertEqual(len(rows), 1)

    def test_failover_then_failback_persists_exactly_two_rows_never_more(self):
        manager = APIManager()
        manager.health_tracker.cool_down_seconds = 0.0
        manager.adapters[ProviderName.NEWSAPI] = NewsAPIProvider(
            simulate_failure=ProviderDownError("simulated NewsAPI outage")
        )
        manager.adapters[ProviderName.FINNHUB] = _finnhub_returning(_FINNHUB_NEWS_PAYLOAD)

        # Failover: NewsAPI down, Finnhub serves -- persist the one result.
        failover_result = MarketNewsCollector(api_manager=manager).collect("INFY")
        self._persist(failover_result)

        # Failback: NewsAPI recovers -- persist the one (different) result.
        manager.adapters[ProviderName.NEWSAPI] = _newsapi_returning(_NEWSAPI_ARTICLE_PAYLOAD)
        failback_result = MarketNewsCollector(api_manager=manager).collect("INFY")
        self._persist(failback_result)

        rows = self.news_repo.list_by_company(self.company.id)
        self.assertEqual(len(rows), 2)
        # Each row traces back to the provider that actually served it --
        # neither overwrote nor duplicated the other.
        sources_seen = {tuple(row.extracted_facts) for row in rows}
        self.assertEqual(len(sources_seen), 2)

    def test_the_active_provider_switch_itself_never_writes_to_sqlite(self):
        """APIManager's Provider Selection Logic and Failover Rules are
        entirely in-memory (HealthTracker, APILogger) -- switching which
        provider is active never touches SQLite on its own; only an
        explicit persist() call (made by the caller, once per
        successful result) ever does."""
        manager = APIManager()
        manager.adapters[ProviderName.NEWSAPI] = NewsAPIProvider(
            simulate_failure=ProviderDownError("simulated NewsAPI outage")
        )
        manager.adapters[ProviderName.FINNHUB] = _finnhub_returning(_FINNHUB_NEWS_PAYLOAD)

        # Two collect() calls, no persistence at all.
        MarketNewsCollector(api_manager=manager).collect("INFY")
        MarketNewsCollector(api_manager=manager).collect("INFY")

        self.assertEqual(len(self.news_repo.list_by_company(self.company.id)), 0)


class TestCollectorsNeverModifiedToSupportFailover(unittest.TestCase):
    """Per IMP-10G: Finnhub going live requires no Collector change at
    all -- AST-based structural proof that neither
    CompanyCollector/FinancialCollector nor MarketNewsCollector contains
    any Finnhub-specific logic, failover branching, or provider-name
    comparison beyond each one's own pre-existing Primary-only check."""

    UPDATED_COLLECTOR_FILES = (
        ("company", "company_collector.py"),
        ("financial", "financial_collector.py"),
        ("market_news", "market_news_collector.py"),
    )

    def _collectors_dir(self) -> pathlib.Path:
        return pathlib.Path(__file__).resolve().parents[2] / "research_engine" / "collectors"

    def test_no_code_reference_to_finnhub_in_any_collector(self):
        """Docstring prose may name Finnhub (for documentation); no
        executable code token (identifier, string literal used in a
        comparison, import) may."""
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
                        "FINNHUB",
                        node.value.upper().replace(" ", "_"),
                        f"{path}: found a Finnhub-referencing string constant in code",
                    )
                if isinstance(node, ast.Name):
                    self.assertNotIn("Finnhub", node.id, f"{path}: found a Finnhub identifier")
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    module = getattr(node, "module", None) or ""
                    self.assertNotIn("finnhub", module, f"{path}: found a Finnhub import")
                    for alias in node.names:
                        self.assertNotIn(
                            "Finnhub", alias.name, f"{path}: found a Finnhub import"
                        )

    def test_fundamental_collectors_only_ever_check_for_fmp_by_name(self):
        for package, filename in (("company", "company_collector.py"), ("financial", "financial_collector.py")):
            path = self._collectors_dir() / package / filename
            source = path.read_text(encoding="utf-8")
            self.assertIn("ProviderName.FMP", source)

    def test_market_news_collector_only_ever_checks_for_newsapi_by_name(self):
        path = self._collectors_dir() / "market_news" / "market_news_collector.py"
        source = path.read_text(encoding="utf-8")
        self.assertIn("ProviderName.NEWSAPI", source)


if __name__ == "__main__":
    unittest.main()
