"""
Government Policy Result

Implements GovernmentPolicyResult, the structured Collected Data the
Government Policy Collector produces for the Government Policies
Knowledge Section, per project_documentation/KNOWLEDGE_MODEL.md and
project_documentation/RESEARCH_COLLECTORS.md.

CollectorStatus is defined locally here, matching RESEARCH_COLLECTORS.md
Section 5's own three values exactly (Success, Partial, Failed), rather
than imported from research_engine.assembly -- that module is outside
IMP-08F's source of truth, and a real collector's own result package
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
class GovernmentPolicyResult:
    """The Government Policies Collector's Collected Data for one
    policy, per IMP-08F's field list."""

    policy_title: str
    policy_category: str
    policy_description: str
    government_authority: str
    effective_date: datetime
    affected_sectors: List[str]
    affected_companies: List[str]
    expected_impact: str
    policy_status: str
    sources: List[str]
    collection_time: datetime
    collector_status: CollectorStatus
