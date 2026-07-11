"""Integration tests for the NewsAPI Integration (IMP-10F): the Market
News Collector talking to a real (HTTP-mocked) APIManager wired to a
real NewsAPIProvider. Finnhub remains the configured Backup Provider
for News and stays a placeholder -- wherever this suite needs its
Backup path to trivially succeed, the existing placeholder
FinnhubProvider (deterministic mock data, or simulate_failure) is used
directly.

Every HTTP interaction is mocked at NewsAPIProvider's `_send_request`
seam -- no test in this module ever performs a live internet call, per
Claude-Prompts/IMP_10F_NewsAPI_Integration.md's Testing requirement.
"""

import ast
import json
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
from research_engine.api_manager.providers.finnhub_provider import FinnhubProvider
from research_engine.api_manager.providers.newsapi_provider import NewsAPIProvider
from research_engine.collectors.market_news.market_news_collector import MarketNewsCollector


def _newsapi_returning(payload_json: bytes) -> NewsAPIProvider:
    provider = NewsAPIProvider(api_key="test-key")
    provider._send_request = lambda url: (200, payload_json)  # type: ignore[method-assign]
    return provider


_ONE_ARTICLE_PAYLOAD = (
    b'{"status": "ok", "totalResults": 1, "articles": ['
    b'{"source": {"id": null, "name": "Economic Times"}, "author": "Staff",'
    b' "title": "Infosys wins large multi-year deal", '
    b'"description": "Infosys announced a new multi-year outsourcing deal.",'
    b' "url": "https://example.com/infosys-deal", "urlToImage": null,'
    b' "publishedAt": "2026-07-10T09:00:00Z", "content": null}]}'
)

_TWO_ARTICLES_WITH_ONE_DUPLICATE_PAYLOAD = (
    b'{"status": "ok", "totalResults": 3, "articles": ['
    b'{"source": {"name": "Reuters"}, "title": "TCS Q1 results beat estimates",'
    b' "description": "TCS reported higher than expected profit.",'
    b' "url": "https://example.com/tcs-results", "publishedAt": "2026-07-10T11:00:00Z"},'
    b'{"source": {"name": "Wire Copy"}, "title": "TCS Q1 results (syndicated)",'
    b' "description": "Syndicated copy of the same story.",'
    b' "url": "https://example.com/tcs-results", "publishedAt": "2026-07-10T11:05:00Z"},'
    b'{"source": {"name": "Mint"}, "title": "TCS announces buyback",'
    b' "description": "TCS board approved a share buyback.",'
    b' "url": "https://example.com/tcs-buyback", "publishedAt": "2026-07-09T08:00:00Z"}]}'
)

_EMPTY_ARTICLES_PAYLOAD = b'{"status": "ok", "totalResults": 0, "articles": []}'


class TestBackupProviderIsCorrectlyIdentified(unittest.TestCase):
    """Per IMP-10F's Objective: NewsAPI is the live Primary Provider,
    Finnhub remains the configured Backup Provider (still a placeholder)
    for the News Category."""

    def test_newsapi_is_the_registered_primary_for_news(self):
        registry = APIRegistry()
        primary = registry.get_primary(Category.NEWS)
        self.assertEqual(primary.provider_name, ProviderName.NEWSAPI)
        self.assertEqual(primary.role, ProviderRole.PRIMARY)

    def test_finnhub_is_the_registered_backup_for_news(self):
        registry = APIRegistry()
        backup = registry.get_backup(Category.NEWS)
        self.assertEqual(backup.provider_name, ProviderName.FINNHUB)
        self.assertEqual(backup.role, ProviderRole.BACKUP)

    def test_finnhub_is_never_actually_called_when_newsapi_succeeds(self):
        manager = APIManager()
        manager.adapters[ProviderName.NEWSAPI] = _newsapi_returning(_ONE_ARTICLE_PAYLOAD)
        MarketNewsCollector(api_manager=manager).collect("INFY")
        self.assertEqual(manager.logger.usage_count(ProviderName.FINNHUB, Category.NEWS), 0)


class TestMarketNewsCollectorReachesNewsAPIThroughAPIManager(unittest.TestCase):
    """End to end: Collector.collect() -> APIManager.request() ->
    NewsAPIProvider.call() (HTTP mocked) -> back up through APIManager
    to the Collector's Result."""

    def test_collector_succeeds_through_a_real_api_manager(self):
        manager = APIManager()
        manager.adapters[ProviderName.NEWSAPI] = _newsapi_returning(_ONE_ARTICLE_PAYLOAD)
        result = MarketNewsCollector(api_manager=manager).collect("INFY")

        self.assertEqual(result.collector_status.value, "Success")
        self.assertEqual(len(result.sources), 1)
        self.assertIn("NewsAPI", result.sources[0])
        self.assertIn("Primary", result.sources[0])

    def test_api_manager_actually_recorded_the_attempt(self):
        manager = APIManager()
        manager.adapters[ProviderName.NEWSAPI] = _newsapi_returning(_ONE_ARTICLE_PAYLOAD)
        MarketNewsCollector(api_manager=manager).collect("INFY")

        entries = manager.logger.entries_for(ProviderName.NEWSAPI, Category.NEWS)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].collector_name, "Market News Collector")

    def test_without_an_api_manager_the_collector_still_returns_placeholder_success(self):
        """Backward compatibility: omitting api_manager entirely (the
        default) must behave exactly as every prior phase."""
        collector = MarketNewsCollector()
        result = collector.collect("Sample Manufacturing Ltd (SMFG, NSE)")
        self.assertEqual(result.collector_status.value, "Success")
        self.assertIn("(placeholder)", result.sources[0])


class TestDataMapsOntoResearchEngineModels(unittest.TestCase):
    """IMP-10F's checklist: real NewsAPI data must map onto the
    existing MarketNewsResult dataclass's typed fields, publication
    timestamps preserved exactly."""

    def test_article_maps_onto_market_news_result(self):
        manager = APIManager()
        manager.adapters[ProviderName.NEWSAPI] = _newsapi_returning(_ONE_ARTICLE_PAYLOAD)
        result = MarketNewsCollector(api_manager=manager).collect("INFY")

        self.assertEqual(result.news_title, "Infosys wins large multi-year deal")
        self.assertEqual(
            result.news_summary, "Infosys announced a new multi-year outsourcing deal."
        )
        self.assertEqual(result.source_name, "Economic Times")
        self.assertEqual(result.url, "https://example.com/infosys-deal")
        self.assertEqual(result.related_companies, ["INFY"])
        # NewsAPI's own publishedAt (2026-07-10T09:00:00Z), preserved exactly.
        self.assertEqual(result.published_time.year, 2026)
        self.assertEqual(result.published_time.month, 7)
        self.assertEqual(result.published_time.day, 10)
        self.assertEqual(result.published_time.hour, 9)

    def test_backup_finnhub_response_never_triggers_newsapi_field_mapping(self):
        manager = APIManager()
        manager.adapters[ProviderName.NEWSAPI] = NewsAPIProvider(
            simulate_failure=ProviderDownError("simulated NewsAPI outage")
        )
        manager.adapters[ProviderName.FINNHUB] = FinnhubProvider()
        result = MarketNewsCollector(api_manager=manager).collect(
            "Sample Manufacturing Ltd (SMFG, NSE)"
        )

        self.assertEqual(result.collector_status.value, "Success")
        # placeholder title/url untouched -- Finnhub's placeholder
        # response was never mistaken for a NewsAPI article.
        self.assertEqual(
            result.news_title, "Sample Manufacturing Ltd announces new plant expansion"
        )
        self.assertEqual(
            result.url, "https://example.com/sample-manufacturing-plant-expansion"
        )
        self.assertIn("Finnhub", result.sources[0])


class TestUrlHandling(unittest.TestCase):
    """Follow-up requirements: the URL is preserved exactly (including
    unusual-but-valid characters), remains a valid absolute http(s)
    URL after mapping, and a missing/empty/non-http(s) URL degrades
    gracefully instead of breaking the pipeline or leaking a stale
    placeholder value."""

    def _collect_with_article(self, article_fields: dict):
        payload = {
            "status": "ok",
            "totalResults": 1,
            "articles": [
                {
                    "source": {"name": "Example Source"},
                    "title": "A relevant headline",
                    "description": "A relevant description.",
                    "publishedAt": "2026-07-11T10:00:00Z",
                    **article_fields,
                }
            ],
        }
        manager = APIManager()
        manager.adapters[ProviderName.NEWSAPI] = _newsapi_returning(json.dumps(payload).encode())
        return MarketNewsCollector(api_manager=manager).collect("TESTSYM")

    def test_url_with_query_string_and_fragment_is_preserved_byte_for_byte(self):
        exact_url = (
            "https://example.com/path/to-article?id=123&ref=abc%20def"
            "&tag=%E2%9C%93#section-2"
        )
        result = self._collect_with_article({"url": exact_url})
        self.assertEqual(result.url, exact_url)

    def test_missing_url_key_degrades_to_empty_string_not_the_stale_placeholder(self):
        result = self._collect_with_article({})
        self.assertEqual(result.collector_status.value, "Success")
        self.assertEqual(result.url, "")

    def test_empty_string_url_degrades_to_empty_string(self):
        result = self._collect_with_article({"url": ""})
        self.assertEqual(result.collector_status.value, "Success")
        self.assertEqual(result.url, "")

    def test_null_url_degrades_to_empty_string(self):
        result = self._collect_with_article({"url": None})
        self.assertEqual(result.collector_status.value, "Success")
        self.assertEqual(result.url, "")

    def test_non_http_scheme_url_is_rejected_to_empty_string(self):
        for bad_url in ("javascript:alert(1)", "ftp://example.com/a", "/relative/path", "example.com/a"):
            result = self._collect_with_article({"url": bad_url})
            self.assertEqual(result.url, "", f"expected '' for {bad_url!r}")

    def test_uppercase_scheme_is_still_accepted_and_preserved_exactly(self):
        exact_url = "HTTPS://Example.com/Article"
        result = self._collect_with_article({"url": exact_url})
        self.assertEqual(result.url, exact_url)

    def test_missing_url_never_breaks_the_rest_of_the_pipeline(self):
        """A missing url must not affect any other mapped field or the
        collector status -- the pipeline degrades gracefully, not
        partially."""
        result = self._collect_with_article({})
        self.assertEqual(result.news_title, "A relevant headline")
        self.assertEqual(result.news_summary, "A relevant description.")
        self.assertEqual(result.collector_status.value, "Success")
        self.assertIn("NewsAPI", result.sources[0])


class TestDuplicateRemoval(unittest.TestCase):
    """Duplicate articles are removed within the API Manager result
    before the Collector maps the first one -- the second, later
    article never overwrites the first."""

    def test_deduplicated_article_list_is_available_on_the_raw_result(self):
        manager = APIManager()
        manager.adapters[ProviderName.NEWSAPI] = _newsapi_returning(
            _TWO_ARTICLES_WITH_ONE_DUPLICATE_PAYLOAD
        )
        api_result = manager.request(
            Category.NEWS, "Company News", {"query": "TCS"}, collector_name="test"
        )
        self.assertEqual(len(api_result.data["articles"]), 2)
        self.assertEqual(api_result.data["duplicates_removed"], 1)

    def test_collector_maps_the_first_deduplicated_article(self):
        manager = APIManager()
        manager.adapters[ProviderName.NEWSAPI] = _newsapi_returning(
            _TWO_ARTICLES_WITH_ONE_DUPLICATE_PAYLOAD
        )
        result = MarketNewsCollector(api_manager=manager).collect("TCS")
        self.assertEqual(result.news_title, "TCS Q1 results beat estimates")
        self.assertEqual(result.url, "https://example.com/tcs-results")


class TestEmptyResultHandling(unittest.TestCase):
    """NewsAPI succeeds (HTTP 200) but returns zero articles for a
    query it has no data for -- treated as Collector Failed, never
    fabricated, and never itself a trigger for failover."""

    def test_empty_articles_reports_collector_failed(self):
        manager = APIManager()
        manager.adapters[ProviderName.NEWSAPI] = _newsapi_returning(_EMPTY_ARTICLES_PAYLOAD)
        result = MarketNewsCollector(api_manager=manager).collect("NoSuchCompanyXYZ")

        self.assertEqual(result.collector_status.value, "Failed")
        self.assertEqual(result.sources, [])

    def test_empty_articles_never_triggers_failover(self):
        manager = APIManager()
        manager.adapters[ProviderName.NEWSAPI] = _newsapi_returning(_EMPTY_ARTICLES_PAYLOAD)
        MarketNewsCollector(api_manager=manager).collect("NoSuchCompanyXYZ")
        self.assertEqual(manager.logger.usage_count(ProviderName.FINNHUB, Category.NEWS), 0)


class TestMockedFailureModesAtTheCollectorLevel(unittest.TestCase):
    """Invalid API key, Timeout, and Rate Limit handling, mocked only,
    verified end to end from the Collector's perspective."""

    def test_invalid_api_key_fails_over_and_collector_still_succeeds(self):
        manager = APIManager()
        manager.adapters[ProviderName.NEWSAPI] = NewsAPIProvider(
            simulate_failure=ProviderInvalidKeyError("simulated invalid key")
        )
        manager.adapters[ProviderName.FINNHUB] = FinnhubProvider()
        result = MarketNewsCollector(api_manager=manager).collect("INFY")

        self.assertEqual(result.collector_status.value, "Success")
        self.assertIn("Finnhub", result.sources[0])
        health = manager.health_tracker.get(ProviderName.NEWSAPI, Category.NEWS)
        self.assertEqual(health.status, HealthStatus.INVALID_KEY)

    def test_timeout_fails_over_and_collector_still_succeeds(self):
        manager = APIManager()
        manager.adapters[ProviderName.NEWSAPI] = NewsAPIProvider(
            simulate_failure=ProviderTimeoutError("simulated timeout")
        )
        manager.adapters[ProviderName.FINNHUB] = FinnhubProvider()
        result = MarketNewsCollector(api_manager=manager).collect("INFY")

        self.assertEqual(result.collector_status.value, "Success")
        health = manager.health_tracker.get(ProviderName.NEWSAPI, Category.NEWS)
        self.assertEqual(health.status, HealthStatus.TIMEOUT)

    def test_rate_limit_fails_over_and_collector_still_succeeds(self):
        manager = APIManager()
        manager.adapters[ProviderName.NEWSAPI] = NewsAPIProvider(
            simulate_failure=ProviderRateLimitedError("simulated rate limit")
        )
        manager.adapters[ProviderName.FINNHUB] = FinnhubProvider()
        result = MarketNewsCollector(api_manager=manager).collect("INFY")

        self.assertEqual(result.collector_status.value, "Success")
        health = manager.health_tracker.get(ProviderName.NEWSAPI, Category.NEWS)
        self.assertEqual(health.status, HealthStatus.RATE_LIMITED)

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


class TestCollectorsNeverImportNewsAPIOrNetworkDirectly(unittest.TestCase):
    """AST-based structural proof, mirroring
    test_alpha_vantage_api_manager_integration.py's equivalent -- the
    updated Market News Collector's only new dependency is
    `research_engine.api_manager` (via a relative import), never
    newsapi_provider, urllib, http, or socket directly."""

    FORBIDDEN_SUBSTRINGS = (
        "newsapi_provider",
        "NewsAPIProvider",
        "import urllib",
        "import socket",
        "import http",
        "import requests",
    )

    def _collector_path(self) -> pathlib.Path:
        return (
            pathlib.Path(__file__).resolve().parents[2]
            / "research_engine"
            / "collectors"
            / "market_news"
            / "market_news_collector.py"
        )

    def test_no_forbidden_substring_appears_in_the_collector(self):
        source = self._collector_path().read_text(encoding="utf-8")
        for forbidden in self.FORBIDDEN_SUBSTRINGS:
            self.assertNotIn(forbidden, source, f"found forbidden '{forbidden}'")

    def test_only_relative_imports_reach_outside_the_collector_s_own_package(self):
        allowed_stdlib = {"dataclasses", "datetime", "enum", "typing", "__future__"}
        tree = ast.parse(self._collector_path().read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.level == 0:
                self.assertIn(
                    node.module, allowed_stdlib, f"unexpected absolute import '{node.module}'"
                )
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    top = alias.name.split(".")[0]
                    self.assertIn(top, allowed_stdlib, f"unexpected import '{alias.name}'")

    def test_relative_api_manager_import_resolves_to_the_package_not_a_submodule(self):
        allowed_names = {"APIManager", "Category", "ProviderName"}
        tree = ast.parse(self._collector_path().read_text(encoding="utf-8"))
        relative_imports = [
            node for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and node.level > 0
        ]
        api_manager_imports = [node for node in relative_imports if node.module == "api_manager"]
        self.assertEqual(len(api_manager_imports), 1, "expected exactly one `from ...api_manager import ...`")
        imported_names = {alias.name for alias in api_manager_imports[0].names}
        self.assertTrue(
            {"APIManager", "Category"}.issubset(imported_names),
            "missing required APIManager/Category import",
        )
        self.assertTrue(
            imported_names.issubset(allowed_names),
            f"unexpected api_manager import(s) {imported_names - allowed_names}",
        )


if __name__ == "__main__":
    unittest.main()
