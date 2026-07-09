"""
Historical Price Collector

Implements HistoricalPriceCollector, per
project_documentation/RESEARCH_COLLECTORS.md and
project_documentation/COLLECTOR_SOURCE_STRATEGY.md. It is responsible
ONLY for collecting the Historical Price (OHLC) Knowledge Section and
returning a HistoricalPriceResult.

This phase does NOT perform live research. collect() returns a valid
HistoricalPriceResult built from placeholder/mock values only -- the
goal is to validate the Collector architecture and the Historical Price
data contract, not external data retrieval. It NEVER calls an API,
accesses the internet, verifies data, approves data, accesses a
database, writes SQLite, generates scripts or videos, or calls any other
collector.

Preferred Source Category: Market Data Providers. Fallback Category:
Official Exchange Information, per COLLECTOR_SOURCE_STRATEGY.md's
Collector Mapping (Section 4).
"""

from __future__ import annotations

from datetime import datetime

from ..base_collector import BaseCollector
from .historical_price_result import CollectorStatus, HistoricalPriceResult, OHLCRecord


class InvalidResearchTopicError(Exception):
    """Raised when collect() is given an empty or missing Research
    Topic."""


class HistoricalPriceCollector(BaseCollector):
    """Collects the Historical Price (OHLC) Knowledge Section."""

    @property
    def collector_name(self) -> str:
        return "Historical Price Collector"

    @property
    def knowledge_section(self) -> str:
        return "Historical Price (OHLC)"

    def collect(self, research_topic: str) -> HistoricalPriceResult:
        """Gather Historical Price (OHLC) data for `research_topic`.

        Input: Research Topic. Output: a HistoricalPriceResult.

        This phase returns placeholder/mock values only -- no live
        research, no API call, no internet access. It validates the
        collector's interface and data contract, not real collection.
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

        return HistoricalPriceResult(
            symbol="SMFG",
            exchange="NSE",
            timeframe="Daily",
            start_date=ohlc_records[0].date,
            end_date=ohlc_records[-1].date,
            ohlc_records=ohlc_records,
            total_trading_days=len(ohlc_records),
            adjusted_prices=True,
            sources=["Market Data Providers (placeholder)"],
            collection_time=datetime.now(),
            collector_status=CollectorStatus.SUCCESS,
        )
