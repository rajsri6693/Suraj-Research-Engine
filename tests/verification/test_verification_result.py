"""Unit tests for research_engine.verification.verification_result."""

import unittest
from datetime import datetime

from research_engine.planner.research_plan import KnowledgeSection
from research_engine.verification.verification_result import (
    Confidence,
    VerificationResult,
    VerificationStatus,
)


class TestVerificationStatusVocabulary(unittest.TestCase):
    def test_four_statuses_defined(self):
        self.assertEqual(
            {status.value for status in VerificationStatus},
            {"Pending", "Verified", "Rejected", "Needs Human Review"},
        )


class TestConfidenceVocabulary(unittest.TestCase):
    def test_three_levels_defined(self):
        self.assertEqual(
            {level.value for level in Confidence}, {"High", "Medium", "Low"}
        )


class TestVerificationResultConstruction(unittest.TestCase):
    def test_holds_every_field(self):
        result = VerificationResult(
            knowledge_section=KnowledgeSection.FINANCIAL_INFORMATION,
            verification_status=VerificationStatus.VERIFIED,
            reason="Collected Knowledge is present with at least one valid source.",
            source_count=2,
            confidence=Confidence.HIGH,
            last_updated=datetime(2026, 7, 9, 9, 6, 0),
        )
        self.assertEqual(result.knowledge_section, KnowledgeSection.FINANCIAL_INFORMATION)
        self.assertEqual(result.verification_status, VerificationStatus.VERIFIED)
        self.assertEqual(result.source_count, 2)
        self.assertEqual(result.confidence, Confidence.HIGH)

    def test_confidence_and_last_updated_may_be_none(self):
        result = VerificationResult(
            knowledge_section=KnowledgeSection.TECHNICAL_ANALYSIS,
            verification_status=VerificationStatus.REJECTED,
            reason="No Collected Knowledge was received for this section.",
            source_count=0,
            confidence=None,
            last_updated=None,
        )
        self.assertIsNone(result.confidence)
        self.assertIsNone(result.last_updated)


if __name__ == "__main__":
    unittest.main()
