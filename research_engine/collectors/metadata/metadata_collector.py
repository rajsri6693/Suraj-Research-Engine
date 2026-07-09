"""
Metadata Collector

Implements MetadataCollector, per
project_documentation/RESEARCH_COLLECTORS.md and
project_documentation/COLLECTOR_SOURCE_STRATEGY.md. It is responsible
ONLY for collecting Research metadata and returning a MetadataResult.

This phase does NOT perform live research. collect() returns a valid
MetadataResult built from placeholder/mock values only -- the goal is to
validate the Collector architecture and the Metadata contract, not
external data retrieval. It NEVER calls an API, accesses the internet,
verifies data, approves data, accesses a database, writes SQLite,
generates scripts or videos, or calls any other collector.

Per COLLECTOR_SOURCE_STRATEGY.md's Collector Mapping (Section 4), the
Metadata Knowledge Section has no Preferred Source Category of its own --
it is derived from the collection process itself (collection time,
collector status), not an external source category.
"""

from __future__ import annotations

from datetime import datetime

from ..base_collector import BaseCollector
from .metadata_result import CollectorStatus, MetadataResult


class InvalidResearchTopicError(Exception):
    """Raised when collect() is given an empty or missing Research
    Topic."""


class MetadataCollector(BaseCollector):
    """Collects the Metadata Knowledge Section."""

    @property
    def collector_name(self) -> str:
        return "Metadata Collector"

    @property
    def knowledge_section(self) -> str:
        return "Metadata"

    def collect(self, research_topic: str) -> MetadataResult:
        """Gather Research metadata for `research_topic`.

        Input: Research Topic. Output: a MetadataResult.

        This phase returns placeholder/mock values only, except for
        Research Topic, which is the real value passed in -- no live
        research, no API call, no internet access. It validates the
        collector's interface and data contract, not real collection.
        """
        if not research_topic or not research_topic.strip():
            raise InvalidResearchTopicError("Research Topic must not be empty.")

        started_time = datetime(2026, 7, 9, 9, 0, 0)
        completed_time = datetime(2026, 7, 9, 9, 17, 0)

        return MetadataResult(
            research_session_id="RS-20260709-001 (placeholder)",
            research_topic=research_topic,
            research_profile="Sample Manufacturing Ltd (SMFG, NSE) (placeholder)",
            research_category="Stock Analysis (placeholder)",
            language="English",
            research_version="1.0",
            collector_version="1.0",
            workflow_version="1.0",
            started_time=started_time,
            completed_time=completed_time,
            execution_duration=completed_time - started_time,
            runtime_environment="Python (standard library only)",
            sources=["Derived from the collection process (placeholder)"],
            collection_time=datetime.now(),
            collector_status=CollectorStatus.SUCCESS,
        )
