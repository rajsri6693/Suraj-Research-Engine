"""Unit tests for
research_engine.collectors.historical_price.historical_price_collector."""

import unittest
from datetime import datetime

from research_engine.collectors.base_collector import BaseCollector
from research_engine.collectors.collector_factory import CollectorFactory
from research_engine.collectors.collector_registry import CollectorRegistry
from research_engine.collectors.historical_price.historical_price_collector import (
    HistoricalPriceCollector,
    InvalidResearchTopicError,
)
from research_engine.collectors.historical_price.historical_price_result import (
    CollectorStatus,
    HistoricalPriceResult,
    OHLCRecord,
)


class TestCollectorCreation(unittest.TestCase):
    def test_can_be_instantiated(self):
        collector = HistoricalPriceCollector()
        self.assertIsInstance(collector, HistoricalPriceCollector)

    def test_is_a_base_collector(self):
        self.assertIsInstance(HistoricalPriceCollector(), BaseCollector)


class TestCollectorMetadata(unittest.TestCase):
    def setUp(self):
        self.collector = HistoricalPriceCollector()

    def test_collector_name(self):
        self.assertEqual(self.collector.collector_name, "Historical Price Collector")

    def test_knowledge_section(self):
        self.assertEqual(self.collector.knowledge_section, "Historical Price (OHLC)")


class TestCollectReturnType(unittest.TestCase):
    def test_collect_returns_a_historical_price_result(self):
        result = HistoricalPriceCollector().collect(
            "Full analysis ahead of quarterly results next week."
        )
        self.assertIsInstance(result, HistoricalPriceResult)


class TestReturnedStructureValidity(unittest.TestCase):
    def setUp(self):
        self.result = HistoricalPriceCollector().collect(
            "Full analysis ahead of quarterly results next week."
        )

    def test_symbol_exchange_and_timeframe_are_non_empty_strings(self):
        for value in (self.result.symbol, self.result.exchange, self.result.timeframe):
            self.assertIsInstance(value, str)
            self.assertTrue(value.strip())

    def test_start_and_end_dates_are_datetimes_in_order(self):
        self.assertIsInstance(self.result.start_date, datetime)
        self.assertIsInstance(self.result.end_date, datetime)
        self.assertLessEqual(self.result.start_date, self.result.end_date)

    def test_ohlc_records_is_a_non_empty_list_of_ohlc_records(self):
        self.assertIsInstance(self.result.ohlc_records, list)
        self.assertTrue(len(self.result.ohlc_records) > 0)
        for record in self.result.ohlc_records:
            self.assertIsInstance(record, OHLCRecord)
            self.assertIsInstance(record.date, datetime)
            for price in (record.open, record.high, record.low, record.close):
                self.assertIsInstance(price, (int, float))
            self.assertIsInstance(record.volume, int)

    def test_high_is_never_below_low_in_any_record(self):
        for record in self.result.ohlc_records:
            self.assertGreaterEqual(record.high, record.low)

    def test_total_trading_days_matches_record_count(self):
        self.assertEqual(self.result.total_trading_days, len(self.result.ohlc_records))

    def test_adjusted_prices_is_a_bool(self):
        self.assertIsInstance(self.result.adjusted_prices, bool)

    def test_sources_is_a_non_empty_list_of_strings(self):
        self.assertIsInstance(self.result.sources, list)
        self.assertTrue(len(self.result.sources) > 0)
        self.assertTrue(all(isinstance(source, str) for source in self.result.sources))

    def test_collection_time_is_a_datetime(self):
        self.assertIsInstance(self.result.collection_time, datetime)

    def test_collector_status_is_success(self):
        self.assertEqual(self.result.collector_status, CollectorStatus.SUCCESS)

    def test_each_call_returns_an_independent_result(self):
        first = HistoricalPriceCollector().collect("Topic A")
        second = HistoricalPriceCollector().collect("Topic B")
        self.assertIsNot(first, second)
        self.assertIsNot(first.ohlc_records, second.ohlc_records)
        self.assertIsNot(first.sources, second.sources)


class TestInvalidTopicHandling(unittest.TestCase):
    def setUp(self):
        self.collector = HistoricalPriceCollector()

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
        registry.register_collector("Historical Price (OHLC)", HistoricalPriceCollector)
        factory = CollectorFactory(registry)

        collector = factory.create_collector("Historical Price (OHLC)")
        self.assertIsInstance(collector, HistoricalPriceCollector)
        result = collector.collect("Full analysis ahead of quarterly results next week.")
        self.assertIsInstance(result, HistoricalPriceResult)


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
            / "historical_price"
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
