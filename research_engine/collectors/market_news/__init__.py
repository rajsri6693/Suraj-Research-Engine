"""
Market News Collector package.

Public entry point for the Market News Collector, implementing the
Market News Knowledge Section per
project_documentation/RESEARCH_COLLECTORS.md.
"""

from .market_news_collector import InvalidResearchTopicError, MarketNewsCollector
from .market_news_result import CollectorStatus, MarketNewsResult

__all__ = [
    "MarketNewsCollector",
    "MarketNewsResult",
    "CollectorStatus",
    "InvalidResearchTopicError",
]
