"""
Human Review

Implements HumanReview, per project_documentation/HUMAN_REVIEW.md. It is
the only component that lets a human reviewer decide whether Verified
Knowledge is marked Approved.

It NEVER performs research, verifies knowledge, modifies collected
knowledge, accesses a database, calls APIs, or generates scripts or
videos. Verification Status has already been decided by Knowledge
Verification (KNOWLEDGE_VERIFICATION.md) by the time a Verification
Report reaches this module -- Human Review only ever acts on that
existing result, per HUMAN_REVIEW.md Section 5: only Knowledge Sections
whose Verification Status is Verified are eligible for any Reviewer
Action.
"""

from __future__ import annotations

from datetime import datetime
from typing import List

from research_engine.planner.research_plan import KnowledgeSection
from research_engine.verification.verification_report import VerificationReport

from .review_decision import ReviewDecision
from .review_result import ReviewResult


class InvalidReviewError(Exception):
    """Raised when a review action is attempted without a Verification
    Report, without a reviewer identity, without at least one target
    Knowledge Section, or against a section whose Verification Status is
    not Verified -- per HUMAN_REVIEW.md Section 5."""


class HumanReview:
    """Lets a human reviewer act on the Verified sections of a
    Verification Report."""

    def review_verification_report(
        self, verification_report: VerificationReport
    ) -> ReviewResult:
        """Review Verification Report.

        Input: Verification Report, per HUMAN_REVIEW.md Section 2
        (Review Input). Output: a ReviewResult, per Section 3,
        representing the report's arrival on the Review Screen -- every
        Verified section becomes eligible for review, and none has been
        acted on yet. Review Decision starts at Skipped, matching
        Pending Review -- the default status for every Verified section
        entering Human Review, per Section 7 -- since ReviewDecision has
        no separate "not yet decided" value of its own.
        """
        if verification_report is None:
            raise InvalidReviewError("A Verification Report is required.")
        return ReviewResult(
            research_id=verification_report.research_id,
            review_decision=ReviewDecision.SKIPPED,
            review_notes="",
            reviewed_by=None,
            review_time=datetime.now(),
            reviewed_sections=list(verification_report.verified_sections),
            revision_sections=[],
        )

    def approve(
        self,
        verification_report: VerificationReport,
        sections: List[KnowledgeSection],
        reviewed_by: str,
        review_notes: str = "",
    ) -> ReviewResult:
        """Approve.

        The reviewer confirms the given Verified sections are accurate
        and fit for use, per HUMAN_REVIEW.md Section 5.
        """
        self._validate_action(verification_report, sections, reviewed_by)
        return self._make_result(
            verification_report, ReviewDecision.APPROVED, sections, reviewed_by, review_notes
        )

    def reject(
        self,
        verification_report: VerificationReport,
        sections: List[KnowledgeSection],
        reviewed_by: str,
        review_notes: str = "",
    ) -> ReviewResult:
        """Reject.

        The reviewer determines the given Verified sections should not
        be treated as usable knowledge, despite having passed
        verification, per HUMAN_REVIEW.md Section 5.
        """
        self._validate_action(verification_report, sections, reviewed_by)
        return self._make_result(
            verification_report, ReviewDecision.REJECTED, sections, reviewed_by, review_notes
        )

    def request_revision(
        self,
        verification_report: VerificationReport,
        sections: List[KnowledgeSection],
        reviewed_by: str,
        review_notes: str = "",
    ) -> ReviewResult:
        """Request Revision.

        The reviewer determines the given Verified sections are close
        but not yet acceptable, per HUMAN_REVIEW.md Section 5. Revision
        Sections holds exactly these sections -- only Request Revision
        ever populates it.
        """
        self._validate_action(verification_report, sections, reviewed_by)
        result = self._make_result(
            verification_report,
            ReviewDecision.NEEDS_REVISION,
            sections,
            reviewed_by,
            review_notes,
        )
        result.revision_sections = list(sections)
        return result

    def skip(
        self,
        verification_report: VerificationReport,
        sections: List[KnowledgeSection],
        reviewed_by: str,
        review_notes: str = "",
    ) -> ReviewResult:
        """Skip.

        The reviewer defers a decision on the given Verified sections
        without approving, rejecting, or requesting revision, per
        HUMAN_REVIEW.md Section 5. The sections remain Pending Review.
        """
        self._validate_action(verification_report, sections, reviewed_by)
        return self._make_result(
            verification_report, ReviewDecision.SKIPPED, sections, reviewed_by, review_notes
        )

    def _validate_action(
        self,
        verification_report: VerificationReport,
        sections: List[KnowledgeSection],
        reviewed_by: str,
    ) -> None:
        if verification_report is None:
            raise InvalidReviewError("A Verification Report is required.")
        if not reviewed_by or not reviewed_by.strip():
            raise InvalidReviewError("A reviewer identity is required.")
        if not sections:
            raise InvalidReviewError("At least one Knowledge Section is required.")
        ineligible = [
            section
            for section in sections
            if section not in verification_report.verified_sections
        ]
        if ineligible:
            names = ", ".join(section.value for section in ineligible)
            raise InvalidReviewError(
                "Not eligible for review -- Verification Status is not Verified "
                f"for: {names}."
            )

    def _make_result(
        self,
        verification_report: VerificationReport,
        decision: ReviewDecision,
        sections: List[KnowledgeSection],
        reviewed_by: str,
        review_notes: str,
    ) -> ReviewResult:
        return ReviewResult(
            research_id=verification_report.research_id,
            review_decision=decision,
            review_notes=review_notes,
            reviewed_by=reviewed_by,
            review_time=datetime.now(),
            reviewed_sections=list(sections),
            revision_sections=[],
        )
