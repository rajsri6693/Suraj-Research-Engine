"""
Competitor Result

Implements CompetitorResult, the structured Collected Data the
Competitors Collector produces for the Competitors Knowledge Section,
per project_documentation/KNOWLEDGE_MODEL.md and
project_documentation/RESEARCH_COLLECTORS.md.

CollectorStatus is defined locally here, matching RESEARCH_COLLECTORS.md
Section 5's own three values exactly (Success, Partial, Failed), rather
than imported from research_engine.assembly -- that module is outside
IMP-08J's source of truth, and a real collector's own result package
should be self-contained.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import List, Optional


class CollectorStatus(Enum):
    """Whether this collector's own attempt succeeded, per
    RESEARCH_COLLECTORS.md Section 5."""

    SUCCESS = "Success"
    PARTIAL = "Partial"
    FAILED = "Failed"


@dataclass
class CompetitorResult:
    """The Competitors Collector's Collected Data comparing one company
    against one named competitor, per IMP-08J's field list.

    market_share is Optional since a reliable market share figure is not
    always determinable for a given competitor comparison.
    """

    company_name: str
    competitor_name: str
    industry: str
    comparison_summary: str
    competitive_strengths: List[str]
    competitive_weaknesses: List[str]
    market_position: str
    market_share: Optional[float]
    sources: List[str]
    collection_time: datetime
    collector_status: CollectorStatus
