"""
Company Result

Implements CompanyResult, the structured Collected Data the Company
Collector produces for the Company Information Knowledge Section, per
project_documentation/KNOWLEDGE_MODEL.md and
project_documentation/RESEARCH_COLLECTORS.md.

CollectorStatus is defined locally here, matching RESEARCH_COLLECTORS.md
Section 5's own three values exactly (Success, Partial, Failed), rather
than imported from research_engine.assembly -- that module is outside
IMP-08A's source of truth, and a real collector's own result package
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
class CompanyResult:
    """The Company Information Collector's Collected Data for one
    company, per IMP-08A's field list."""

    company_name: str
    nse_symbol: Optional[str]
    bse_symbol: Optional[str]
    isin: Optional[str]
    sector: str
    industry: str
    headquarters: str
    founded_year: Optional[int]
    business_description: str
    official_website: str
    sources: List[str]
    collection_time: datetime
    collector_status: CollectorStatus
