"""Unit tests for
research_engine.collectors.technical_analysis.technical_analysis_collector."""

import unittest
from datetime import datetime

from research_engine.collectors.base_collector import BaseCollector
from research_engine.collectors.collector_factory import CollectorFactory
from research_engine.collectors.collector_registry import CollectorRegistry
from research_engine.collectors.technical_analysis.technical_analysis_collector import (
    InvalidResearchTopicError,
    TechnicalAnalysisCollector,
)
from research_engine.collectors.technical_analysis.technical_analysis_result import (
    CollectorStatus,
    TechnicalAnalysisResult,
)


class TestCollectorCreation(unittest.TestCase):
    def test_can_be_instantiated(self):
        collector = TechnicalAnalysisCollector()
        self.assertIsInstance(collector, TechnicalAnalysisCollector)

    def test_is_a_base_collector(self):
        self.assertIsInstance(TechnicalAnalysisCollector(), BaseCollector)


class TestCollectorMetadata(unittest.TestCase):
    def setUp(self):
        self.collector = TechnicalAnalysisCollector()

    def test_collector_name(self):
        self.assertEqual(
            self.collector.collector_name, "Technical Analysis Collector"
        )

    def test_knowledge_section(self):
        self.assertEqual(self.collector.knowledge_section, "Technical Analysis")


class TestCollectReturnType(unittest.TestCase):
    def test_collect_returns_a_technical_analysis_result(self):
        result = TechnicalAnalysisCollector().collect(
            "Full analysis ahead of quarterly results next week."
        )
        self.assertIsInstance(result, TechnicalAnalysisResult)


class TestReturnedStructureValidity(unittest.TestCase):
    def setUp(self):
        self.result = TechnicalAnalysisCollector().collect(
            "Full analysis ahead of quarterly results next week."
        )

    def test_current_price_and_rsi_are_numbers(self):
        self.assertIsInstance(self.result.current_price, (int, float))
        self.assertIsInstance(self.result.rsi, (int, float))

    def test_support_and_resistance_levels_are_lists_of_numbers(self):
        for levels in (self.result.support_levels, self.result.resistance_levels):
            self.assertIsInstance(levels, list)
            self.assertTrue(len(levels) > 0)
            self.assertTrue(all(isinstance(value, (int, float)) for value in levels))

    def test_moving_averages_is_a_dict_of_floats(self):
        self.assertIsInstance(self.result.moving_averages, dict)
        self.assertTrue(len(self.result.moving_averages) > 0)
        for label, value in self.result.moving_averages.items():
            self.assertIsInstance(label, str)
            self.assertIsInstance(value, (int, float))

    def test_text_fields_are_non_empty_strings(self):
        for value in (
            self.result.trend,
            self.result.macd,
            self.result.volume_analysis,
            self.result.pattern,
            self.result.technical_summary,
        ):
            self.assertIsInstance(value, str)
            self.assertTrue(value.strip())

    def test_sources_is_a_non_empty_list_of_strings(self):
        self.assertIsInstance(self.result.sources, list)
        self.assertTrue(len(self.result.sources) > 0)
        self.assertTrue(all(isinstance(source, str) for source in self.result.sources))

    def test_collection_time_is_a_datetime(self):
        self.assertIsInstance(self.result.collection_time, datetime)

    def test_collector_status_is_success(self):
        self.assertEqual(self.result.collector_status, CollectorStatus.SUCCESS)

    def test_each_call_returns_an_independent_result(self):
        first = TechnicalAnalysisCollector().collect("Topic A")
        second = TechnicalAnalysisCollector().collect("Topic B")
        self.assertIsNot(first, second)
        self.assertIsNot(first.support_levels, second.support_levels)
        self.assertIsNot(first.moving_averages, second.moving_averages)
        self.assertIsNot(first.sources, second.sources)


class TestInvalidTopicHandling(unittest.TestCase):
    def setUp(self):
        self.collector = TechnicalAnalysisCollector()

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
        registry.register_collector("Technical Analysis", TechnicalAnalysisCollector)
        factory = CollectorFactory(registry)

        collector = factory.create_collector("Technical Analysis")
        self.assertIsInstance(collector, TechnicalAnalysisCollector)
        result = collector.collect(
            "Full analysis ahead of quarterly results next week."
        )
        self.assertIsInstance(result, TechnicalAnalysisResult)


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
            / "technical_analysis"
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
