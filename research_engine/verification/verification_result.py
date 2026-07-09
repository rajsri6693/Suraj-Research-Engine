"""
Verification Result

Implements VerificationResult, per
project_documentation/KNOWLEDGE_VERIFICATION.md Section 6 (Verification
Report) -- one entry per Knowledge Section evaluated.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional

from research_engine.planner.research_plan import KnowledgeSection


class VerificationStatus(Enum):
    """The four Verification Status values, per KNOWLEDGE_VERIFICATION.md
    Section 5.

    This implementation evaluates one Research Package snapshot at a
    time, with no access to previously-stored verified knowledge and no
    external database -- see KnowledgeVerifier's docstring for exactly
    which of these four values it can actually produce.
    """

    PENDING = "Pending"
    VERIFIED = "Verified"
    REJECTED = "Rejected"
    NEEDS_HUMAN_REVIEW = "Needs Human Review"


class Confidence(Enum):
    """Confidence values, per KNOWLEDGE_VERIFICATION.md Section 6."""

    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


@dataclass
class VerificationResult:
    """One Verification Report entry for one Knowledge Section, per
    KNOWLEDGE_VERIFICATION.md Section 6.

    Confidence is None for any section that did not reach Verified --
    per Section 6, Confidence describes how strongly sources support
    knowledge that was already found trustworthy, not a rating of
    knowledge that was rejected outright.
    """

    knowledge_section: KnowledgeSection
    verification_status: VerificationStatus
    reason: str
    source_count: int
    confidence: Optional[Confidence]
    last_updated: Optional[datetime]
