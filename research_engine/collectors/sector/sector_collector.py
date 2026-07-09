"""
Sector Collector

Implements SectorCollector, per
project_documentation/RESEARCH_COLLECTORS.md and
project_documentation/COLLECTOR_SOURCE_STRATEGY.md. It is responsible
ONLY for collecting the Sector Information Knowledge Section and
returning a SectorResult.

This phase does NOT perform live research. collect() returns a valid
SectorResult built from placeholder/mock values only -- the goal is to
validate the Collector architecture and the Sector data contract, not
external data retrieval. It NEVER calls an API, accesses the internet,
verifies data, approves data, accesses a database, writes SQLite,
generates scripts or videos, or calls any other collector.

Preferred Source Category: Sector Information Sources. Fallback
Category: Government Information, per COLLECTOR_SOURCE_STRATEGY.md's
Collector Mapping (Section 4).
"""

from __future__ import annotations

from datetime import datetime

from ..base_collector import BaseCollector
from .sector_result import CollectorStatus, SectorResult


class InvalidResearchTopicError(Exception):
    """Raised when collect() is given an empty or missing Research
    Topic."""


class SectorCollector(BaseCollector):
    """Collects the Sector Information Knowledge Section."""

    @property
    def collector_name(self) -> str:
        return "Sector Information Collector"

    @property
    def knowledge_section(self) -> str:
        return "Sector Information"

    def collect(self, research_topic: str) -> SectorResult:
        """Gather Sector Information for `research_topic`.

        Input: Research Topic. Output: a SectorResult.

        This phase returns placeholder/mock values only -- no live
        research, no API call, no internet access. It validates the
        collector's interface and data contract, not real collection.
        """
        if not research_topic or not research_topic.strip():
            raise InvalidResearchTopicError("Research Topic must not be empty.")

        return SectorResult(
            sector_name="Industrials",
            industry="Diversified Manufacturing",
            sector_description=(
                "A placeholder sector description used to validate the "
                "Sector Collector's data contract; not the result of live "
                "research."
            ),
            sector_performance="Moderate growth, broadly in line with the market.",
            top_companies=["Sample Manufacturing Ltd", "Placeholder Industries Ltd"],
            growth_drivers=["Rising domestic demand", "Infrastructure investment"],
            major_risks=["Input cost volatility", "Global supply chain disruption"],
            related_government_policies=["Placeholder manufacturing incentive scheme"],
            sources=["Sector Information Sources (placeholder)"],
            collection_time=datetime.now(),
            collector_status=CollectorStatus.SUCCESS,
        )
