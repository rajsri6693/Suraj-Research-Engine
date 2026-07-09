"""
Risk Result

Implements RiskResult, the structured Collected Data the Risks Collector
produces for the Risks Knowledge Section, per
project_documentation/KNOWLEDGE_MODEL.md and
project_documentation/RESEARCH_COLLECTORS.md.

CollectorStatus is defined locally here, matching RESEARCH_COLLECTORS.md
Section 5's own three values exactly (Success, Partial, Failed), rather
than imported from research_engine.assembly -- that module is outside
IMP-08M's source of truth, and a real collector's own result package
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
class RiskResult:
    """The Risks Collector's Collected Data for one company, per
    IMP-08M's field list.

    Each risk category is its own field, per KNOWLEDGE_MODEL.md's Risks
    section ("Business risks, financial risks, regulatory risks,
    litigation, operational risks, and their sources").
    """

    company_name: str
    business_risks: List[str]
    financial_risks: List[str]
    operational_risks: List[str]
    regulatory_risks: List[str]
    sector_risks: List[str]
    market_risks: List[str]
    key_risk_summary: str
    risk_level: str
    mitigation_factors: List[str]
    sources: List[str]
    collection_time: datetime
    collector_status: CollectorStatus
