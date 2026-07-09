"""
Management Collector

Implements ManagementCollector, per
project_documentation/RESEARCH_COLLECTORS.md and
project_documentation/COLLECTOR_SOURCE_STRATEGY.md. It is responsible
ONLY for collecting the Management Knowledge Section and returning a
ManagementResult.

This phase does NOT perform live research. collect() returns a valid
ManagementResult built from placeholder/mock values only -- the goal is
to validate the Collector architecture and the Management data contract,
not external data retrieval. It NEVER calls an API, accesses the
internet, verifies data, approves data, accesses a database, writes
SQLite, generates scripts or videos, or calls any other collector.

Preferred Source Category: Official Company Information. Fallback
Category: Official Corporate Filings, per
COLLECTOR_SOURCE_STRATEGY.md's Collector Mapping (Section 4).
"""

from __future__ import annotations

from datetime import datetime

from ..base_collector import BaseCollector
from .management_result import CollectorStatus, ManagementResult


class InvalidResearchTopicError(Exception):
    """Raised when collect() is given an empty or missing Research
    Topic."""


class ManagementCollector(BaseCollector):
    """Collects the Management Knowledge Section."""

    @property
    def collector_name(self) -> str:
        return "Management Collector"

    @property
    def knowledge_section(self) -> str:
        return "Management"

    def collect(self, research_topic: str) -> ManagementResult:
        """Gather Management information for `research_topic`.

        Input: Research Topic. Output: a ManagementResult.

        This phase returns placeholder/mock values only -- no live
        research, no API call, no internet access. It validates the
        collector's interface and data contract, not real collection.
        """
        if not research_topic or not research_topic.strip():
            raise InvalidResearchTopicError("Research Topic must not be empty.")

        return ManagementResult(
            company_name="Sample Manufacturing Ltd",
            chairman="Placeholder Chairperson",
            managing_director="Placeholder Managing Director",
            chief_executive_officer="Placeholder Chief Executive Officer",
            board_of_directors=[
                "Placeholder Chairperson",
                "Placeholder Managing Director",
                "Placeholder Independent Director A",
                "Placeholder Independent Director B",
            ],
            key_management_personnel=[
                "Placeholder Chief Financial Officer",
                "Placeholder Chief Operating Officer",
            ],
            management_experience_summary=(
                "A placeholder management experience summary used to "
                "validate the Management Collector's data contract; not "
                "the result of live research."
            ),
            corporate_governance_notes=(
                "Placeholder note: board composition meets independent "
                "director requirements."
            ),
            sources=["Official Company Information (placeholder)"],
            collection_time=datetime.now(),
            collector_status=CollectorStatus.SUCCESS,
        )
