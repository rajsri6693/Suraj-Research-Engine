"""
Review Result

Implements ReviewResult, the single output of every HumanReview action,
per project_documentation/HUMAN_REVIEW.md.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from research_engine.planner.research_plan import KnowledgeSection

from .review_decision import ReviewDecision


@dataclass
class ReviewResult:
    """The outcome of one Human Review action.

    reviewed_sections holds every section this specific action touched,
    regardless of which decision was made. revision_sections holds the
    subset that needs revision -- populated only when review_decision is
    Needs Revision, per HUMAN_REVIEW.md Section 5 (Request Revision);
    empty for every other decision, including Review Verification
    Report's initial, pre-action result, where reviewed_by is None since
    no reviewer has acted yet.
    """

    research_id: str
    review_decision: ReviewDecision
    review_notes: str
    reviewed_by: Optional[str]
    review_time: datetime
    reviewed_sections: List[KnowledgeSection]
    revision_sections: List[KnowledgeSection]
