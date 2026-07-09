"""
Shareholding Result

Implements ShareholdingResult, the structured Collected Data the
Shareholding Collector produces for the Shareholding Knowledge Section,
per project_documentation/KNOWLEDGE_MODEL.md and
project_documentation/RESEARCH_COLLECTORS.md.

CollectorStatus is defined locally here, matching RESEARCH_COLLECTORS.md
Section 5's own three values exactly (Success, Partial, Failed), rather
than imported from research_engine.assembly -- that module is outside
IMP-08L's source of truth, and a real collector's own result package
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
class ShareholdingResult:
    """The Shareholding Collector's Collected Data for one company, for
    one reporting quarter, per IMP-08L's field list.

    Each holding percentage (promoter, FII, DII, public, government,
    insider) is its own field, per KNOWLEDGE_MODEL.md's Shareholding
    section ("Promoter/founder holding percentage, institutional
    ownership, public float... major shareholders").
    """

    company_name: str
    quarter: str
    promoter_holding: float
    fii_holding: float
    dii_holding: float
    public_holding: float
    government_holding: float
    insider_holding: float
    shareholding_changes: List[str]
    share_pledged: float
    institutional_holding_summary: str
    sources: List[str]
    collection_time: datetime
    collector_status: CollectorStatus
