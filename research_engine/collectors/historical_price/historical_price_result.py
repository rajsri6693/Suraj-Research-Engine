"""
Historical Price Result

Implements HistoricalPriceResult, the structured Collected Data the
Historical Price Collector produces for the Historical Price (OHLC)
Knowledge Section, per project_documentation/KNOWLEDGE_MODEL.md and
project_documentation/RESEARCH_COLLECTORS.md.

CollectorStatus is defined locally here, matching RESEARCH_COLLECTORS.md
Section 5's own three values exactly (Success, Partial, Failed), rather
than imported from research_engine.assembly -- that module is outside
IMP-08G's source of truth, and a real collector's own result package
should be self-contained.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import List


class CollectorStatus(Enum):
    """Whether this collector's own attempt succeeded, per
    RESEARCH_COLLECTORS.md Section 5."""

    SUCCESS = "Success"
    PARTIAL = "Partial"
    FAILED = "Failed"


@dataclass
class OHLCRecord:
    """One trading period's record, per KNOWLEDGE_MODEL.md's Historical
    Price (OHLC) section: "One record per trading period -- open, high,
    low, close, volume, and the date or interval the record covers."""

    date: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int


@dataclass
class HistoricalPriceResult:
    """The Historical Price (OHLC) Collector's Collected Data for one
    company, per IMP-08G's field list."""

    symbol: str
    exchange: str
    timeframe: str
    start_date: datetime
    end_date: datetime
    ohlc_records: List[OHLCRecord]
    total_trading_days: int
    adjusted_prices: bool
    sources: List[str]
    collection_time: datetime
    collector_status: CollectorStatus
