"""Unit tests for research_engine.collectors.shareholding.shareholding_collector."""

import unittest
from datetime import datetime

from research_engine.collectors.base_collector import BaseCollector
from research_engine.collectors.collector_factory import CollectorFactory
from research_engine.collectors.collector_registry import CollectorRegistry
from research_engine.collectors.shareholding.shareholding_collector import (
    InvalidResearchTopicError,
    ShareholdingCollector,
)
from research_engine.collectors.shareholding.shareholding_result import (
    CollectorStatus,
    ShareholdingResult,
)


class TestCollectorCreation(unittest.TestCase):
    def test_can_be_instantiated(self):
        collector = ShareholdingCollector()
        self.assertIsInstance(collector, ShareholdingCollector)

    def test_is_a_base_collector(self):
        self.assertIsInstance(ShareholdingCollector(), BaseCollector)


class TestCollectorMetadata(unittest.TestCase):
    def setUp(self):
        self.collector = ShareholdingCollector()

    def test_collector_name(self):
        self.assertEqual(self.collector.collector_name, "Shareholding Collector")

    def test_knowledge_section(self):
        self.assertEqual(self.collector.knowledge_section, "Shareholding")


class TestCollectReturnType(unittest.TestCase):
    def test_collect_returns_a_shareholding_result(self):
        result = ShareholdingCollector().collect(
            "Full analysis ahead of quarterly results next week."
        )
        self.assertIsInstance(result, ShareholdingResult)


class TestReturnedStructureValidity(unittest.TestCase):
    def setUp(self):
        self.result = ShareholdingCollector().collect(
            "Full analysis ahead of quarterly results next week."
        )

    def test_company_name_quarter_and_summary_are_non_empty_strings(self):
        for value in (
            self.result.company_name,
            self.result.quarter,
            self.result.institutional_holding_summary,
        ):
            self.assertIsInstance(value, str)
            self.assertTrue(value.strip())

    def test_holding_percentages_are_numbers(self):
        for value in (
            self.result.promoter_holding,
            self.result.fii_holding,
            self.result.dii_holding,
            self.result.public_holding,
            self.result.government_holding,
            self.result.insider_holding,
            self.result.share_pledged,
        ):
            self.assertIsInstance(value, (int, float))

    def test_holding_percentages_sum_to_roughly_one_hundred(self):
        total = (
            self.result.promoter_holding
            + self.result.fii_holding
            + self.result.dii_holding
            + self.result.public_holding
            + self.result.government_holding
            + self.result.insider_holding
        )
        self.assertAlmostEqual(total, 100.0, delta=1.0)

    def test_shareholding_changes_is_a_list_of_strings(self):
        self.assertIsInstance(self.result.shareholding_changes, list)
        self.assertTrue(
            all(isinstance(item, str) for item in self.result.shareholding_changes)
        )

    def test_sources_is_a_non_empty_list_of_strings(self):
        self.assertIsInstance(self.result.sources, list)
        self.assertTrue(len(self.result.sources) > 0)
        self.assertTrue(all(isinstance(source, str) for source in self.result.sources))

    def test_collection_time_is_a_datetime(self):
        self.assertIsInstance(self.result.collection_time, datetime)

    def test_collector_status_is_success(self):
        self.assertEqual(self.result.collector_status, CollectorStatus.SUCCESS)

    def test_each_call_returns_an_independent_result(self):
        first = ShareholdingCollector().collect("Topic A")
        second = ShareholdingCollector().collect("Topic B")
        self.assertIsNot(first, second)
        self.assertIsNot(first.shareholding_changes, second.shareholding_changes)
        self.assertIsNot(first.sources, second.sources)


class TestInvalidTopicHandling(unittest.TestCase):
    def setUp(self):
        self.collector = ShareholdingCollector()

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
        registry.register_collector("Shareholding", ShareholdingCollector)
        factory = CollectorFactory(registry)

        collector = factory.create_collector("Shareholding")
        self.assertIsInstance(collector, ShareholdingCollector)
        result = collector.collect("Full analysis ahead of quarterly results next week.")
        self.assertIsInstance(result, ShareholdingResult)


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
            / "shareholding"
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
