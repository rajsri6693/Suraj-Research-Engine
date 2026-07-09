"""
Chart Generator

Implements ChartGenerator, which turns a Historical Price Collector's
own Chart Dataset and a Technical Analysis Collector's own Chart Type
and Chart Data into one combined, chart-ready GeneratedChart, per
Claude-Prompts/IMP_09D_Chart_Support.md.

This module NEVER renders an image, calls an external chart library or
service, generates HTML/JavaScript/React, or produces a PNG -- it only
reshapes structured data the two collectors already gathered into one
combined, chart-ready structure. It NEVER calls an API, accesses the
internet, verifies data, approves data, or accesses a database.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List

from research_engine.collectors.historical_price.historical_price_result import (
    ChartDataset,
    HistoricalPriceResult,
)
from research_engine.collectors.technical_analysis.technical_analysis_result import (
    TechnicalAnalysisResult,
    TechnicalChartData,
)


@dataclass
class GeneratedChart:
    """The chart-ready data Chart Generator produces for one company,
    combining the Historical Price Collector's own Chart Dataset with
    the Technical Analysis Collector's own Chart Type and Chart Data.

    Structured data only -- no image, HTML, or external chart library
    is ever involved in producing it.
    """

    symbol: str
    timeframe: str
    chart_type: str
    price_dataset: ChartDataset
    indicator_data: TechnicalChartData
    indicators_available: List[str]
    generated_time: datetime


class ChartGenerator:
    """Generates chart-ready data from a Historical Price Result and a
    Technical Analysis Result.

    Never fetches data itself, never calls either collector, and never
    renders an image -- it only reshapes the two results it is given.
    """

    def generate(
        self,
        historical_price_result: HistoricalPriceResult,
        technical_analysis_result: TechnicalAnalysisResult,
    ) -> GeneratedChart:
        """Combine `historical_price_result` and
        `technical_analysis_result` into one GeneratedChart."""
        return GeneratedChart(
            symbol=historical_price_result.symbol,
            timeframe=historical_price_result.timeframe,
            chart_type=technical_analysis_result.chart_type,
            price_dataset=historical_price_result.chart_dataset,
            indicator_data=technical_analysis_result.chart_data,
            indicators_available=list(technical_analysis_result.indicators_available),
            generated_time=datetime.now(),
        )
