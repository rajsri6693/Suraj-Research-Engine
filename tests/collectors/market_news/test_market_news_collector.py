"""Unit tests for research_engine.collectors.market_news.market_news_collector."""

import unittest
from datetime import datetime

from research_engine.collectors.base_collector import BaseCollector
from research_engine.collectors.collector_factory import CollectorFactory
from research_engine.collectors.collector_registry import CollectorRegistry
from research_engine.collectors.market_news.market_news_collector import (
    InvalidResearchTopicError,
    MarketNewsCollector,
)
from research_engine.collectors.market_news.market_news_result import (
    CollectorStatus,
    MarketNewsResult,
)


class TestValidArticleUrl(unittest.TestCase):
    """Unit coverage for MarketNewsCollector._valid_article_url --
    preserves a valid absolute http(s) URL exactly, degrades anything
    else to ''."""

    def test_valid_https_url_preserved_exactly(self):
        url = "https://example.com/a?x=1&y=2#frag"
        self.assertEqual(MarketNewsCollector._valid_article_url(url), url)

    def test_valid_http_url_preserved_exactly(self):
        url = "http://example.com/a"
        self.assertEqual(MarketNewsCollector._valid_article_url(url), url)

    def test_uppercase_scheme_accepted_and_preserved_exactly(self):
        url = "HTTPS://Example.com/A"
        self.assertEqual(MarketNewsCollector._valid_article_url(url), url)

    def test_none_degrades_to_empty_string(self):
        self.assertEqual(MarketNewsCollector._valid_article_url(None), "")

    def test_empty_string_degrades_to_empty_string(self):
        self.assertEqual(MarketNewsCollector._valid_article_url(""), "")

    def test_relative_path_degrades_to_empty_string(self):
        self.assertEqual(MarketNewsCollector._valid_article_url("/a/b"), "")

    def test_non_http_scheme_degrades_to_empty_string(self):
        for bad in ("ftp://example.com/a", "javascript:alert(1)", "mailto:a@b.com"):
            self.assertEqual(MarketNewsCollector._valid_article_url(bad), "")

    def test_non_string_degrades_to_empty_string(self):
        self.assertEqual(MarketNewsCollector._valid_article_url(12345), "")


class TestCollectorCreation(unittest.TestCase):
    def test_can_be_instantiated(self):
        collector = MarketNewsCollector()
        self.assertIsInstance(collector, MarketNewsCollector)

    def test_is_a_base_collector(self):
        self.assertIsInstance(MarketNewsCollector(), BaseCollector)


class TestCollectorMetadata(unittest.TestCase):
    def setUp(self):
        self.collector = MarketNewsCollector()

    def test_collector_name(self):
        self.assertEqual(self.collector.collector_name, "Market News Collector")

    def test_knowledge_section(self):
        self.assertEqual(self.collector.knowledge_section, "Market News")


class TestCollectReturnType(unittest.TestCase):
    def test_collect_returns_a_market_news_result(self):
        result = MarketNewsCollector().collect("Latest announcement.")
        self.assertIsInstance(result, MarketNewsResult)


class TestReturnedStructureValidity(unittest.TestCase):
    def setUp(self):
        self.result = MarketNewsCollector().collect("Latest announcement.")

    def test_title_summary_category_and_impact_are_non_empty_strings(self):
        for value in (
            self.result.news_title,
            self.result.news_summary,
            self.result.news_category,
            self.result.impact,
        ):
            self.assertIsInstance(value, str)
            self.assertTrue(value.strip())

    def test_source_name_is_a_non_empty_string(self):
        self.assertIsInstance(self.result.source_name, str)
        self.assertTrue(self.result.source_name.strip())

    def test_url_is_a_non_empty_string(self):
        self.assertIsInstance(self.result.url, str)
        self.assertTrue(self.result.url.strip())

    def test_published_time_is_a_datetime(self):
        self.assertIsInstance(self.result.published_time, datetime)

    def test_related_companies_and_sectors_are_lists_of_strings(self):
        for value in (self.result.related_companies, self.result.related_sectors):
            self.assertIsInstance(value, list)
            self.assertTrue(all(isinstance(item, str) for item in value))

    def test_sources_is_a_non_empty_list_of_strings(self):
        self.assertIsInstance(self.result.sources, list)
        self.assertTrue(len(self.result.sources) > 0)
        self.assertTrue(all(isinstance(source, str) for source in self.result.sources))

    def test_collection_time_is_a_datetime(self):
        self.assertIsInstance(self.result.collection_time, datetime)

    def test_collector_status_is_success(self):
        self.assertEqual(self.result.collector_status, CollectorStatus.SUCCESS)

    def test_each_call_returns_an_independent_result(self):
        first = MarketNewsCollector().collect("Topic A")
        second = MarketNewsCollector().collect("Topic B")
        self.assertIsNot(first, second)
        self.assertIsNot(first.related_companies, second.related_companies)
        self.assertIsNot(first.sources, second.sources)


class TestInvalidTopicHandling(unittest.TestCase):
    def setUp(self):
        self.collector = MarketNewsCollector()

    def test_empty_string_topic_is_rejected(self):
        with self.assertRaises(InvalidResearchTopicError):
            self.collector.collect("")

    def test_whitespace_only_topic_is_rejected(self):
        with self.assertRaises(InvalidResearchTopicError):
            self.collector.collect("   ")

    def test_none_topic_is_rejected(self):
        with self.assertRaises(InvalidResearchTopicError):
            self.collector.collect(None)


class TestIntegrationWithCollectorFramework(unittest.TestCase):
    def test_registers_and_creates_through_the_existing_framework(self):
        registry = CollectorRegistry()
        registry.register_collector("Market News", MarketNewsCollector)
        factory = CollectorFactory(registry)

        collector = factory.create_collector("Market News")
        self.assertIsInstance(collector, MarketNewsCollector)
        result = collector.collect("Latest announcement.")
        self.assertIsInstance(result, MarketNewsResult)


class TestNoForeignDependencies(unittest.TestCase):
    def test_only_standard_library_and_framework_imports(self):
        import ast
        import pathlib

        allowed_stdlib = {"dataclasses", "datetime", "enum", "typing", "__future__"}
        forbidden_modules = {
            "http",
            "http.client",
            "urllib",
            "urllib.request",
            "requests",
            "socket",
            "sqlite3",
            "ai",
            "openai",
            "anthropic",
        }

        package_dir = (
            pathlib.Path(__file__).resolve().parents[3]
            / "research_engine"
            / "collectors"
            / "market_news"
        )
        for module_path in package_dir.glob("*.py"):
            tree = ast.parse(module_path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    if node.level > 0:
                        continue  # relative import within the collectors package
                    self.assertNotIn(node.module, forbidden_modules)
                    self.assertIn(
                        node.module,
                        allowed_stdlib,
                        f"{module_path.name}: unexpected import '{node.module}'",
                    )
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        top = alias.name.split(".")[0]
                        self.assertNotIn(top, forbidden_modules)
                        self.assertIn(
                            top,
                            allowed_stdlib,
                            f"{module_path.name}: unexpected import '{alias.name}'",
                        )


if __name__ == "__main__":
    unittest.main()
