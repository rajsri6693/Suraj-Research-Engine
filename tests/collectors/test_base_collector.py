"""Unit tests for research_engine.collectors.base_collector."""

import unittest

from research_engine.collectors.base_collector import BaseCollector


class IncompleteCollector(BaseCollector):
    """Deliberately implements nothing -- used only to prove BaseCollector
    cannot be instantiated on its own."""


class MinimalCollector(BaseCollector):
    """Implements only the two required properties, inheriting the base
    collect() default so its NotImplementedError behavior can be tested."""

    @property
    def collector_name(self) -> str:
        return "Minimal Test Collector"

    @property
    def knowledge_section(self) -> str:
        return "Financial Information"


class OverridingCollector(BaseCollector):
    """Implements collect() itself, proving the interface is meant to be
    overridden by a concrete collector."""

    @property
    def collector_name(self) -> str:
        return "Overriding Test Collector"

    @property
    def knowledge_section(self) -> str:
        return "Risks"

    def collect(self):
        return "collected"


class TestBaseCollectorIsAbstract(unittest.TestCase):
    def test_base_collector_cannot_be_instantiated_directly(self):
        with self.assertRaises(TypeError):
            BaseCollector()

    def test_subclass_missing_required_properties_cannot_be_instantiated(self):
        with self.assertRaises(TypeError):
            IncompleteCollector()


class TestBaseCollectorInterface(unittest.TestCase):
    def test_minimal_subclass_exposes_collector_name_and_knowledge_section(self):
        collector = MinimalCollector()
        self.assertEqual(collector.collector_name, "Minimal Test Collector")
        self.assertEqual(collector.knowledge_section, "Financial Information")


class TestDefaultCollectRaisesNotImplementedError(unittest.TestCase):
    def test_default_collect_raises_not_implemented_error(self):
        collector = MinimalCollector()
        with self.assertRaises(NotImplementedError):
            collector.collect()

    def test_overriding_collect_no_longer_raises(self):
        collector = OverridingCollector()
        self.assertEqual(collector.collect(), "collected")


if __name__ == "__main__":
    unittest.main()
