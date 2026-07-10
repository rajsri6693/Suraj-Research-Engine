"""
Technical Analysis Collector

Implements TechnicalAnalysisCollector, per
project_documentation/RESEARCH_COLLECTORS.md and
project_documentation/COLLECTOR_SOURCE_STRATEGY.md. It is responsible
ONLY for collecting the Technical Analysis Knowledge Section and
returning a TechnicalAnalysisResult.

Per Claude-Prompts/IMP_10D_Alpha_Vantage_Integration.md, this collector
may optionally be given an APIManager (research_engine/api_manager/)
for Market & Technical Category requests -- RSI is Primary Provider
Alpha Vantage's operation for this section, per
API_MANAGER_ARCHITECTURE.md Section 2/3 (this collector requests
"RSI"). Without an APIManager (the default), collect() returns the
same placeholder/mock TechnicalAnalysisResult as every prior phase, so
every existing caller and test is unaffected. When one is given,
collect() requests through it exclusively -- it NEVER calls Alpha
Vantage, Twelve Data, or any provider directly, per IMP-10D's
Collectors rule.

When Alpha Vantage itself serves the request with at least one real
RSI value, collect() maps the most recent value onto
TechnicalAnalysisResult.rsi and rebuilds chart_data's indicator series
from the real RSI time series (dates as labels, RSI values). The
remaining fields (support_levels, resistance_levels, trend,
moving_averages, macd, volume_analysis, pattern, technical_summary)
come from separate Alpha Vantage operations (SMA/EMA/MACD, not called
by this collector) or are not derivable from RSI data at all, so they
are deliberately left as placeholder values rather than fabricated --
combining multiple Alpha Vantage operations into one collector call is
future work outside this phase's scope. Per
Claude-Prompts/IMP_10E_Twelve_Data_Integration.md, this Alpha-Vantage-
shaped mapping is intentionally NOT extended to Twelve Data (now real,
the Backup Provider) -- failover must happen only inside APIManager,
never inside a Collector, so this module has no Twelve Data-specific
code at all and never will. When the Backup Provider serves the
request instead (Twelve Data's own real response, shaped differently
from Alpha Vantage's), or Alpha Vantage returns no data for the
symbol, every field keeps its placeholder value and only
Sources/Collector Status reflect the real outcome.

It NEVER accesses the internet itself, verifies data, approves data,
accesses a database, writes SQLite, generates scripts or videos, or
calls any other collector.

Preferred Source Category: Technical Market Data Sources. Fallback
Category: Market Data Providers, per COLLECTOR_SOURCE_STRATEGY.md's
Collector Mapping (Section 4).
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from ...api_manager import APIManager, Category, ProviderName
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

    AV_OPERATION = "RSI"

    def __init__(self, api_manager: Optional[APIManager] = None) -> None:
        self.api_manager = api_manager

    @property
    def collector_name(self) -> str:
        return "Technical Analysis Collector"

    @property
    def knowledge_section(self) -> str:
        return "Technical Analysis"

    def collect(self, research_topic: str) -> TechnicalAnalysisResult:
        """Gather Technical Analysis for `research_topic`.

        Input: Research Topic. Output: a TechnicalAnalysisResult.

        Without an APIManager, returns placeholder/mock values only, as
        every prior phase did. With one, requests through it
        exclusively and reflects the real outcome onto the same
        placeholder shape -- see this module's docstring.
        """
        if not research_topic or not research_topic.strip():
            raise InvalidResearchTopicError("Research Topic must not be empty.")

        support_levels = [405.0, 390.0]
        resistance_levels = [430.0, 445.0]
        moving_averages = {"50-day": 410.5, "200-day": 395.2}
        rsi = 58.4

        result = TechnicalAnalysisResult(
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

        if self.api_manager is None:
            return result

        api_result = self.api_manager.request(
            Category.MARKET_TECHNICAL,
            self.AV_OPERATION,
            {"symbol": research_topic},
            collector_name=self.collector_name,
        )
        rsi_series = self._alpha_vantage_rsi_series(api_result)

        if api_result.success and (rsi_series is not None or api_result.provider_name != ProviderName.ALPHA_VANTAGE):
            result.sources = [f"{api_result.provider_name.value} ({api_result.served_by.value})"]
            result.collector_status = CollectorStatus.SUCCESS
            if rsi_series is not None:
                dates_newest_first = sorted(rsi_series.keys(), reverse=True)
                result.rsi = rsi_series[dates_newest_first[0]]
                dates_oldest_first = list(reversed(dates_newest_first))
                result.chart_data = TechnicalChartData(
                    indicator_labels=dates_oldest_first,
                    indicator_values=[rsi_series[date] for date in dates_oldest_first],
                    support_levels=list(support_levels),
                    resistance_levels=list(resistance_levels),
                )
                result.indicators_available = ["RSI"]
        else:
            # Either the API call itself failed, or Alpha Vantage
            # succeeded but returned no data for this symbol -- either
            # way, no real Collected Data exists for this section, per
            # COLLECTOR_SOURCE_STRATEGY.md's Missing Source Rules.
            result.sources = []
            result.collector_status = CollectorStatus.FAILED

        return result

    @staticmethod
    def _alpha_vantage_rsi_series(api_result) -> Optional[dict]:
        """Parse Alpha Vantage's live "Technical Analysis: RSI"
        response (date -> {"RSI": value}, value as a string) into a
        plain {date_str: float} mapping -- or None if this result did
        not come from Alpha Vantage, or it returned no series data."""
        if not api_result.success or api_result.provider_name != ProviderName.ALPHA_VANTAGE:
            return None
        if not isinstance(api_result.data, dict):
            return None
        series = api_result.data.get("series")
        if not isinstance(series, dict) or not series:
            return None

        parsed = {}
        for date_str, values in series.items():
            try:
                parsed[date_str] = float(values["RSI"])
            except (KeyError, ValueError, TypeError):
                continue
        return parsed or None

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
