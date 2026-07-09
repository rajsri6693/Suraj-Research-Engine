"""Unit tests for research_engine.verification.verification_report."""

import unittest
from datetime import datetime

from research_engine.planner.research_plan import KnowledgeSection
from research_engine.verification.verification_report import (
    OverallVerificationStatus,
    VerificationReport,
)
from research_engine.verification.verification_result import (
    Confidence,
    VerificationResult,
    VerificationStatus,
)


class TestOverallVerificationStatusVocabulary(unittest.TestCase):
    def test_three_statuses_defined(self):
        self.assertEqual(
            {status.value for status in OverallVerificationStatus},
            {"Verified", "Partial", "Rejected"},
        )


class TestVerificationReportConstruction(unittest.TestCase):
    def test_holds_every_field(self):
        results = [
            VerificationResult(
                knowledge_section=KnowledgeSection.FINANCIAL_INFORMATION,
                verification_status=VerificationStatus.VERIFIED,
                reason="Verified.",
                source_count=1,
                confidence=Confidence.MEDIUM,
                last_updated=datetime(2026, 7, 9, 9, 6, 0),
            ),
        ]
        report = VerificationReport(
            research_id="RS-20260709-001",
            verification_results=results,
            overall_status=OverallVerificationStatus.VERIFIED,
            verified_sections=[KnowledgeSection.FINANCIAL_INFORMATION],
            failed_sections=[],
            pending_sections=[],
            generated_time=datetime(2026, 7, 9, 9, 10, 0),
        )
        self.assertEqual(report.research_id, "RS-20260709-001")
        self.assertEqual(len(report.verification_results), 1)
        self.assertEqual(report.overall_status, OverallVerificationStatus.VERIFIED)
        self.assertEqual(report.verified_sections, [KnowledgeSection.FINANCIAL_INFORMATION])
        self.assertEqual(report.failed_sections, [])
        self.assertEqual(report.pending_sections, [])


if __name__ == "__main__":
    unittest.main()
