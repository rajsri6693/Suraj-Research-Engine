"""
Review Decision

Implements ReviewDecision -- the reviewer's chosen action, per
project_documentation/HUMAN_REVIEW.md Section 5 (Reviewer Actions).
"""

from __future__ import annotations

from enum import Enum


class ReviewDecision(Enum):
    """What a human reviewer chose to do about a set of Knowledge
    Sections, per HUMAN_REVIEW.md Section 5: Approve, Reject, Request
    Revision, or Skip.

    ReviewDecision names the reviewer's action itself. It is distinct
    from Approval Status (HUMAN_REVIEW.md Section 7), which names the
    resulting state stored against a section -- a Skipped decision
    results in Approval Status Pending Review, not a status literally
    called "Skipped."
    """

    APPROVED = "Approved"
    REJECTED = "Rejected"
    NEEDS_REVISION = "Needs Revision"
    SKIPPED = "Skipped"
