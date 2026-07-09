"""Unit tests for research_engine.collectors.financial.financial_collector."""

import unittest
from datetime import datetime

from research_engine.collectors.base_collector import BaseCollector
from research_engine.collectors.collector_factory import CollectorFactory
from research_engine.collectors.collector_registry import CollectorRegistry
from research_engine.collectors.financial.financial_collector import (
    FinancialCollector,
    InvalidResearchTopicError,
)
from research_engine.collectors.financial.financial_result import (
    CollectorStatus,
    FinancialResult,
)


class TestCollectorCreation(unittest.TestCase):
    def test_can_be_instantiated(self):
        collector = FinancialCollector()
        self.assertIsInstance(collector, FinancialCollector)

    def test_is_a_base_collector(self):
        self.assertIsInstance(FinancialCollector(), BaseCollector)


class TestCollectorMetadata(unittest.TestCase):
    def setUp(self):
        self.collector = FinancialCollector()

    def test_collector_name(self):
        self.assertEqual(
            self.collector.collector_name, "Financial Information Collector"
        )

    def test_knowledge_section(self):
        self.assertEqual(self.collector.knowledge_section, "Financial Information")


class TestCollectReturnType(unittest.TestCase):
    def test_collect_returns_a_financial_result(self):
        result = FinancialCollector().collect(
            "Full analysis ahead of quarterly results next week."
        )
        self.assertIsInstance(result, FinancialResult)


class TestReturnedStructureValidity(unittest.TestCase):
    def setUp(self):
        self.result = FinancialCollector().collect(
            "Full analysis ahead of quarterly results next week."
        )

    def test_numeric_fields_are_numbers(self):
        numeric_fields = (
            self.result.revenue,
            self.result.net_profit,
            self.result.eps,
            self.result.book_value,
            self.result.pe_ratio,
            self.result.roe,
            self.result.roce,
            self.result.debt_to_equity,
            self.result.market_capitalization,
            self.result.dividend_yield,
        )
        for value in numeric_fields:
            self.assertIsInstance(value, (int, float))

    def test_financial_year_is_a_non_empty_string(self):
        self.assertIsInstance(self.result.financial_year, str)
        self.assertTrue(self.result.financial_year.strip())

    def test_sources_is_a_non_empty_list_of_strings(self):
        self.assertIsInstance(self.result.sources, list)
        self.assertTrue(len(self.result.sources) > 0)
        self.assertTrue(all(isinstance(source, str) for source in self.result.sources))

    def test_collection_time_is_a_datetime(self):
        self.assertIsInstance(self.result.collection_time, datetime)

    def test_collector_status_is_success(self):
        self.assertEqual(self.result.collector_status, CollectorStatus.SUCCESS)

    def test_each_call_returns_an_independent_result(self):
        first = FinancialCollector().collect("Topic A")
        second = FinancialCollector().collect("Topic B")
        self.assertIsNot(first, second)
        self.assertIsNot(first.sources, second.sources)


class TestInvalidTopicHandling(unittest.TestCase):
    def setUp(self):
        self.collector = FinancialCollector()

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
        registry.register_collector("Financial Information", FinancialCollector)
        factory = CollectorFactory(registry)

        collector = factory.create_collector("Financial Information")
        self.assertIsInstance(collector, FinancialCollector)
        result = collector.collect("Full analysis ahead of quarterly results next week.")
        self.assertIsInstance(result, FinancialResult)


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
            / "financial"
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
