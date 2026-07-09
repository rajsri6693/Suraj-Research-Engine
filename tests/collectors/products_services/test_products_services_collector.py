"""Unit tests for
research_engine.collectors.products_services.products_services_collector."""

import unittest
from datetime import datetime

from research_engine.collectors.base_collector import BaseCollector
from research_engine.collectors.collector_factory import CollectorFactory
from research_engine.collectors.collector_registry import CollectorRegistry
from research_engine.collectors.products_services.products_services_collector import (
    InvalidResearchTopicError,
    ProductsServicesCollector,
)
from research_engine.collectors.products_services.products_services_result import (
    CollectorStatus,
    ProductsServicesResult,
)


class TestCollectorCreation(unittest.TestCase):
    def test_can_be_instantiated(self):
        collector = ProductsServicesCollector()
        self.assertIsInstance(collector, ProductsServicesCollector)

    def test_is_a_base_collector(self):
        self.assertIsInstance(ProductsServicesCollector(), BaseCollector)


class TestCollectorMetadata(unittest.TestCase):
    def setUp(self):
        self.collector = ProductsServicesCollector()

    def test_collector_name(self):
        self.assertEqual(
            self.collector.collector_name, "Products & Services Collector"
        )

    def test_knowledge_section(self):
        self.assertEqual(self.collector.knowledge_section, "Products & Services")


class TestCollectReturnType(unittest.TestCase):
    def test_collect_returns_a_products_services_result(self):
        result = ProductsServicesCollector().collect(
            "Full analysis ahead of quarterly results next week."
        )
        self.assertIsInstance(result, ProductsServicesResult)


class TestReturnedStructureValidity(unittest.TestCase):
    def setUp(self):
        self.result = ProductsServicesCollector().collect(
            "Full analysis ahead of quarterly results next week."
        )

    def test_company_name_and_business_summary_are_non_empty_strings(self):
        for value in (self.result.company_name, self.result.business_summary):
            self.assertIsInstance(value, str)
            self.assertTrue(value.strip())

    def test_list_fields_are_lists_of_strings(self):
        for value in (
            self.result.products,
            self.result.services,
            self.result.business_segments,
            self.result.major_brands,
            self.result.key_customers,
            self.result.geographic_presence,
        ):
            self.assertIsInstance(value, list)
            self.assertTrue(len(value) > 0)
            self.assertTrue(all(isinstance(item, str) for item in value))

    def test_revenue_segments_is_a_dict_of_floats(self):
        self.assertIsInstance(self.result.revenue_segments, dict)
        self.assertTrue(len(self.result.revenue_segments) > 0)
        for label, share in self.result.revenue_segments.items():
            self.assertIsInstance(label, str)
            self.assertIsInstance(share, (int, float))

    def test_sources_is_a_non_empty_list_of_strings(self):
        self.assertIsInstance(self.result.sources, list)
        self.assertTrue(len(self.result.sources) > 0)
        self.assertTrue(all(isinstance(source, str) for source in self.result.sources))

    def test_collection_time_is_a_datetime(self):
        self.assertIsInstance(self.result.collection_time, datetime)

    def test_collector_status_is_success(self):
        self.assertEqual(self.result.collector_status, CollectorStatus.SUCCESS)

    def test_each_call_returns_an_independent_result(self):
        first = ProductsServicesCollector().collect("Topic A")
        second = ProductsServicesCollector().collect("Topic B")
        self.assertIsNot(first, second)
        self.assertIsNot(first.products, second.products)
        self.assertIsNot(first.revenue_segments, second.revenue_segments)
        self.assertIsNot(first.sources, second.sources)


class TestInvalidTopicHandling(unittest.TestCase):
    def setUp(self):
        self.collector = ProductsServicesCollector()

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
        registry.register_collector("Products & Services", ProductsServicesCollector)
        factory = CollectorFactory(registry)

        collector = factory.create_collector("Products & Services")
        self.assertIsInstance(collector, ProductsServicesCollector)
        result = collector.collect("Full analysis ahead of quarterly results next week.")
        self.assertIsInstance(result, ProductsServicesResult)


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
            / "products_services"
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
