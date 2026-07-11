"""Unit tests for research_engine.runtime.collector_wiring, per
Claude-Prompts/IMP_10I_Research_Runtime.md's Collectors requirement:
"Use the existing Collector Registry and Collector Factory. No
Collector may be called directly from the runtime."
"""

import unittest

from research_engine.api_manager import APIManager
from research_engine.collectors.base_collector import BaseCollector
from research_engine.collectors.collector_factory import CollectorFactory
from research_engine.collectors.collector_registry import CollectorRegistry
from research_engine.collectors.company.company_collector import CompanyCollector
from research_engine.collectors.sector.sector_collector import SectorCollector
from research_engine.planner.research_plan import KnowledgeSection
from research_engine.runtime.collector_wiring import (
    API_MANAGER_AWARE_SECTIONS,
    KNOWN_COLLECTORS,
    build_collector_factory,
    build_collector_registry,
)


class TestBuildCollectorRegistry(unittest.TestCase):
    def test_returns_a_real_collector_registry(self):
        registry = build_collector_registry(APIManager())
        self.assertIsInstance(registry, CollectorRegistry)

    def test_registers_every_known_knowledge_section(self):
        registry = build_collector_registry(APIManager())
        registered = set(registry.list_collectors())
        self.assertEqual(registered, set(KNOWN_COLLECTORS.keys()))

    def test_registers_every_section_the_planner_can_require_or_explains_why_not(self):
        """Every Knowledge Section the Planner's own Knowledge Selection
        Rules can require is either registered here, or is one of the
        two sections research_engine.integration.integration_engine's
        own _KNOWN_COLLECTORS also leaves unregistered (Business
        Overview, Market Data -- no real collector exists for either
        anywhere in this codebase, confirmed during IMP-10I research)."""
        registered = set(KNOWN_COLLECTORS.keys())
        all_sections = {section.value for section in KnowledgeSection}
        unregistered = all_sections - registered
        self.assertEqual(unregistered, {"Business Overview", "Market Data"})

    def test_each_registered_class_is_a_base_collector_subclass(self):
        registry = build_collector_registry(APIManager())
        for section_name in registry.list_collectors():
            collector_class = registry.get_collector(section_name)
            self.assertTrue(issubclass(collector_class, BaseCollector))

    def test_two_calls_return_independent_registries(self):
        manager = APIManager()
        first = build_collector_registry(manager)
        second = build_collector_registry(manager)
        self.assertIsNot(first, second)


class TestAPIManagerThreading(unittest.TestCase):
    """The core wiring requirement: every API-Manager-aware collector's
    zero-arg constructed instance actually carries the shared APIManager
    this registry was built with -- not None, and not a different
    instance."""

    def test_api_manager_aware_collectors_receive_the_shared_instance(self):
        manager = APIManager()
        registry = build_collector_registry(manager)
        for section_name in API_MANAGER_AWARE_SECTIONS:
            collector_class = registry.get_collector(section_name)
            instance = collector_class()
            self.assertIs(
                instance.api_manager,
                manager,
                f"{section_name}'s collector did not receive the shared APIManager",
            )

    def test_non_api_manager_sections_are_registered_unchanged(self):
        """Sector Information (and the other non-API-Manager-aware
        sections) are registered as the exact original class, not a
        bound subclass -- these collectors take no api_manager
        parameter at all."""
        registry = build_collector_registry(APIManager())
        self.assertIs(registry.get_collector("Sector Information"), SectorCollector)

    def test_bound_subclass_preserves_collector_name_and_knowledge_section(self):
        manager = APIManager()
        registry = build_collector_registry(manager)
        collector_class = registry.get_collector("Company Information")
        instance = collector_class()
        self.assertEqual(instance.collector_name, "Company Information Collector")
        self.assertEqual(instance.knowledge_section, "Company Information")

    def test_bound_subclass_is_still_a_real_subclass_of_the_original_collector(self):
        manager = APIManager()
        registry = build_collector_registry(manager)
        collector_class = registry.get_collector("Company Information")
        self.assertTrue(issubclass(collector_class, CompanyCollector))
        instance = collector_class()
        self.assertIsInstance(instance, CompanyCollector)

    def test_two_different_api_managers_produce_two_differently_bound_registries(self):
        manager_a = APIManager()
        manager_b = APIManager()
        registry_a = build_collector_registry(manager_a)
        registry_b = build_collector_registry(manager_b)
        instance_a = registry_a.get_collector("Company Information")()
        instance_b = registry_b.get_collector("Company Information")()
        self.assertIs(instance_a.api_manager, manager_a)
        self.assertIs(instance_b.api_manager, manager_b)
        self.assertIsNot(instance_a.api_manager, instance_b.api_manager)


class TestBuildCollectorFactory(unittest.TestCase):
    def test_returns_a_real_collector_factory(self):
        factory = build_collector_factory(APIManager())
        self.assertIsInstance(factory, CollectorFactory)

    def test_factory_creates_an_api_manager_bound_collector(self):
        manager = APIManager()
        factory = build_collector_factory(manager)
        collector = factory.create_collector("Financial Information")
        self.assertIs(collector.api_manager, manager)

    def test_factory_is_available_reflects_the_known_collectors_map(self):
        factory = build_collector_factory(APIManager())
        for section_name in KNOWN_COLLECTORS:
            self.assertTrue(factory.is_available(section_name))
        self.assertFalse(factory.is_available("Business Overview"))
        self.assertFalse(factory.is_available("Market Data"))


if __name__ == "__main__":
    unittest.main()
