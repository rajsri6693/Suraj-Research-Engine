"""Unit tests for research_engine.review.human_review."""

import unittest
from datetime import datetime

from research_engine.assembly.collector_result import CollectorResult, CollectorStatus
from research_engine.assembly.result_assembly import ResearchResultAssembly
from research_engine.planner.research_plan import KnowledgeSection, ResearchCategory
from research_engine.planner.research_planner import ResearchPlanner
from research_engine.review.human_review import HumanReview, InvalidReviewError
from research_engine.review.review_decision import ReviewDecision
from research_engine.session.session_manager import SessionManager
from research_engine.verification.knowledge_verifier import KnowledgeVerifier


def make_result(
    section: KnowledgeSection, status: CollectorStatus = CollectorStatus.SUCCESS
) -> CollectorResult:
    collected_knowledge = "Some gathered fact." if status != CollectorStatus.FAILED else None
    return CollectorResult(
        collector_name=f"{section.value} Collector",
        knowledge_section=section,
        collected_knowledge=collected_knowledge,
        sources=["A source."] if status != CollectorStatus.FAILED else [],
        collection_time=datetime(2026, 7, 9, 9, 5, 0),
        collector_status=status,
    )


def make_verification_report(all_succeed=True):
    session = SessionManager().create_session(
        research_topic="Full analysis ahead of quarterly results next week.",
        research_profile="Sample Manufacturing Ltd (SMFG, NSE)",
        research_category="Stock Analysis",
    )
    plan = ResearchPlanner().create_research_plan(
        research_profile="Sample Manufacturing Ltd (SMFG, NSE)",
        research_category=ResearchCategory.STOCK_ANALYSIS,
        research_topic="Full analysis ahead of quarterly results next week.",
    )
    if all_succeed:
        results = [make_result(section) for section in plan.required_knowledge_sections]
    else:
        results = [
            make_result(section)
            for section in plan.required_knowledge_sections
            if section != KnowledgeSection.TECHNICAL_ANALYSIS
        ]
        results.append(
            make_result(KnowledgeSection.TECHNICAL_ANALYSIS, status=CollectorStatus.FAILED)
        )
    package = ResearchResultAssembly().create_research_package(results, session, plan)
    return KnowledgeVerifier().verify_research_package(package)


class TestReviewVerificationReport(unittest.TestCase):
    def test_returns_skipped_decision_with_all_verified_sections_eligible(self):
        report = make_verification_report()
        result = HumanReview().review_verification_report(report)

        self.assertEqual(result.research_id, report.research_id)
        self.assertEqual(result.review_decision, ReviewDecision.SKIPPED)
        self.assertIsNone(result.reviewed_by)
        self.assertEqual(set(result.reviewed_sections), set(report.verified_sections))
        self.assertEqual(result.revision_sections, [])

    def test_raises_for_missing_report(self):
        with self.assertRaises(InvalidReviewError):
            HumanReview().review_verification_report(None)


class TestApprove(unittest.TestCase):
    def setUp(self):
        self.report = make_verification_report()
        self.review = HumanReview()

    def test_approve_verified_sections(self):
        sections = [KnowledgeSection.FINANCIAL_INFORMATION]
        result = self.review.approve(self.report, sections, reviewed_by="jane.reviewer")
        self.assertEqual(result.review_decision, ReviewDecision.APPROVED)
        self.assertEqual(result.reviewed_sections, sections)
        self.assertEqual(result.revision_sections, [])
        self.assertEqual(result.reviewed_by, "jane.reviewer")

    def test_approve_records_review_notes(self):
        result = self.review.approve(
            self.report,
            [KnowledgeSection.FINANCIAL_INFORMATION],
            reviewed_by="jane.reviewer",
            review_notes="Figures match the filing.",
        )
        self.assertEqual(result.review_notes, "Figures match the filing.")


class TestReject(unittest.TestCase):
    def setUp(self):
        self.report = make_verification_report()
        self.review = HumanReview()

    def test_reject_verified_section(self):
        sections = [KnowledgeSection.HISTORICAL_PRICE_OHLC]
        result = self.review.reject(self.report, sections, reviewed_by="jane.reviewer")
        self.assertEqual(result.review_decision, ReviewDecision.REJECTED)
        self.assertEqual(result.reviewed_sections, sections)
        self.assertEqual(result.revision_sections, [])


class TestRequestRevision(unittest.TestCase):
    def setUp(self):
        self.report = make_verification_report()
        self.review = HumanReview()

    def test_request_revision_populates_revision_sections(self):
        sections = [KnowledgeSection.MANAGEMENT]
        result = self.review.request_revision(
            self.report, sections, reviewed_by="jane.reviewer"
        )
        self.assertEqual(result.review_decision, ReviewDecision.NEEDS_REVISION)
        self.assertEqual(result.reviewed_sections, sections)
        self.assertEqual(result.revision_sections, sections)


class TestSkip(unittest.TestCase):
    def setUp(self):
        self.report = make_verification_report()
        self.review = HumanReview()

    def test_skip_leaves_revision_sections_empty(self):
        sections = [KnowledgeSection.SHAREHOLDING]
        result = self.review.skip(self.report, sections, reviewed_by="jane.reviewer")
        self.assertEqual(result.review_decision, ReviewDecision.SKIPPED)
        self.assertEqual(result.reviewed_sections, sections)
        self.assertEqual(result.revision_sections, [])


class TestInvalidReviewHandling(unittest.TestCase):
    def setUp(self):
        self.report = make_verification_report()
        self.review = HumanReview()

    def test_missing_verification_report_is_rejected(self):
        with self.assertRaises(InvalidReviewError):
            self.review.approve(
                None, [KnowledgeSection.FINANCIAL_INFORMATION], reviewed_by="jane.reviewer"
            )

    def test_empty_reviewed_by_is_rejected(self):
        with self.assertRaises(InvalidReviewError):
            self.review.approve(
                self.report, [KnowledgeSection.FINANCIAL_INFORMATION], reviewed_by=""
            )

    def test_whitespace_only_reviewed_by_is_rejected(self):
        with self.assertRaises(InvalidReviewError):
            self.review.approve(
                self.report, [KnowledgeSection.FINANCIAL_INFORMATION], reviewed_by="   "
            )

    def test_empty_sections_list_is_rejected(self):
        with self.assertRaises(InvalidReviewError):
            self.review.approve(self.report, [], reviewed_by="jane.reviewer")

    def test_section_not_verified_is_rejected(self):
        mixed_report = make_verification_report(all_succeed=False)
        with self.assertRaises(InvalidReviewError):
            self.review.approve(
                mixed_report,
                [KnowledgeSection.TECHNICAL_ANALYSIS],
                reviewed_by="jane.reviewer",
            )

    def test_reject_action_also_enforces_eligibility(self):
        mixed_report = make_verification_report(all_succeed=False)
        with self.assertRaises(InvalidReviewError):
            self.review.reject(
                mixed_report,
                [KnowledgeSection.TECHNICAL_ANALYSIS],
                reviewed_by="jane.reviewer",
            )

    def test_request_revision_action_also_enforces_eligibility(self):
        mixed_report = make_verification_report(all_succeed=False)
        with self.assertRaises(InvalidReviewError):
            self.review.request_revision(
                mixed_report,
                [KnowledgeSection.TECHNICAL_ANALYSIS],
                reviewed_by="jane.reviewer",
            )

    def test_skip_action_also_enforces_eligibility(self):
        mixed_report = make_verification_report(all_succeed=False)
        with self.assertRaises(InvalidReviewError):
            self.review.skip(
                mixed_report,
                [KnowledgeSection.TECHNICAL_ANALYSIS],
                reviewed_by="jane.reviewer",
            )

    def test_one_eligible_and_one_ineligible_section_together_is_rejected(self):
        mixed_report = make_verification_report(all_succeed=False)
        with self.assertRaises(InvalidReviewError):
            self.review.approve(
                mixed_report,
                [KnowledgeSection.FINANCIAL_INFORMATION, KnowledgeSection.TECHNICAL_ANALYSIS],
                reviewed_by="jane.reviewer",
            )


class TestReviewHasOnlyAllowedDependencies(unittest.TestCase):
    def test_review_module_only_imports_allowed_modules_and_stdlib(self):
        import ast
        import pathlib

        allowed_stdlib = {"dataclasses", "datetime", "enum", "typing", "__future__"}
        allowed_absolute = {
            "research_engine.planner.research_plan",
            "research_engine.verification.verification_report",
        }

        package_dir = (
            pathlib.Path(__file__).resolve().parents[2] / "research_engine" / "review"
        )
        for module_path in package_dir.glob("*.py"):
            tree = ast.parse(module_path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    if node.level > 0:
                        continue  # relative import within this package
                    if node.module in allowed_absolute or node.module in allowed_stdlib:
                        continue
                    self.fail(f"{module_path.name}: unexpected import '{node.module}'")
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        top = alias.name.split(".")[0]
                        self.assertIn(
                            top,
                            allowed_stdlib,
                            f"{module_path.name}: unexpected import '{alias.name}'",
                        )


if __name__ == "__main__":
    unittest.main()
