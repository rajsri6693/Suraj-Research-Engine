"""
Management Result

Implements ManagementResult, the structured Collected Data the
Management Collector produces for the Management Knowledge Section, per
project_documentation/KNOWLEDGE_MODEL.md and
project_documentation/RESEARCH_COLLECTORS.md.

CollectorStatus is defined locally here, matching RESEARCH_COLLECTORS.md
Section 5's own three values exactly (Success, Partial, Failed), rather
than imported from research_engine.assembly -- that module is outside
IMP-08K's source of truth, and a real collector's own result package
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
class ManagementResult:
    """The Management Collector's Collected Data for one company, per
    IMP-08K's field list.

    Chairman, Managing Director, and Chief Executive Officer are
    Optional since not every company's leadership structure fills each
    of these roles separately -- some are combined, or not applicable.
    """

    company_name: str
    chairman: Optional[str]
    managing_director: Optional[str]
    chief_executive_officer: Optional[str]
    board_of_directors: List[str]
    key_management_personnel: List[str]
    management_experience_summary: str
    corporate_governance_notes: str
    sources: List[str]
    collection_time: datetime
    collector_status: CollectorStatus
