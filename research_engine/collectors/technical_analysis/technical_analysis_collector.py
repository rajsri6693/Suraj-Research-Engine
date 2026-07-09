"""
Technical Analysis Collector

Implements TechnicalAnalysisCollector, per
project_documentation/RESEARCH_COLLECTORS.md and
project_documentation/COLLECTOR_SOURCE_STRATEGY.md. It is responsible
ONLY for collecting the Technical Analysis Knowledge Section and
returning a TechnicalAnalysisResult.

This phase does NOT perform live research. collect() returns a valid
TechnicalAnalysisResult built from placeholder/mock values only -- the
goal is to validate the Collector architecture and the Technical
Analysis data contract, not external data retrieval. It NEVER calls an
API, accesses the internet, verifies data, approves data, accesses a
database, writes SQLite, generates scripts or videos, or calls any other
collector.

Preferred Source Category: Technical Market Data Sources. Fallback
Category: Market Data Providers, per COLLECTOR_SOURCE_STRATEGY.md's
Collector Mapping (Section 4).
"""

from __future__ import annotations

from datetime import datetime

from ..base_collector import BaseCollector
from .technical_analysis_result import (
    CollectorStatus,
    TechnicalAnalysisResult,
    TechnicalChartData,
)


class InvalidResearchTopicError(Exception):
    """Raised when collect() is given an empty or missing Research
    Topic."""


class TechnicalAnalysisCollector(BaseCollector):
    """Collects the Technical Analysis Knowledge Section."""

    @property
    def collector_name(self) -> str:
        return "Technical Analysis Collector"

    @property
    def knowledge_section(self) -> str:
        return "Technical Analysis"

    def collect(self, research_topic: str) -> TechnicalAnalysisResult:
        """Gather Technical Analysis for `research_topic`.

        Input: Research Topic. Output: a TechnicalAnalysisResult.

        This phase returns placeholder/mock values only -- no live
        research, no API call, no internet access. It validates the
        collector's interface and data contract, not real collection.
        """
        if not research_topic or not research_topic.strip():
            raise InvalidResearchTopicError("Research Topic must not be empty.")

        support_levels = [405.0, 390.0]
        resistance_levels = [430.0, 445.0]
        moving_averages = {"50-day": 410.5, "200-day": 395.2}
        rsi = 58.4

        return TechnicalAnalysisResult(
            current_price=418.65,
            support_levels=support_levels,
            resistance_levels=resistance_levels,
            trend="Bullish",
            moving_averages=moving_averages,
            rsi=rsi,
            macd="MACD line above signal line, bullish momentum.",
            volume_analysis="Traded volume above its 30-day average.",
            pattern="Ascending triangle (placeholder)",
            technical_summary=(
                "A placeholder technical summary used to validate the "
                "Technical Analysis Collector's data contract; not the "
                "result of live research."
            ),
            chart_data=self._build_chart_data(moving_averages, support_levels, resistance_levels),
            chart_type="Candlestick",
            indicators_available=[*moving_averages.keys(), "RSI", "MACD"],
            sources=["Technical Market Data Sources (placeholder)"],
            collection_time=datetime.now(),
            collector_status=CollectorStatus.SUCCESS,
        )

    @staticmethod
    def _build_chart_data(moving_averages, support_levels, resistance_levels) -> TechnicalChartData:
        """Reshape this collector's own indicator values into a
        chart-ready Technical Chart Data, per IMP-09D -- reporting the
        same gathered facts in a chart-friendly layout, not generating
        a chart itself."""
        return TechnicalChartData(
            indicator_labels=list(moving_averages.keys()),
            indicator_values=list(moving_averages.values()),
            support_levels=list(support_levels),
            resistance_levels=list(resistance_levels),
        )
