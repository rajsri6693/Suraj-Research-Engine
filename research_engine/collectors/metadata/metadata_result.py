"""
Metadata Result

Implements MetadataResult, the structured Collected Data the Metadata
Collector produces for the Metadata Knowledge Section, per
project_documentation/KNOWLEDGE_MODEL.md and
project_documentation/RESEARCH_COLLECTORS.md.

CollectorStatus is defined locally here, matching RESEARCH_COLLECTORS.md
Section 5's own three values exactly (Success, Partial, Failed), rather
than imported from research_engine.assembly -- that module is outside
IMP-08P's source of truth, and a real collector's own result package
should be self-contained.

Per KNOWLEDGE_MODEL.md, the Metadata section "describes the knowledge
record itself, not the company" -- so, unlike every other collector,
MetadataResult's fields describe this research run's own identity,
versioning, and timing rather than a fact about the company being
researched.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import List


class CollectorStatus(Enum):
    """Whether this collector's own attempt succeeded, per
    RESEARCH_COLLECTORS.md Section 5."""

    SUCCESS = "Success"
    PARTIAL = "Partial"
    FAILED = "Failed"


@dataclass
class MetadataResult:
    """The Metadata Collector's Collected Data describing this research
    run itself, per IMP-08P's field list."""

    research_session_id: str
    research_topic: str
    research_profile: str
    research_category: str
    language: str
    research_version: str
    collector_version: str
    workflow_version: str
    started_time: datetime
    completed_time: datetime
    execution_duration: timedelta
    runtime_environment: str
    sources: List[str]
    collection_time: datetime
    collector_status: CollectorStatus
