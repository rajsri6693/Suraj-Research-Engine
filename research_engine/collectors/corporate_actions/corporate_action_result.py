"""
Corporate Action Result

Implements CorporateActionResult, the structured Collected Data the
Corporate Action Collector produces for the Corporate Actions Knowledge
Section, per project_documentation/KNOWLEDGE_MODEL.md and
project_documentation/RESEARCH_COLLECTORS.md.

CollectorStatus is defined locally here, matching RESEARCH_COLLECTORS.md
Section 5's own three values exactly (Success, Partial, Failed), rather
than imported from research_engine.assembly -- that module is outside
IMP-08H's source of truth, and a real collector's own result package
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
class CorporateActionResult:
    """The Corporate Actions Collector's Collected Data for one action,
    per IMP-08H's field list.

    record_date is Optional since not every action type carries one --
    KNOWLEDGE_MODEL.md's Corporate Actions section covers dividends,
    stock splits, bonus issues, buybacks, and mergers, each with an
    action type, announcement date, effective date, and terms, but a
    record date specifically applies to some action types more than
    others.
    """

    action_type: str
    action_title: str
    announcement_date: datetime
    effective_date: datetime
    record_date: Optional[datetime]
    description: str
    impact_summary: str
    related_company: str
    sources: List[str]
    collection_time: datetime
    collector_status: CollectorStatus
