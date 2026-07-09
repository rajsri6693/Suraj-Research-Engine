"""Unit tests for research_engine.collectors.metadata.metadata_collector."""

import unittest
from datetime import datetime, timedelta

from research_engine.collectors.base_collector import BaseCollector
from research_engine.collectors.collector_factory import CollectorFactory
from research_engine.collectors.collector_registry import CollectorRegistry
from research_engine.collectors.metadata.metadata_collector import (
    InvalidResearchTopicError,
    MetadataCollector,
)
from research_engine.collectors.metadata.metadata_result import (
    CollectorStatus,
    MetadataResult,
)


class TestCollectorCreation(unittest.TestCase):
    def test_can_be_instantiated(self):
        collector = MetadataCollector()
        self.assertIsInstance(collector, MetadataCollector)

    def test_is_a_base_collector(self):
        self.assertIsInstance(MetadataCollector(), BaseCollector)


class TestCollectorMetadata(unittest.TestCase):
    def setUp(self):
        self.collector = MetadataCollector()

    def test_collector_name(self):
        self.assertEqual(self.collector.collector_name, "Metadata Collector")

    def test_knowledge_section(self):
        self.assertEqual(self.collector.knowledge_section, "Metadata")


class TestCollectReturnType(unittest.TestCase):
    def test_collect_returns_a_metadata_result(self):
        result = MetadataCollector().collect(
            "Full analysis ahead of quarterly results next week."
        )
        self.assertIsInstance(result, MetadataResult)


class TestReturnedStructureValidity(unittest.TestCase):
    def setUp(self):
        self.topic = "Full analysis ahead of quarterly results next week."
        self.result = MetadataCollector().collect(self.topic)

    def test_text_fields_are_non_empty_strings(self):
        for value in (
            self.result.research_session_id,
            self.result.research_topic,
            self.result.research_profile,
            self.result.research_category,
            self.result.language,
            self.result.research_version,
            self.result.collector_version,
            self.result.workflow_version,
            self.result.runtime_environment,
        ):
            self.assertIsInstance(value, str)
            self.assertTrue(value.strip())

    def test_research_topic_echoes_the_real_input(self):
        self.assertEqual(self.result.research_topic, self.topic)

    def test_started_and_completed_times_are_datetimes_in_order(self):
        self.assertIsInstance(self.result.started_time, datetime)
        self.assertIsInstance(self.result.completed_time, datetime)
        self.assertLessEqual(self.result.started_time, self.result.completed_time)

    def test_execution_duration_matches_started_and_completed_times(self):
        self.assertIsInstance(self.result.execution_duration, timedelta)
        self.assertEqual(
            self.result.execution_duration,
            self.result.completed_time - self.result.started_time,
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
        first = MetadataCollector().collect("Topic A")
        second = MetadataCollector().collect("Topic B")
        self.assertIsNot(first, second)
        self.assertIsNot(first.sources, second.sources)
        self.assertNotEqual(first.research_topic, second.research_topic)


class TestInvalidTopicHandling(unittest.TestCase):
    def setUp(self):
        self.collector = MetadataCollector()

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
        registry.register_collector("Metadata", MetadataCollector)
        factory = CollectorFactory(registry)

        collector = factory.create_collector("Metadata")
        self.assertIsInstance(collector, MetadataCollector)
        result = collector.collect("Full analysis ahead of quarterly results next week.")
        self.assertIsInstance(result, MetadataResult)


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
            / "metadata"
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
