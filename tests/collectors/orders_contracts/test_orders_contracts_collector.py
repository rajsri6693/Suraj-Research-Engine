"""Unit tests for
research_engine.collectors.orders_contracts.orders_contracts_collector."""

import unittest
from datetime import datetime

from research_engine.collectors.base_collector import BaseCollector
from research_engine.collectors.collector_factory import CollectorFactory
from research_engine.collectors.collector_registry import CollectorRegistry
from research_engine.collectors.orders_contracts.order_contract_result import (
    CollectorStatus,
    OrderContractResult,
)
from research_engine.collectors.orders_contracts.orders_contracts_collector import (
    InvalidResearchTopicError,
    OrdersContractsCollector,
)


class TestCollectorCreation(unittest.TestCase):
    def test_can_be_instantiated(self):
        collector = OrdersContractsCollector()
        self.assertIsInstance(collector, OrdersContractsCollector)

    def test_is_a_base_collector(self):
        self.assertIsInstance(OrdersContractsCollector(), BaseCollector)


class TestCollectorMetadata(unittest.TestCase):
    def setUp(self):
        self.collector = OrdersContractsCollector()

    def test_collector_name(self):
        self.assertEqual(self.collector.collector_name, "Orders & Contracts Collector")

    def test_knowledge_section(self):
        self.assertEqual(self.collector.knowledge_section, "Orders & Contracts")


class TestCollectReturnType(unittest.TestCase):
    def test_collect_returns_an_order_contract_result(self):
        result = OrdersContractsCollector().collect(
            "Full analysis ahead of quarterly results next week."
        )
        self.assertIsInstance(result, OrderContractResult)


class TestReturnedStructureValidity(unittest.TestCase):
    def setUp(self):
        self.result = OrdersContractsCollector().collect(
            "Full analysis ahead of quarterly results next week."
        )

    def test_text_fields_are_non_empty_strings(self):
        for value in (
            self.result.order_title,
            self.result.order_type,
            self.result.customer_name,
            self.result.currency,
            self.result.execution_period,
            self.result.order_status,
            self.result.related_company,
        ):
            self.assertIsInstance(value, str)
            self.assertTrue(value.strip())

    def test_contract_value_is_a_positive_number(self):
        self.assertIsInstance(self.result.contract_value, (int, float))
        self.assertGreater(self.result.contract_value, 0)

    def test_announcement_date_is_a_datetime(self):
        self.assertIsInstance(self.result.announcement_date, datetime)

    def test_sources_is_a_non_empty_list_of_strings(self):
        self.assertIsInstance(self.result.sources, list)
        self.assertTrue(len(self.result.sources) > 0)
        self.assertTrue(all(isinstance(source, str) for source in self.result.sources))

    def test_collection_time_is_a_datetime(self):
        self.assertIsInstance(self.result.collection_time, datetime)

    def test_collector_status_is_success(self):
        self.assertEqual(self.result.collector_status, CollectorStatus.SUCCESS)

    def test_each_call_returns_an_independent_result(self):
        first = OrdersContractsCollector().collect("Topic A")
        second = OrdersContractsCollector().collect("Topic B")
        self.assertIsNot(first, second)
        self.assertIsNot(first.sources, second.sources)


class TestInvalidTopicHandling(unittest.TestCase):
    def setUp(self):
        self.collector = OrdersContractsCollector()

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
        registry.register_collector("Orders & Contracts", OrdersContractsCollector)
        factory = CollectorFactory(registry)

        collector = factory.create_collector("Orders & Contracts")
        self.assertIsInstance(collector, OrdersContractsCollector)
        result = collector.collect("Full analysis ahead of quarterly results next week.")
        self.assertIsInstance(result, OrderContractResult)


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
            / "orders_contracts"
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
