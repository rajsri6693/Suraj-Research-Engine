"""Unit tests for research_engine.collectors.sources.sources_collector."""

import unittest
from datetime import datetime

from research_engine.collectors.base_collector import BaseCollector
from research_engine.collectors.collector_factory import CollectorFactory
from research_engine.collectors.collector_registry import CollectorRegistry
from research_engine.collectors.sources.sources_collector import (
    InvalidResearchTopicError,
    SourcesCollector,
)
from research_engine.collectors.sources.sources_result import (
    CollectorStatus,
    SourceCategory,
    SourcePriority,
    SourcesResult,
)


class TestSourceVocabularies(unittest.TestCase):
    def test_ten_source_categories_defined(self):
        self.assertEqual(len(list(SourceCategory)), 10)

    def test_three_source_priorities_defined(self):
        self.assertEqual(
            {priority.value for priority in SourcePriority},
            {"Primary Source", "Secondary Source", "Fallback Source"},
        )


class TestCollectorCreation(unittest.TestCase):
    def test_can_be_instantiated(self):
        collector = SourcesCollector()
        self.assertIsInstance(collector, SourcesCollector)

    def test_is_a_base_collector(self):
        self.assertIsInstance(SourcesCollector(), BaseCollector)


class TestCollectorMetadata(unittest.TestCase):
    def setUp(self):
        self.collector = SourcesCollector()

    def test_collector_name(self):
        self.assertEqual(self.collector.collector_name, "Sources Collector")

    def test_knowledge_section(self):
        self.assertEqual(self.collector.knowledge_section, "Sources")


class TestCollectReturnType(unittest.TestCase):
    def test_collect_returns_a_sources_result(self):
        result = SourcesCollector().collect(
            "Full analysis ahead of quarterly results next week."
        )
        self.assertIsInstance(result, SourcesResult)


class TestReturnedStructureValidity(unittest.TestCase):
    def setUp(self):
        self.result = SourcesCollector().collect(
            "Full analysis ahead of quarterly results next week."
        )

    def test_text_fields_are_non_empty_strings(self):
        for value in (
            self.result.source_name,
            self.result.source_type,
            self.result.source_reliability,
            self.result.source_language,
            self.result.source_notes,
        ):
            self.assertIsInstance(value, str)
            self.assertTrue(value.strip())

    def test_source_category_is_a_valid_enum_member(self):
        self.assertIsInstance(self.result.source_category, SourceCategory)

    def test_source_priority_is_a_valid_enum_member(self):
        self.assertIsInstance(self.result.source_priority, SourcePriority)

    def test_collection_timestamp_and_collection_time_are_both_datetimes(self):
        self.assertIsInstance(self.result.collection_timestamp, datetime)
        self.assertIsInstance(self.result.collection_time, datetime)

    def test_collection_timestamp_and_collection_time_are_populated_independently(self):
        # Collection Timestamp is when the catalogued source was itself
        # retrieved (a fixed placeholder date here); Collection Time is
        # when this collector ran (effectively "now"). They are distinct
        # fields with different values in this fixture.
        self.assertEqual(self.result.collection_timestamp, datetime(2026, 7, 9))
        self.assertNotEqual(self.result.collection_timestamp, self.result.collection_time)

    def test_sources_is_a_non_empty_list_of_strings(self):
        self.assertIsInstance(self.result.sources, list)
        self.assertTrue(len(self.result.sources) > 0)
        self.assertTrue(all(isinstance(source, str) for source in self.result.sources))

    def test_collector_status_is_success(self):
        self.assertEqual(self.result.collector_status, CollectorStatus.SUCCESS)

    def test_each_call_returns_an_independent_result(self):
        first = SourcesCollector().collect("Topic A")
        second = SourcesCollector().collect("Topic B")
        self.assertIsNot(first, second)
        self.assertIsNot(first.sources, second.sources)


class TestInvalidTopicHandling(unittest.TestCase):
    def setUp(self):
        self.collector = SourcesCollector()

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
        registry.register_collector("Sources", SourcesCollector)
        factory = CollectorFactory(registry)

        collector = factory.create_collector("Sources")
        self.assertIsInstance(collector, SourcesCollector)
        result = collector.collect("Full analysis ahead of quarterly results next week.")
        self.assertIsInstance(result, SourcesResult)


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
            / "sources"
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
