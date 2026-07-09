"""
Market News Collector

Implements MarketNewsCollector, per
project_documentation/RESEARCH_COLLECTORS.md and
project_documentation/COLLECTOR_SOURCE_STRATEGY.md. It is responsible
ONLY for collecting the Market News Knowledge Section and returning a
MarketNewsResult.

This phase does NOT perform live research. collect() returns a valid
MarketNewsResult built from placeholder/mock values only -- the goal is
to validate the Collector architecture and the Market News data
contract, not external data retrieval. It NEVER calls an API, accesses
the internet, verifies data, approves data, accesses a database, writes
SQLite, generates scripts or videos, or calls any other collector.

Preferred Source Category: Financial News Sources. Fallback Category:
Official Exchange Information, per COLLECTOR_SOURCE_STRATEGY.md's
Collector Mapping (Section 4).
"""

from __future__ import annotations

from datetime import datetime

from ..base_collector import BaseCollector
from .market_news_result import CollectorStatus, MarketNewsResult


class InvalidResearchTopicError(Exception):
    """Raised when collect() is given an empty or missing Research
    Topic."""


class MarketNewsCollector(BaseCollector):
    """Collects the Market News Knowledge Section."""

    @property
    def collector_name(self) -> str:
        return "Market News Collector"

    @property
    def knowledge_section(self) -> str:
        return "Market News"

    def collect(self, research_topic: str) -> MarketNewsResult:
        """Gather Market News for `research_topic`.

        Input: Research Topic. Output: a MarketNewsResult.

        This phase returns placeholder/mock values only -- no live
        research, no API call, no internet access. It validates the
        collector's interface and data contract, not real collection.
        """
        if not research_topic or not research_topic.strip():
            raise InvalidResearchTopicError("Research Topic must not be empty.")

        return MarketNewsResult(
            news_title="Sample Manufacturing Ltd announces new plant expansion",
            news_summary=(
                "A placeholder news summary used to validate the Market News "
                "Collector's data contract; not the result of live research."
            ),
            news_category="Corporate Announcement",
            published_time=datetime(2026, 7, 8, 15, 30, 0),
            source_name="Business News Wire (placeholder)",
            related_companies=["Sample Manufacturing Ltd"],
            related_sectors=["Industrials"],
            impact="Positive",
            sources=["Financial News Sources (placeholder)"],
            collection_time=datetime.now(),
            collector_status=CollectorStatus.SUCCESS,
        )
