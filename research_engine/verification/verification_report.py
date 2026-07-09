"""
Verification Report

Implements VerificationReport, the single output of KnowledgeVerifier,
per project_documentation/KNOWLEDGE_VERIFICATION.md.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import List

from research_engine.planner.research_plan import KnowledgeSection

from .verification_result import VerificationResult


class OverallVerificationStatus(Enum):
    """The aggregate status for a whole Verification Report, mirroring
    the Complete/Partial/Failed pattern RESEARCH_RESULT_ASSEMBLY.md uses
    for Overall Collection Status, in Verification's own vocabulary."""

    VERIFIED = "Verified"
    PARTIAL = "Partial"
    REJECTED = "Rejected"


@dataclass
class VerificationReport:
    """The complete result of verifying one Research Package.

    research_id is the Research ID of the Research Session the verified
    Research Package belongs to (`research_package.research_session`),
    since a Verification Report describes verification progress for one
    research request, tracked by its session, across however many
    Research Packages that session has produced.

    pending_sections holds every section whose Verification Status is
    Pending or Needs Human Review -- both represent work not yet
    resolved to Verified or Rejected. See KnowledgeVerifier's docstring
    for why Needs Human Review is never produced by this implementation
    today, and Verification Results for full per-section fidelity.
    """

    research_id: str
    verification_results: List[VerificationResult]
    overall_status: OverallVerificationStatus
    verified_sections: List[KnowledgeSection]
    failed_sections: List[KnowledgeSection]
    pending_sections: List[KnowledgeSection]
    generated_time: datetime
