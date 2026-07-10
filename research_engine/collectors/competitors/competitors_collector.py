"""
Competitors Collector

Implements CompetitorsCollector, per
project_documentation/RESEARCH_COLLECTORS.md and
project_documentation/COLLECTOR_SOURCE_STRATEGY.md. It is responsible
ONLY for collecting the Competitors Knowledge Section and returning a
CompetitorResult.

Per Claude-Prompts/IMP_10C_FMP_Integration.md, this collector may
optionally be given an APIManager (research_engine/api_manager/) for
Fundamental Data Category requests -- Competitors is Primary Provider
FMP's operation for this section, per API_MANAGER_ARCHITECTURE.md
Section 2/3. Without an APIManager (the default), collect() returns
the same placeholder/mock CompetitorResult as every prior phase, so
every existing caller and test is unaffected. When one is given,
collect() requests through it exclusively -- it NEVER calls FMP,
Finnhub, or any provider directly, per IMP-10C's Collectors rule -- and
reflects the real call's outcome (Success or Failed, and the real
provider that served it) onto the same placeholder shape. Mapping
FMP's raw JSON response onto each of CompetitorResult's individual
typed fields is future work outside this phase's scope.

It NEVER accesses the internet itself, verifies data, approves data,
accesses a database, writes SQLite, generates scripts or videos, or
calls any other collector.

Preferred Source Category: Sector Information Sources. Fallback
Category: Financial News Sources, per COLLECTOR_SOURCE_STRATEGY.md's
Collector Mapping (Section 4).
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from ...api_manager import APIManager, Category
from ..base_collector import BaseCollector
from .competitor_result import CollectorStatus, CompetitorResult


class InvalidResearchTopicError(Exception):
    """Raised when collect() is given an empty or missing Research
    Topic."""


class CompetitorsCollector(BaseCollector):
    """Collects the Competitors Knowledge Section."""

    FMP_OPERATION = "Competitors"

    def __init__(self, api_manager: Optional[APIManager] = None) -> None:
        self.api_manager = api_manager

    @property
    def collector_name(self) -> str:
        return "Competitors Collector"

    @property
    def knowledge_section(self) -> str:
        return "Competitors"

    def collect(self, research_topic: str) -> CompetitorResult:
        """Gather Competitor information for `research_topic`.

        Input: Research Topic. Output: a CompetitorResult.

        Without an APIManager, returns placeholder/mock values only, as
        every prior phase did. With one, requests through it
        exclusively and reflects the real outcome onto the same
        placeholder shape -- see this module's docstring.
        """
        if not research_topic or not research_topic.strip():
            raise InvalidResearchTopicError("Research Topic must not be empty.")

        result = CompetitorResult(
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

        if self.api_manager is None:
            return result

        api_result = self.api_manager.request(
            Category.FUNDAMENTAL_DATA,
            self.FMP_OPERATION,
            {"symbol": research_topic},
            collector_name=self.collector_name,
        )
        if api_result.success:
            result.sources = [f"{api_result.provider_name.value} ({api_result.served_by.value})"]
            result.collector_status = CollectorStatus.SUCCESS
        else:
            result.sources = []
            result.collector_status = CollectorStatus.FAILED

        return result
