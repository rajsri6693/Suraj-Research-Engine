"""Unit tests for research_engine.collectors.collector_factory."""

import unittest

from research_engine.collectors.base_collector import BaseCollector
from research_engine.collectors.collector_factory import (
    CollectorFactory,
    CollectorUnavailableError,
)
from research_engine.collectors.collector_registry import CollectorRegistry


class FinancialInformationCollector(BaseCollector):
    @property
    def collector_name(self) -> str:
        return "Financial Information Collector"

    @property
    def knowledge_section(self) -> str:
        return "Financial Information"


class TestIsAvailable(unittest.TestCase):
    def setUp(self):
        self.registry = CollectorRegistry()
        self.registry.register_collector(
            "Financial Information", FinancialInformationCollector
        )
        self.factory = CollectorFactory(self.registry)

    def test_available_for_a_registered_section(self):
        self.assertTrue(self.factory.is_available("Financial Information"))

    def test_unavailable_for_an_unregistered_section(self):
        self.assertFalse(self.factory.is_available("Risks"))


class TestCreateCollector(unittest.TestCase):
    def setUp(self):
        self.registry = CollectorRegistry()
        self.registry.register_collector(
            "Financial Information", FinancialInformationCollector
        )
        self.factory = CollectorFactory(self.registry)

    def test_creates_an_instance_of_the_registered_class(self):
        collector = self.factory.create_collector("Financial Information")
        self.assertIsInstance(collector, FinancialInformationCollector)
        self.assertEqual(collector.collector_name, "Financial Information Collector")
        self.assertEqual(collector.knowledge_section, "Financial Information")

    def test_each_call_returns_a_fresh_instance(self):
        first = self.factory.create_collector("Financial Information")
        second = self.factory.create_collector("Financial Information")
        self.assertIsNot(first, second)

    def test_created_collector_still_raises_on_collect(self):
        # The framework registers a collector class, but this phase
        # implements no real collection logic -- collect() still raises.
        collector = self.factory.create_collector("Financial Information")
        with self.assertRaises(NotImplementedError):
            collector.collect()


class TestFactoryInvalidCollectorHandling(unittest.TestCase):
    def test_create_collector_raises_for_unregistered_section(self):
        factory = CollectorFactory(CollectorRegistry())
        with self.assertRaises(CollectorUnavailableError):
            factory.create_collector("Financial Information")

    def test_create_collector_after_unregistering_raises(self):
        registry = CollectorRegistry()
        registry.register_collector(
            "Financial Information", FinancialInformationCollector
        )
        factory = CollectorFactory(registry)
        registry.unregister_collector("Financial Information")
        with self.assertRaises(CollectorUnavailableError):
            factory.create_collector("Financial Information")


if __name__ == "__main__":
    unittest.main()
