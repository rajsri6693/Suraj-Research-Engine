"""Unit tests for research_engine.review.review_result."""

import unittest
from datetime import datetime

from research_engine.planner.research_plan import KnowledgeSection
from research_engine.review.review_decision import ReviewDecision
from research_engine.review.review_result import ReviewResult


class TestReviewResultConstruction(unittest.TestCase):
    def test_holds_every_field(self):
        result = ReviewResult(
            research_id="RS-20260709-001",
            review_decision=ReviewDecision.APPROVED,
            review_notes="Looks correct.",
            reviewed_by="jane.reviewer",
            review_time=datetime(2026, 7, 9, 10, 0, 0),
            reviewed_sections=[KnowledgeSection.FINANCIAL_INFORMATION],
            revision_sections=[],
        )
        self.assertEqual(result.research_id, "RS-20260709-001")
        self.assertEqual(result.review_decision, ReviewDecision.APPROVED)
        self.assertEqual(result.review_notes, "Looks correct.")
        self.assertEqual(result.reviewed_by, "jane.reviewer")
        self.assertEqual(
            result.reviewed_sections, [KnowledgeSection.FINANCIAL_INFORMATION]
        )
        self.assertEqual(result.revision_sections, [])

    def test_reviewed_by_may_be_none(self):
        result = ReviewResult(
            research_id="RS-20260709-001",
            review_decision=ReviewDecision.SKIPPED,
            review_notes="",
            reviewed_by=None,
            review_time=datetime(2026, 7, 9, 10, 0, 0),
            reviewed_sections=[],
            revision_sections=[],
        )
        self.assertIsNone(result.reviewed_by)


if __name__ == "__main__":
    unittest.main()
