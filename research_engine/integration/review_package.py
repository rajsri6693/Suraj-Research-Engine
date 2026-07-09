"""
Human Review Package

Implements HumanReviewPackage, the complete bundle Integration Engine
delivers to the Human Review layer once Knowledge Verification
completes, per project_documentation/HUMAN_REVIEW.md,
project_documentation/RESEARCH_WORKFLOW.md,
project_documentation/KNOWLEDGE_VERIFICATION.md, and
project_documentation/RESEARCH_RESULT_ASSEMBLY.md.

This module defines data only -- it implements no user interface and
performs no review action itself. Assembling this package is Integration
Engine's own responsibility; the existing, unmodified Human Review
module (research_engine.review.human_review.HumanReview) still owns
every actual review decision.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

from research_engine.assembly.research_package import ResearchPackage
from research_engine.collectors.historical_price.historical_price_result import (
    ChartDataset,
)
from research_engine.planner.research_plan import KnowledgeSection, ResearchPlan
from research_engine.session.research_session import ResearchSession
from research_engine.verification.verification_report import VerificationReport


class ReviewPackageStatus(Enum):
    """The status of a Human Review Package at the moment it is handed
    to the Human Review layer.

    Pending Review is the only value this package ever carries, matching
    HUMAN_REVIEW.md Section 7's own definition -- the default status for
    every Verified section entering Human Review, before any Reviewer
    Action has been taken. This package is a snapshot of what is being
    handed over, not a decision; whatever a reviewer later decides is
    recorded separately, as a ReviewResult, by the Human Review module
    itself once it is invoked.
    """

    PENDING_REVIEW = "Pending Review"


@dataclass
class HumanReviewPackage:
    """The complete package Integration Engine delivers to Human Review
    once Knowledge Verification completes, per IMP-09B.

    eligible_sections mirrors verification_report.verified_sections --
    only Verified sections are eligible for any Reviewer Action, per
    HUMAN_REVIEW.md Section 5.

    chart_available, chart_type, and chart_dataset expose the Chart
    Generator's output to Human Review, per IMP-09D. chart_available is
    False and the other two are None whenever research_plan carried no
    chart request, since Chart Generator never runs in that case.
    """

    research_session: ResearchSession
    research_plan: ResearchPlan
    research_package: ResearchPackage
    verification_report: VerificationReport
    review_status: ReviewPackageStatus
    eligible_sections: List[KnowledgeSection]
    chart_available: bool = False
    chart_type: Optional[str] = None
    chart_dataset: Optional[ChartDataset] = None
