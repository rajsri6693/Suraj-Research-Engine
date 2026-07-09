"""Unit tests for research_engine.collectors.company.company_collector."""

import unittest
from datetime import datetime

from research_engine.collectors.base_collector import BaseCollector
from research_engine.collectors.collector_factory import CollectorFactory
from research_engine.collectors.collector_registry import CollectorRegistry
from research_engine.collectors.company.company_collector import (
    CompanyCollector,
    InvalidResearchTopicError,
)
from research_engine.collectors.company.company_result import (
    CollectorStatus,
    CompanyResult,
)


class TestCollectorCreation(unittest.TestCase):
    def test_can_be_instantiated(self):
        collector = CompanyCollector()
        self.assertIsInstance(collector, CompanyCollector)

    def test_is_a_base_collector(self):
        self.assertIsInstance(CompanyCollector(), BaseCollector)


class TestCollectorMetadata(unittest.TestCase):
    def setUp(self):
        self.collector = CompanyCollector()

    def test_collector_name(self):
        self.assertEqual(self.collector.collector_name, "Company Information Collector")

    def test_knowledge_section(self):
        self.assertEqual(self.collector.knowledge_section, "Company Information")


class TestCollectReturnType(unittest.TestCase):
    def test_collect_returns_a_company_result(self):
        result = CompanyCollector().collect("Full analysis of Sample Manufacturing Ltd.")
        self.assertIsInstance(result, CompanyResult)


class TestReturnedStructureValidity(unittest.TestCase):
    def setUp(self):
        self.result = CompanyCollector().collect("Full analysis of Sample Manufacturing Ltd.")

    def test_company_name_is_a_non_empty_string(self):
        self.assertIsInstance(self.result.company_name, str)
        self.assertTrue(self.result.company_name.strip())

    def test_sector_industry_headquarters_and_description_are_strings(self):
        self.assertIsInstance(self.result.sector, str)
        self.assertIsInstance(self.result.industry, str)
        self.assertIsInstance(self.result.headquarters, str)
        self.assertIsInstance(self.result.business_description, str)
        self.assertTrue(self.result.business_description.strip())

    def test_official_website_is_a_non_empty_string(self):
        self.assertIsInstance(self.result.official_website, str)
        self.assertTrue(self.result.official_website.strip())

    def test_founded_year_is_an_int_or_none(self):
        self.assertTrue(
            self.result.founded_year is None or isinstance(self.result.founded_year, int)
        )

    def test_symbols_and_isin_are_str_or_none(self):
        for value in (self.result.nse_symbol, self.result.bse_symbol, self.result.isin):
            self.assertTrue(value is None or isinstance(value, str))

    def test_sources_is_a_non_empty_list_of_strings(self):
        self.assertIsInstance(self.result.sources, list)
        self.assertTrue(len(self.result.sources) > 0)
        self.assertTrue(all(isinstance(source, str) for source in self.result.sources))

    def test_collection_time_is_a_datetime(self):
        self.assertIsInstance(self.result.collection_time, datetime)

    def test_collector_status_is_success(self):
        self.assertEqual(self.result.collector_status, CollectorStatus.SUCCESS)

    def test_each_call_returns_an_independent_result(self):
        first = CompanyCollector().collect("Topic A")
        second = CompanyCollector().collect("Topic B")
        self.assertIsNot(first, second)
        self.assertIsNot(first.sources, second.sources)


class TestInvalidTopicHandling(unittest.TestCase):
    def setUp(self):
        self.collector = CompanyCollector()

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
        registry.register_collector("Company Information", CompanyCollector)
        factory = CollectorFactory(registry)

        collector = factory.create_collector("Company Information")
        self.assertIsInstance(collector, CompanyCollector)
        result = collector.collect("Full analysis of Sample Manufacturing Ltd.")
        self.assertIsInstance(result, CompanyResult)


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
            / "company"
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
