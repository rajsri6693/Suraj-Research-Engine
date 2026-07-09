"""
Sector Result

Implements SectorResult, the structured Collected Data the Sector
Collector produces for the Sector Information Knowledge Section, per
project_documentation/KNOWLEDGE_MODEL.md and
project_documentation/RESEARCH_COLLECTORS.md.

CollectorStatus is defined locally here, matching RESEARCH_COLLECTORS.md
Section 5's own three values exactly (Success, Partial, Failed), rather
than imported from research_engine.assembly -- that module is outside
IMP-08D's source of truth, and a real collector's own result package
should be self-contained.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import List


class CollectorStatus(Enum):
    """Whether this collector's own attempt succeeded, per
    RESEARCH_COLLECTORS.md Section 5."""

    SUCCESS = "Success"
    PARTIAL = "Partial"
    FAILED = "Failed"


@dataclass
class SectorResult:
    """The Sector Information Collector's Collected Data for one sector,
    per IMP-08D's field list."""

    sector_name: str
    industry: str
    sector_description: str
    sector_performance: str
    top_companies: List[str]
    growth_drivers: List[str]
    major_risks: List[str]
    related_government_policies: List[str]
    sources: List[str]
    collection_time: datetime
    collector_status: CollectorStatus
