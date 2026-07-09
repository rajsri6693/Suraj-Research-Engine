"""Unit tests for research_engine.verification.knowledge_verifier."""

import unittest
from datetime import datetime

from research_engine.assembly.collector_result import CollectorResult, CollectorStatus
from research_engine.assembly.research_package import (
    AssembledSection,
    OverallCollectionStatus,
    ResearchPackage,
    SectionStatus,
)
from research_engine.assembly.result_assembly import ResearchResultAssembly
from research_engine.planner.research_plan import KnowledgeSection, ResearchCategory
from research_engine.planner.research_planner import ResearchPlanner
from research_engine.session.session_manager import SessionManager
from research_engine.verification.knowledge_verifier import (
    InvalidVerificationInputError,
    KnowledgeVerifier,
)
from research_engine.verification.verification_report import OverallVerificationStatus
from research_engine.verification.verification_result import (
    Confidence,
    VerificationStatus,
)


def make_result(
    section: KnowledgeSection,
    status: CollectorStatus = CollectorStatus.SUCCESS,
    sources=None,
) -> CollectorResult:
    collected_knowledge = "Some gathered fact." if status != CollectorStatus.FAILED else None
    return CollectorResult(
        collector_name=f"{section.value} Collector",
        knowledge_section=section,
        collected_knowledge=collected_knowledge,
        sources=(sources if sources is not None else ["A source."]) if status != CollectorStatus.FAILED else [],
        collection_time=datetime(2026, 7, 9, 9, 5, 0),
        collector_status=status,
    )


def make_full_success_package():
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
    results = [make_result(section) for section in plan.required_knowledge_sections]
    return ResearchResultAssembly().create_research_package(results, session, plan)


def make_mixed_package():
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
    results = [
        make_result(section)
        for section in plan.required_knowledge_sections
        if section != KnowledgeSection.TECHNICAL_ANALYSIS
    ]
    results.append(
        make_result(KnowledgeSection.TECHNICAL_ANALYSIS, status=CollectorStatus.FAILED)
    )
    return ResearchResultAssembly().create_research_package(results, session, plan)


class TestVerifyResearchPackage(unittest.TestCase):
    def setUp(self):
        self.verifier = KnowledgeVerifier()

    def test_all_sections_verified_when_everything_succeeded(self):
        package = make_full_success_package()
        report = self.verifier.verify_research_package(package)

        self.assertEqual(report.research_id, package.research_session)
        self.assertEqual(len(report.verification_results), 12)
        self.assertEqual(len(report.verified_sections), 12)
        self.assertEqual(report.failed_sections, [])
        self.assertEqual(report.pending_sections, [])
        self.assertEqual(report.overall_status, OverallVerificationStatus.VERIFIED)
        self.assertIsNotNone(report.generated_time)

    def test_failed_collector_section_is_rejected(self):
        package = make_mixed_package()
        report = self.verifier.verify_research_package(package)

        rejected = [
            result
            for result in report.verification_results
            if result.knowledge_section == KnowledgeSection.TECHNICAL_ANALYSIS
        ][0]
        self.assertEqual(rejected.verification_status, VerificationStatus.REJECTED)
        self.assertIn(KnowledgeSection.TECHNICAL_ANALYSIS, report.failed_sections)
        self.assertNotIn(KnowledgeSection.TECHNICAL_ANALYSIS, report.verified_sections)


class TestValidateSources(unittest.TestCase):
    def setUp(self):
        self.verifier = KnowledgeVerifier()

    def test_true_when_data_and_sources_present(self):
        entry = AssembledSection(
            knowledge_section=KnowledgeSection.FINANCIAL_INFORMATION,
            status=SectionStatus.COMPLETED,
            collected_knowledge="Fact.",
            sources=["Source A"],
            collection_time=datetime(2026, 7, 9, 9, 5, 0),
        )
        self.assertTrue(self.verifier.validate_sources(entry))

    def test_false_when_no_sources(self):
        entry = AssembledSection(
            knowledge_section=KnowledgeSection.FINANCIAL_INFORMATION,
            status=SectionStatus.COMPLETED,
            collected_knowledge="Fact.",
            sources=[],
            collection_time=datetime(2026, 7, 9, 9, 5, 0),
        )
        self.assertFalse(self.verifier.validate_sources(entry))

    def test_false_when_no_collected_knowledge(self):
        entry = AssembledSection(
            knowledge_section=KnowledgeSection.TECHNICAL_ANALYSIS,
            status=SectionStatus.FAILED,
            collected_knowledge=None,
            sources=[],
            collection_time=datetime(2026, 7, 9, 9, 9, 0),
        )
        self.assertFalse(self.verifier.validate_sources(entry))


class TestDetectMissingSections(unittest.TestCase):
    def test_finds_the_failed_section(self):
        package = make_mixed_package()
        missing = KnowledgeVerifier().detect_missing_sections(package)
        self.assertEqual(missing, [KnowledgeSection.TECHNICAL_ANALYSIS])

    def test_empty_when_everything_succeeded(self):
        package = make_full_success_package()
        missing = KnowledgeVerifier().detect_missing_sections(package)
        self.assertEqual(missing, [])


class TestDetectDuplicateSections(unittest.TestCase):
    def test_no_duplicates_in_a_well_formed_package(self):
        package = make_full_success_package()
        self.assertEqual(KnowledgeVerifier().detect_duplicate_sections(package), [])

    def test_finds_a_duplicate_entry(self):
        package = make_full_success_package()
        duplicate_entry = AssembledSection(
            knowledge_section=package.knowledge_sections[0].knowledge_section,
            status=SectionStatus.COMPLETED,
            collected_knowledge="Duplicate.",
            sources=["Source"],
            collection_time=datetime(2026, 7, 9, 9, 5, 0),
        )
        package.knowledge_sections.append(duplicate_entry)
        duplicates = KnowledgeVerifier().detect_duplicate_sections(package)
        self.assertEqual(duplicates, [package.knowledge_sections[0].knowledge_section])


class TestDetermineVerificationStatus(unittest.TestCase):
    def setUp(self):
        self.verifier = KnowledgeVerifier()

    def test_missing_collected_knowledge_is_rejected(self):
        entry = AssembledSection(
            knowledge_section=KnowledgeSection.TECHNICAL_ANALYSIS,
            status=SectionStatus.MISSING,
            collected_knowledge=None,
            sources=[],
            collection_time=None,
        )
        status, reason = self.verifier.determine_verification_status(entry)
        self.assertEqual(status, VerificationStatus.REJECTED)
        self.assertIn("No Collected Knowledge", reason)

    def test_missing_sources_is_rejected(self):
        entry = AssembledSection(
            knowledge_section=KnowledgeSection.FINANCIAL_INFORMATION,
            status=SectionStatus.COMPLETED,
            collected_knowledge="Fact.",
            sources=[],
            collection_time=datetime(2026, 7, 9, 9, 5, 0),
        )
        status, reason = self.verifier.determine_verification_status(entry)
        self.assertEqual(status, VerificationStatus.REJECTED)
        self.assertIn("source", reason)

    def test_missing_collection_time_is_rejected(self):
        entry = AssembledSection(
            knowledge_section=KnowledgeSection.FINANCIAL_INFORMATION,
            status=SectionStatus.COMPLETED,
            collected_knowledge="Fact.",
            sources=["Source A"],
            collection_time=None,
        )
        status, reason = self.verifier.determine_verification_status(entry)
        self.assertEqual(status, VerificationStatus.REJECTED)
        self.assertIn("Collection Time", reason)

    def test_complete_entry_is_verified(self):
        entry = AssembledSection(
            knowledge_section=KnowledgeSection.FINANCIAL_INFORMATION,
            status=SectionStatus.COMPLETED,
            collected_knowledge="Fact.",
            sources=["Source A"],
            collection_time=datetime(2026, 7, 9, 9, 5, 0),
        )
        status, _ = self.verifier.determine_verification_status(entry)
        self.assertEqual(status, VerificationStatus.VERIFIED)

    def test_confidence_high_with_multiple_sources(self):
        entry = AssembledSection(
            knowledge_section=KnowledgeSection.FINANCIAL_INFORMATION,
            status=SectionStatus.COMPLETED,
            collected_knowledge="Fact.",
            sources=["Source A", "Source B"],
            collection_time=datetime(2026, 7, 9, 9, 5, 0),
        )
        result = self.verifier._verify_section(entry)
        self.assertEqual(result.confidence, Confidence.HIGH)

    def test_confidence_medium_with_single_source(self):
        entry = AssembledSection(
            knowledge_section=KnowledgeSection.FINANCIAL_INFORMATION,
            status=SectionStatus.COMPLETED,
            collected_knowledge="Fact.",
            sources=["Source A"],
            collection_time=datetime(2026, 7, 9, 9, 5, 0),
        )
        result = self.verifier._verify_section(entry)
        self.assertEqual(result.confidence, Confidence.MEDIUM)

    def test_confidence_none_when_rejected(self):
        entry = AssembledSection(
            knowledge_section=KnowledgeSection.TECHNICAL_ANALYSIS,
            status=SectionStatus.MISSING,
            collected_knowledge=None,
            sources=[],
            collection_time=None,
        )
        result = self.verifier._verify_section(entry)
        self.assertIsNone(result.confidence)


class TestGenerateVerificationReport(unittest.TestCase):
    def setUp(self):
        self.verifier = KnowledgeVerifier()

    def test_overall_status_verified_when_all_sections_verified(self):
        report = self.verifier.verify_research_package(make_full_success_package())
        self.assertEqual(report.overall_status, OverallVerificationStatus.VERIFIED)

    def test_overall_status_partial_when_mixed(self):
        report = self.verifier.verify_research_package(make_mixed_package())
        self.assertEqual(report.overall_status, OverallVerificationStatus.PARTIAL)

    def test_overall_status_rejected_when_nothing_verified(self):
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
        empty_package = ResearchResultAssembly().create_research_package(
            [], session, plan
        )
        report = self.verifier.verify_research_package(empty_package)
        self.assertEqual(report.overall_status, OverallVerificationStatus.REJECTED)
        self.assertEqual(report.verified_sections, [])
        self.assertEqual(len(report.failed_sections), 12)


class TestInvalidInputHandling(unittest.TestCase):
    def setUp(self):
        self.verifier = KnowledgeVerifier()

    def test_package_with_no_knowledge_sections_is_rejected(self):
        package = make_full_success_package()
        package.knowledge_sections = []
        with self.assertRaises(InvalidVerificationInputError):
            self.verifier.verify_research_package(package)

    def test_package_with_duplicate_sections_is_rejected(self):
        package = make_full_success_package()
        duplicate_entry = AssembledSection(
            knowledge_section=package.knowledge_sections[0].knowledge_section,
            status=SectionStatus.COMPLETED,
            collected_knowledge="Duplicate.",
            sources=["Source"],
            collection_time=datetime(2026, 7, 9, 9, 5, 0),
        )
        package.knowledge_sections.append(duplicate_entry)
        with self.assertRaises(InvalidVerificationInputError):
            self.verifier.verify_research_package(package)

    def test_invalid_input_never_produces_a_report(self):
        package = make_full_success_package()
        package.knowledge_sections = []
        try:
            self.verifier.verify_research_package(package)
        except InvalidVerificationInputError:
            pass
        else:
            self.fail("Expected InvalidVerificationInputError")


class TestVerificationHasOnlyAllowedDependencies(unittest.TestCase):
    def test_verification_module_only_imports_allowed_modules_and_stdlib(self):
        import ast
        import pathlib

        allowed_stdlib = {"dataclasses", "datetime", "enum", "typing", "__future__"}
        allowed_absolute = {
            "research_engine.planner.research_plan",
            "research_engine.assembly.research_package",
        }

        package_dir = (
            pathlib.Path(__file__).resolve().parents[2]
            / "research_engine"
            / "verification"
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
