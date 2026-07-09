"""
Historical Price Collector package.

Public entry point for the Historical Price Collector, implementing the
Historical Price (OHLC) Knowledge Section per
project_documentation/RESEARCH_COLLECTORS.md.
"""

from .historical_price_collector import (
    HistoricalPriceCollector,
    InvalidResearchTopicError,
)
from .historical_price_result import CollectorStatus, HistoricalPriceResult, OHLCRecord

__all__ = [
    "HistoricalPriceCollector",
    "HistoricalPriceResult",
    "OHLCRecord",
    "CollectorStatus",
    "InvalidResearchTopicError",
]
