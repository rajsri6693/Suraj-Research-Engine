"""Unit tests for research_engine.review.review_decision."""

import unittest

from research_engine.review.review_decision import ReviewDecision


class TestReviewDecisionVocabulary(unittest.TestCase):
    def test_four_decisions_defined(self):
        self.assertEqual(
            {decision.value for decision in ReviewDecision},
            {"Approved", "Rejected", "Needs Revision", "Skipped"},
        )


if __name__ == "__main__":
    unittest.main()
