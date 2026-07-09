"""
Sources Collector

Implements SourcesCollector, per
project_documentation/RESEARCH_COLLECTORS.md and
project_documentation/COLLECTOR_SOURCE_STRATEGY.md. It is responsible
ONLY for collecting source metadata used during research and returning a
SourcesResult.

This phase does NOT perform live research. collect() returns a valid
SourcesResult built from placeholder/mock values only -- the goal is to
validate the Collector architecture and the Source metadata contract,
not external data retrieval. It NEVER calls an API, accesses the
internet, verifies data, approves data, accesses a database, writes
SQLite, generates scripts or videos, or calls any other collector.

Per COLLECTOR_SOURCE_STRATEGY.md's Collector Mapping (Section 4), the
Sources Knowledge Section has no Preferred Source Category of its own --
it is compiled from the sources already used by every other section's
collector, not independently sourced from one of the ten categories.
"""

from __future__ import annotations

from datetime import datetime

from ..base_collector import BaseCollector
from .sources_result import (
    CollectorStatus,
    SourceCategory,
    SourcePriority,
    SourcesResult,
)


class InvalidResearchTopicError(Exception):
    """Raised when collect() is given an empty or missing Research
    Topic."""


class SourcesCollector(BaseCollector):
    """Collects the Sources Knowledge Section."""

    @property
    def collector_name(self) -> str:
        return "Sources Collector"

    @property
    def knowledge_section(self) -> str:
        return "Sources"

    def collect(self, research_topic: str) -> SourcesResult:
        """Gather source metadata for `research_topic`.

        Input: Research Topic. Output: a SourcesResult.

        This phase returns placeholder/mock values only -- no live
        research, no API call, no internet access. It validates the
        collector's interface and data contract, not real collection.
        """
        if not research_topic or not research_topic.strip():
            raise InvalidResearchTopicError("Research Topic must not be empty.")

        return SourcesResult(
            source_name="Sample Manufacturing Ltd Q4 FY2026 quarterly filing (placeholder)",
            source_type="Filing",
            source_category=SourceCategory.OFFICIAL_CORPORATE_FILINGS,
            source_priority=SourcePriority.PRIMARY,
            source_reliability="High",
            source_language="English",
            collection_timestamp=datetime(2026, 7, 9),
            source_notes=(
                "A placeholder source note used to validate the Sources "
                "Collector's data contract; not the result of live research."
            ),
            sources=["Official Corporate Filings (placeholder)"],
            collection_time=datetime.now(),
            collector_status=CollectorStatus.SUCCESS,
        )
