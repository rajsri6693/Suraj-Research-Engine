"""
Historical Price Collector

Implements HistoricalPriceCollector, per
project_documentation/RESEARCH_COLLECTORS.md and
project_documentation/COLLECTOR_SOURCE_STRATEGY.md. It is responsible
ONLY for collecting the Historical Price (OHLC) Knowledge Section and
returning a HistoricalPriceResult.

Per Claude-Prompts/IMP_10D_Alpha_Vantage_Integration.md, this collector
may optionally be given an APIManager (research_engine/api_manager/)
for Market & Technical Category requests -- Daily OHLC is Primary
Provider Alpha Vantage's operation for this section, per
API_MANAGER_ARCHITECTURE.md Section 2/3. Without an APIManager (the
default), collect() returns the same placeholder/mock
HistoricalPriceResult as every prior phase, so every existing caller
and test is unaffected. When one is given, collect() requests through
it exclusively -- it NEVER calls Alpha Vantage, Twelve Data, or any
provider directly, per IMP-10D's Collectors rule.

When Alpha Vantage itself serves the request with at least one real
OHLC record, collect() maps its live daily time series onto
HistoricalPriceResult (symbol, start/end date, ohlc_records,
total_trading_days) and rebuilds chart_dataset from those same real
records via this module's own existing _build_chart_dataset() -- no
separate real-data chart path is needed, since Chart Dataset has always
been derived from ohlc_records, real or placeholder alike. exchange and
adjusted_prices are not present in Alpha Vantage's response and are
deliberately left at their placeholder values rather than fabricated.
Per Claude-Prompts/IMP_10E_Twelve_Data_Integration.md, this Alpha-
Vantage-shaped mapping is intentionally NOT extended to Twelve Data
(now real, the Backup Provider) -- failover must happen only inside
APIManager, never inside a Collector, so this module has no Twelve
Data-specific code at all and never will. When the Backup Provider
serves the request instead (Twelve Data's own real response, shaped
differently from Alpha Vantage's), or Alpha Vantage returns no records
for the symbol, the existing placeholder field values are kept and
only Sources/Collector Status reflect the real outcome.

It NEVER accesses the internet itself, verifies data, approves data,
accesses a database, writes SQLite, generates scripts or videos, or
calls any other collector.

Preferred Source Category: Market Data Providers. Fallback Category:
Official Exchange Information, per COLLECTOR_SOURCE_STRATEGY.md's
Collector Mapping (Section 4).
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from ...api_manager import APIManager, Category, ProviderName
from ..base_collector import BaseCollector
from .historical_price_result import (
    ChartDataset,
    CollectorStatus,
    HistoricalPriceResult,
    OHLCRecord,
)


class InvalidResearchTopicError(Exception):
    """Raised when collect() is given an empty or missing Research
    Topic."""


class HistoricalPriceCollector(BaseCollector):
    """Collects the Historical Price (OHLC) Knowledge Section."""

    AV_OPERATION = "Daily OHLC"

    def __init__(self, api_manager: Optional[APIManager] = None) -> None:
        self.api_manager = api_manager

    @property
    def collector_name(self) -> str:
        return "Historical Price Collector"

    @property
    def knowledge_section(self) -> str:
        return "Historical Price (OHLC)"

    def collect(self, research_topic: str) -> HistoricalPriceResult:
        """Gather Historical Price (OHLC) data for `research_topic`.

        Input: Research Topic. Output: a HistoricalPriceResult.

        Without an APIManager, returns placeholder/mock values only, as
        every prior phase did. With one, requests through it
        exclusively and reflects the real outcome onto the same
        placeholder shape -- see this module's docstring.
        """
        if not research_topic or not research_topic.strip():
            raise InvalidResearchTopicError("Research Topic must not be empty.")

        ohlc_records = [
            OHLCRecord(
                date=datetime(2026, 7, 6),
                open=412.0,
                high=418.5,
                low=409.2,
                close=415.8,
                volume=1_250_000,
            ),
            OHLCRecord(
                date=datetime(2026, 7, 7),
                open=415.8,
                high=421.0,
                low=413.0,
                close=419.4,
                volume=1_380_000,
            ),
            OHLCRecord(
                date=datetime(2026, 7, 8),
                open=419.4,
                high=422.6,
                low=416.1,
                close=418.65,
                volume=1_190_000,
            ),
        ]

        result = HistoricalPriceResult(
            symbol="SMFG",
            exchange="NSE",
            timeframe="Daily",
            start_date=ohlc_records[0].date,
            end_date=ohlc_records[-1].date,
            ohlc_records=ohlc_records,
            total_trading_days=len(ohlc_records),
            adjusted_prices=True,
            chart_dataset=self._build_chart_dataset(ohlc_records),
            sources=["Market Data Providers (placeholder)"],
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
        real_records = self._alpha_vantage_records(api_result)

        if api_result.success and (real_records is not None or api_result.provider_name != ProviderName.ALPHA_VANTAGE):
            result.sources = [f"{api_result.provider_name.value} ({api_result.served_by.value})"]
            result.collector_status = CollectorStatus.SUCCESS
            if real_records is not None:
                result.symbol = research_topic
                result.ohlc_records = real_records
                result.start_date = real_records[0].date
                result.end_date = real_records[-1].date
                result.total_trading_days = len(real_records)
                result.chart_dataset = self._build_chart_dataset(real_records)
        else:
            # Either the API call itself failed, or Alpha Vantage
            # succeeded but returned no records for this symbol --
            # either way, no real Collected Data exists for this
            # section, per COLLECTOR_SOURCE_STRATEGY.md's Missing
            # Source Rules.
            result.sources = []
            result.collector_status = CollectorStatus.FAILED

        return result

    @staticmethod
    def _alpha_vantage_records(api_result) -> Optional[list]:
        """Parse Alpha Vantage's live "Time Series (Daily)" response
        (date -> {"1. open", "2. high", "3. low", "4. close",
        "5. volume"}, values as strings) into OHLCRecord objects,
        oldest first -- or None if this result did not come from Alpha
        Vantage, or it returned no series data."""
        if not api_result.success or api_result.provider_name != ProviderName.ALPHA_VANTAGE:
            return None
        if not isinstance(api_result.data, dict):
            return None
        series = api_result.data.get("series")
        if not isinstance(series, dict) or not series:
            return None

        records = []
        for date_str, values in series.items():
            try:
                records.append(
                    OHLCRecord(
                        date=datetime.strptime(date_str, "%Y-%m-%d"),
                        open=float(values["1. open"]),
                        high=float(values["2. high"]),
                        low=float(values["3. low"]),
                        close=float(values["4. close"]),
                        volume=int(float(values["5. volume"])),
                    )
                )
            except (KeyError, ValueError, TypeError):
                continue
        if not records:
            return None
        records.sort(key=lambda record: record.date)
        return records

    @staticmethod
    def _build_chart_dataset(ohlc_records) -> ChartDataset:
        """Reshape this collector's own OHLC Records into a chart-ready
        Chart Dataset, per IMP-09D -- reporting the same gathered facts
        in a chart-friendly layout, not generating a chart itself. Used
        for both placeholder and real (Alpha Vantage) records alike."""
        return ChartDataset(
            labels=[record.date.strftime("%Y-%m-%d") for record in ohlc_records],
            open_values=[record.open for record in ohlc_records],
            high_values=[record.high for record in ohlc_records],
            low_values=[record.low for record in ohlc_records],
            close_values=[record.close for record in ohlc_records],
            volume_values=[record.volume for record in ohlc_records],
        )
