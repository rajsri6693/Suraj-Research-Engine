"""Unit tests for research_engine.chart.chart_generator."""

import unittest
from datetime import datetime

from research_engine.chart.chart_generator import ChartGenerator, GeneratedChart
from research_engine.collectors.historical_price.historical_price_collector import (
    HistoricalPriceCollector,
)
from research_engine.collectors.historical_price.historical_price_result import (
    ChartDataset,
)
from research_engine.collectors.technical_analysis.technical_analysis_collector import (
    TechnicalAnalysisCollector,
)
from research_engine.collectors.technical_analysis.technical_analysis_result import (
    TechnicalChartData,
)


def make_generated_chart() -> GeneratedChart:
    historical_price_result = HistoricalPriceCollector().collect(
        "Full analysis ahead of quarterly results next week."
    )
    technical_analysis_result = TechnicalAnalysisCollector().collect(
        "Full analysis ahead of quarterly results next week."
    )
    return ChartGenerator().generate(historical_price_result, technical_analysis_result)


class TestChartGeneratorReturnType(unittest.TestCase):
    def test_generate_returns_a_generated_chart(self):
        self.assertIsInstance(make_generated_chart(), GeneratedChart)


class TestGeneratedChartStructureValidity(unittest.TestCase):
    def setUp(self):
        self.historical_price_result = HistoricalPriceCollector().collect(
            "Full analysis ahead of quarterly results next week."
        )
        self.technical_analysis_result = TechnicalAnalysisCollector().collect(
            "Full analysis ahead of quarterly results next week."
        )
        self.chart = ChartGenerator().generate(
            self.historical_price_result, self.technical_analysis_result
        )

    def test_symbol_and_timeframe_come_from_historical_price_result(self):
        self.assertEqual(self.chart.symbol, self.historical_price_result.symbol)
        self.assertEqual(self.chart.timeframe, self.historical_price_result.timeframe)

    def test_chart_type_comes_from_technical_analysis_result(self):
        self.assertEqual(self.chart.chart_type, self.technical_analysis_result.chart_type)

    def test_price_dataset_is_the_historical_price_results_chart_dataset(self):
        self.assertIsInstance(self.chart.price_dataset, ChartDataset)
        self.assertEqual(
            self.chart.price_dataset, self.historical_price_result.chart_dataset
        )

    def test_indicator_data_is_the_technical_analysis_results_chart_data(self):
        self.assertIsInstance(self.chart.indicator_data, TechnicalChartData)
        self.assertEqual(
            self.chart.indicator_data, self.technical_analysis_result.chart_data
        )

    def test_indicators_available_matches_technical_analysis_result(self):
        self.assertEqual(
            self.chart.indicators_available,
            self.technical_analysis_result.indicators_available,
        )
        self.assertIsNot(
            self.chart.indicators_available,
            self.technical_analysis_result.indicators_available,
        )

    def test_generated_time_is_a_datetime(self):
        self.assertIsInstance(self.chart.generated_time, datetime)

    def test_each_call_returns_an_independent_generated_chart(self):
        first = make_generated_chart()
        second = make_generated_chart()
        self.assertIsNot(first, second)


class TestChartGeneratorProducesNoImageOrMarkup(unittest.TestCase):
    """DO NOT: generate images, call external chart services, use
    JavaScript, use React, generate HTML, generate PNG -- per
    IMP-09D. A GeneratedChart carries only plain data fields; none of
    its own field values are ever raw HTML/JS/PNG/image bytes."""

    def test_generated_chart_carries_no_html_or_script_markup(self):
        chart = make_generated_chart()
        self.assertNotIn("<", chart.chart_type)
        for label in chart.price_dataset.labels:
            self.assertNotIn("<", label)


class TestNoForeignOrExternalChartDependencies(unittest.TestCase):
    def test_only_standard_library_and_intra_engine_imports(self):
        import ast
        import pathlib

        allowed_stdlib = {"dataclasses", "datetime", "enum", "typing", "__future__"}
        allowed_prefixes = ("research_engine.collectors.",)
        forbidden_modules = {
            "http",
            "http.client",
            "urllib",
            "urllib.request",
            "requests",
            "socket",
            "sqlite3",
            "matplotlib",
            "plotly",
            "seaborn",
            "bokeh",
            "ai",
            "openai",
            "anthropic",
        }

        package_dir = (
            pathlib.Path(__file__).resolve().parents[2]
            / "research_engine"
            / "chart"
        )
        for module_path in package_dir.glob("*.py"):
            tree = ast.parse(module_path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    if node.level > 0:
                        continue  # relative import within the chart package
                    module = node.module or ""
                    self.assertNotIn(module, forbidden_modules)
                    self.assertTrue(
                        module in allowed_stdlib
                        or module.startswith(allowed_prefixes),
                        f"{module_path.name}: unexpected import '{module}'",
                    )
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        top = alias.name.split(".")[0]
                        self.assertNotIn(top, forbidden_modules)
                        self.assertTrue(
                            top in allowed_stdlib
                            or alias.name.startswith(allowed_prefixes),
                            f"{module_path.name}: unexpected import '{alias.name}'",
                        )


if __name__ == "__main__":
    unittest.main()
