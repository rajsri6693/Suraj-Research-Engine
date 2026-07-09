"""Unit tests for research_engine.collectors.collector_registry."""

import unittest

from research_engine.collectors.base_collector import BaseCollector
from research_engine.collectors.collector_registry import (
    CollectorNotFoundError,
    CollectorRegistry,
    DuplicateCollectorError,
)


class FinancialInformationCollector(BaseCollector):
    @property
    def collector_name(self) -> str:
        return "Financial Information Collector"

    @property
    def knowledge_section(self) -> str:
        return "Financial Information"


class RisksCollector(BaseCollector):
    @property
    def collector_name(self) -> str:
        return "Risks Collector"

    @property
    def knowledge_section(self) -> str:
        return "Risks"


class NotACollector:
    """Deliberately not a BaseCollector subclass."""


class TestRegisterCollector(unittest.TestCase):
    def setUp(self):
        self.registry = CollectorRegistry()

    def test_register_collector_makes_it_listed(self):
        self.registry.register_collector(
            "Financial Information", FinancialInformationCollector
        )
        self.assertIn("Financial Information", self.registry.list_collectors())

    def test_register_collector_rejects_non_base_collector_classes(self):
        with self.assertRaises(TypeError):
            self.registry.register_collector("Financial Information", NotACollector)

    def test_register_collector_rejects_a_non_class_value(self):
        with self.assertRaises(TypeError):
            self.registry.register_collector("Financial Information", object())

    def test_duplicate_registration_for_the_same_section_is_rejected(self):
        self.registry.register_collector(
            "Financial Information", FinancialInformationCollector
        )
        with self.assertRaises(DuplicateCollectorError):
            self.registry.register_collector(
                "Financial Information", FinancialInformationCollector
            )

    def test_different_sections_can_be_registered_independently(self):
        self.registry.register_collector(
            "Financial Information", FinancialInformationCollector
        )
        self.registry.register_collector("Risks", RisksCollector)
        self.assertEqual(
            set(self.registry.list_collectors()), {"Financial Information", "Risks"}
        )


class TestGetCollector(unittest.TestCase):
    def setUp(self):
        self.registry = CollectorRegistry()
        self.registry.register_collector(
            "Financial Information", FinancialInformationCollector
        )

    def test_get_collector_returns_the_registered_class(self):
        self.assertIs(
            self.registry.get_collector("Financial Information"),
            FinancialInformationCollector,
        )

    def test_get_collector_raises_for_unregistered_section(self):
        with self.assertRaises(CollectorNotFoundError):
            self.registry.get_collector("Risks")


class TestUnregisterCollector(unittest.TestCase):
    def setUp(self):
        self.registry = CollectorRegistry()
        self.registry.register_collector(
            "Financial Information", FinancialInformationCollector
        )

    def test_unregister_collector_removes_it(self):
        self.registry.unregister_collector("Financial Information")
        self.assertNotIn("Financial Information", self.registry.list_collectors())

    def test_unregister_collector_raises_for_unregistered_section(self):
        with self.assertRaises(CollectorNotFoundError):
            self.registry.unregister_collector("Risks")

    def test_section_can_be_reregistered_after_unregistering(self):
        self.registry.unregister_collector("Financial Information")
        self.registry.register_collector(
            "Financial Information", FinancialInformationCollector
        )
        self.assertIn("Financial Information", self.registry.list_collectors())


class TestListCollectors(unittest.TestCase):
    def test_empty_registry_lists_nothing(self):
        self.assertEqual(CollectorRegistry().list_collectors(), [])


if __name__ == "__main__":
    unittest.main()
