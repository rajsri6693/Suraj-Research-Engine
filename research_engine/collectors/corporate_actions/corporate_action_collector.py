"""
Corporate Action Collector

Implements CorporateActionCollector, per
project_documentation/RESEARCH_COLLECTORS.md and
project_documentation/COLLECTOR_SOURCE_STRATEGY.md. It is responsible
ONLY for collecting the Corporate Actions Knowledge Section and
returning a CorporateActionResult.

This phase does NOT perform live research. collect() returns a valid
CorporateActionResult built from placeholder/mock values only -- the
goal is to validate the Collector architecture and the Corporate Action
data contract, not external data retrieval. It NEVER calls an API,
accesses the internet, verifies data, approves data, accesses a
database, writes SQLite, generates scripts or videos, or calls any other
collector.

Preferred Source Category: Official Corporate Filings. Fallback
Category: Official Exchange Information, per
COLLECTOR_SOURCE_STRATEGY.md's Collector Mapping (Section 4).
"""

from __future__ import annotations

from datetime import datetime

from ..base_collector import BaseCollector
from .corporate_action_result import CollectorStatus, CorporateActionResult


class InvalidResearchTopicError(Exception):
    """Raised when collect() is given an empty or missing Research
    Topic."""


class CorporateActionCollector(BaseCollector):
    """Collects the Corporate Actions Knowledge Section."""

    @property
    def collector_name(self) -> str:
        return "Corporate Actions Collector"

    @property
    def knowledge_section(self) -> str:
        return "Corporate Actions"

    def collect(self, research_topic: str) -> CorporateActionResult:
        """Gather Corporate Action information for `research_topic`.

        Input: Research Topic. Output: a CorporateActionResult.

        This phase returns placeholder/mock values only -- no live
        research, no API call, no internet access. It validates the
        collector's interface and data contract, not real collection.
        """
        if not research_topic or not research_topic.strip():
            raise InvalidResearchTopicError("Research Topic must not be empty.")

        return CorporateActionResult(
            action_type="Dividend",
            action_title="Interim dividend for FY2026",
            announcement_date=datetime(2026, 7, 1),
            effective_date=datetime(2026, 7, 20),
            record_date=datetime(2026, 7, 15),
            description=(
                "A placeholder corporate action description used to validate "
                "the Corporate Action Collector's data contract; not the "
                "result of live research."
            ),
            impact_summary="Positive -- returns cash to shareholders.",
            related_company="Sample Manufacturing Ltd",
            sources=["Official Corporate Filings (placeholder)"],
            collection_time=datetime.now(),
            collector_status=CollectorStatus.SUCCESS,
        )
