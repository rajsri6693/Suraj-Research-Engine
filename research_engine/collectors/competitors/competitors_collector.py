"""
Competitors Collector

Implements CompetitorsCollector, per
project_documentation/RESEARCH_COLLECTORS.md and
project_documentation/COLLECTOR_SOURCE_STRATEGY.md. It is responsible
ONLY for collecting the Competitors Knowledge Section and returning a
CompetitorResult.

This phase does NOT perform live research. collect() returns a valid
CompetitorResult built from placeholder/mock values only -- the goal is
to validate the Collector architecture and the Competitor data contract,
not external data retrieval. It NEVER calls an API, accesses the
internet, verifies data, approves data, accesses a database, writes
SQLite, generates scripts or videos, or calls any other collector.

Preferred Source Category: Sector Information Sources. Fallback
Category: Financial News Sources, per COLLECTOR_SOURCE_STRATEGY.md's
Collector Mapping (Section 4).
"""

from __future__ import annotations

from datetime import datetime

from ..base_collector import BaseCollector
from .competitor_result import CollectorStatus, CompetitorResult


class InvalidResearchTopicError(Exception):
    """Raised when collect() is given an empty or missing Research
    Topic."""


class CompetitorsCollector(BaseCollector):
    """Collects the Competitors Knowledge Section."""

    @property
    def collector_name(self) -> str:
        return "Competitors Collector"

    @property
    def knowledge_section(self) -> str:
        return "Competitors"

    def collect(self, research_topic: str) -> CompetitorResult:
        """Gather Competitor information for `research_topic`.

        Input: Research Topic. Output: a CompetitorResult.

        This phase returns placeholder/mock values only -- no live
        research, no API call, no internet access. It validates the
        collector's interface and data contract, not real collection.
        """
        if not research_topic or not research_topic.strip():
            raise InvalidResearchTopicError("Research Topic must not be empty.")

        return CompetitorResult(
            company_name="Sample Manufacturing Ltd",
            competitor_name="Placeholder Industries Ltd",
            industry="Diversified Manufacturing",
            comparison_summary=(
                "A placeholder comparison summary used to validate the "
                "Competitors Collector's data contract; not the result of "
                "live research."
            ),
            competitive_strengths=["Wider distribution network", "Lower cost base"],
            competitive_weaknesses=["Smaller product portfolio"],
            market_position="Challenger",
            market_share=12.4,
            sources=["Sector Information Sources (placeholder)"],
            collection_time=datetime.now(),
            collector_status=CollectorStatus.SUCCESS,
        )
