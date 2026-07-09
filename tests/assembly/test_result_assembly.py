"""Unit tests for research_engine.assembly.result_assembly."""

import unittest
from datetime import datetime

from research_engine.assembly.collector_result import CollectorResult, CollectorStatus
from research_engine.assembly.research_package import (
    OverallCollectionStatus,
    SectionStatus,
)
from research_engine.assembly.result_assembly import (
    InvalidAssemblyInputError,
    ResearchResultAssembly,
)
from research_engine.planner.research_plan import KnowledgeSection, ResearchCategory
from research_engine.planner.research_planner import ResearchPlanner
from research_engine.session.session_manager import SessionManager


def make_session_and_plan():
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
    return session, plan


def make_result(
    section: KnowledgeSection,
    status: CollectorStatus = CollectorStatus.SUCCESS,
    collected_knowledge: str = "Some gathered fact.",
    sources=None,
    collector_name: str = None,
    collection_time: datetime = None,
) -> CollectorResult:
    if status == CollectorStatus.FAILED:
        collected_knowledge = None
        sources = []
    return CollectorResult(
        collector_name=collector_name or f"{section.value} Collector",
        knowledge_section=section,
        collected_knowledge=collected_knowledge,
        sources=sources if sources is not None else ["A source."],
        collection_time=collection_time or datetime(2026, 7, 9, 9, 5, 0),
        collector_status=status,
    )


def make_full_success_results(plan):
    return [make_result(section) for section in plan.required_knowledge_sections]


class TestCreateResearchPackage(unittest.TestCase):
    def setUp(self):
        self.assembly = ResearchResultAssembly()
        self.session, self.plan = make_session_and_plan()

    def test_creates_a_fully_formed_package_when_everything_succeeds(self):
        results = make_full_success_results(self.plan)
        package = self.assembly.create_research_package(results, self.session, self.plan)

        self.assertEqual(package.research_session, self.session.research_id)
        self.assertEqual(
            package.research_topic,
            "Full analysis ahead of quarterly results next week.",
        )
        self.assertEqual(
            package.research_profile, ["Sample Manufacturing Ltd (SMFG, NSE)"]
        )
        self.assertEqual(package.research_category, ResearchCategory.STOCK_ANALYSIS)
        self.assertEqual(len(package.knowledge_sections), 12)
        self.assertEqual(package.missing_sections, [])
        self.assertEqual(package.overall_collection_status, OverallCollectionStatus.COMPLETE)
        self.assertIsNotNone(package.collection_completed_time)

    def test_assigns_unique_research_ids_across_runs(self):
        results = make_full_success_results(self.plan)
        first = self.assembly.create_research_package(results, self.session, self.plan)
        second = self.assembly.create_research_package(results, self.session, self.plan)
        self.assertNotEqual(first.research_id, second.research_id)

    def test_research_id_matches_documented_form(self):
        results = make_full_success_results(self.plan)
        package = self.assembly.create_research_package(results, self.session, self.plan)
        prefix, date_stamp, sequence = package.research_id.split("-")
        self.assertEqual(prefix, "RPK")
        self.assertEqual(len(date_stamp), 8)
        self.assertEqual(len(sequence), 3)

    def test_matches_the_documented_worked_example_shape(self):
        # Eleven Completed, one Failed (Technical Analysis) -> Partial,
        # per RESEARCH_RESULT_ASSEMBLY.md Section 9.
        results = [
            make_result(section)
            for section in self.plan.required_knowledge_sections
            if section != KnowledgeSection.TECHNICAL_ANALYSIS
        ]
        results.append(
            make_result(KnowledgeSection.TECHNICAL_ANALYSIS, status=CollectorStatus.FAILED)
        )
        package = self.assembly.create_research_package(results, self.session, self.plan)

        self.assertEqual(package.overall_collection_status, OverallCollectionStatus.PARTIAL)
        self.assertEqual(len(package.missing_sections), 1)
        self.assertEqual(
            package.missing_sections[0].knowledge_section,
            KnowledgeSection.TECHNICAL_ANALYSIS,
        )


class TestMergeCollectorResults(unittest.TestCase):
    def setUp(self):
        self.assembly = ResearchResultAssembly()
        self.session, self.plan = make_session_and_plan()

    def test_one_entry_per_required_section_in_order(self):
        results = make_full_success_results(self.plan)
        merged = self.assembly.merge_collector_results(
            results, self.plan.required_knowledge_sections
        )
        self.assertEqual(
            [entry.knowledge_section for entry in merged],
            self.plan.required_knowledge_sections,
        )

    def test_present_successful_result_becomes_completed(self):
        results = [make_result(KnowledgeSection.FINANCIAL_INFORMATION)]
        merged = self.assembly.merge_collector_results(
            results, [KnowledgeSection.FINANCIAL_INFORMATION]
        )
        entry = merged[0]
        self.assertEqual(entry.status, SectionStatus.COMPLETED)
        self.assertEqual(entry.collected_knowledge, "Some gathered fact.")

    def test_present_failed_result_becomes_failed_with_no_data(self):
        results = [
            make_result(
                KnowledgeSection.TECHNICAL_ANALYSIS, status=CollectorStatus.FAILED
            )
        ]
        merged = self.assembly.merge_collector_results(
            results, [KnowledgeSection.TECHNICAL_ANALYSIS]
        )
        entry = merged[0]
        self.assertEqual(entry.status, SectionStatus.FAILED)
        self.assertIsNone(entry.collected_knowledge)

    def test_absent_result_with_no_previous_package_becomes_missing(self):
        merged = self.assembly.merge_collector_results(
            [], [KnowledgeSection.TECHNICAL_ANALYSIS]
        )
        entry = merged[0]
        self.assertEqual(entry.status, SectionStatus.MISSING)
        self.assertIsNone(entry.collected_knowledge)

    def test_absent_result_with_prior_completed_entry_becomes_skipped_with_data_carried_forward(
        self,
    ):
        first_pass_results = make_full_success_results(self.plan)
        first_package = self.assembly.create_research_package(
            first_pass_results, self.session, self.plan
        )

        # Revision Loop pass: only Financial Information is re-collected;
        # every other required section should be Skipped, carrying its
        # prior entry forward unchanged.
        revised_results = [make_result(KnowledgeSection.FINANCIAL_INFORMATION)]
        second_package = self.assembly.create_research_package(
            revised_results, self.session, self.plan, previous_package=first_package
        )

        skipped_entries = {
            entry.knowledge_section: entry
            for entry in second_package.knowledge_sections
            if entry.knowledge_section != KnowledgeSection.FINANCIAL_INFORMATION
        }
        for section, entry in skipped_entries.items():
            self.assertEqual(entry.status, SectionStatus.SKIPPED)
            self.assertEqual(entry.collected_knowledge, "Some gathered fact.")

        financial_entry = next(
            entry
            for entry in second_package.knowledge_sections
            if entry.knowledge_section == KnowledgeSection.FINANCIAL_INFORMATION
        )
        self.assertEqual(financial_entry.status, SectionStatus.COMPLETED)

    def test_skipped_entry_carrying_forward_missing_data_still_counts_as_missing(self):
        first_package = self.assembly.create_research_package(
            [], self.session, self.plan
        )
        self.assertTrue(
            all(
                entry.status == SectionStatus.MISSING
                for entry in first_package.knowledge_sections
            )
        )

        revised_results = [make_result(KnowledgeSection.FINANCIAL_INFORMATION)]
        second_package = self.assembly.create_research_package(
            revised_results, self.session, self.plan, previous_package=first_package
        )
        still_missing = [
            entry
            for entry in second_package.knowledge_sections
            if entry.knowledge_section == KnowledgeSection.TECHNICAL_ANALYSIS
        ][0]
        self.assertEqual(still_missing.status, SectionStatus.SKIPPED)
        self.assertIsNone(still_missing.collected_knowledge)
        self.assertIn(still_missing, second_package.missing_sections)


class TestIdentifyMissingSections(unittest.TestCase):
    def test_only_sections_without_collected_knowledge_are_missing(self):
        assembly = ResearchResultAssembly()
        session, plan = make_session_and_plan()
        results = [
            make_result(section)
            for section in plan.required_knowledge_sections
            if section != KnowledgeSection.TECHNICAL_ANALYSIS
        ]
        results.append(
            make_result(KnowledgeSection.TECHNICAL_ANALYSIS, status=CollectorStatus.FAILED)
        )
        package = assembly.create_research_package(results, session, plan)
        self.assertEqual(len(package.missing_sections), 1)
        self.assertEqual(
            package.missing_sections[0].knowledge_section,
            KnowledgeSection.TECHNICAL_ANALYSIS,
        )


class TestGenerateCollectorSummary(unittest.TestCase):
    def setUp(self):
        self.assembly = ResearchResultAssembly()
        self.session, self.plan = make_session_and_plan()

    def test_one_row_per_collector_result(self):
        results = make_full_success_results(self.plan)
        package = self.assembly.create_research_package(results, self.session, self.plan)
        self.assertEqual(len(package.collector_summary), len(results))

    def test_skipped_section_has_no_summary_row(self):
        first_package = self.assembly.create_research_package(
            make_full_success_results(self.plan), self.session, self.plan
        )
        revised_results = [make_result(KnowledgeSection.FINANCIAL_INFORMATION)]
        second_package = self.assembly.create_research_package(
            revised_results, self.session, self.plan, previous_package=first_package
        )
        self.assertEqual(len(second_package.collector_summary), 1)
        self.assertEqual(
            second_package.collector_summary[0].collector_name,
            "Financial Information Collector",
        )

    def test_summary_row_matches_collector_result_fields(self):
        result = make_result(
            KnowledgeSection.FINANCIAL_INFORMATION,
            collector_name="Financial Information Collector",
            collection_time=datetime(2026, 7, 9, 9, 6, 0),
        )
        package = self.assembly.create_research_package(
            [result], self.session, self.plan
        )
        row = package.collector_summary[0]
        self.assertEqual(row.collector_name, "Financial Information Collector")
        self.assertEqual(row.execution_status, CollectorStatus.SUCCESS)
        self.assertEqual(row.completion_time, datetime(2026, 7, 9, 9, 6, 0))


class TestDetermineOverallCollectionStatus(unittest.TestCase):
    def setUp(self):
        self.assembly = ResearchResultAssembly()
        self.session, self.plan = make_session_and_plan()

    def test_complete_when_every_section_completed(self):
        package = self.assembly.create_research_package(
            make_full_success_results(self.plan), self.session, self.plan
        )
        self.assertEqual(package.overall_collection_status, OverallCollectionStatus.COMPLETE)

    def test_failed_when_nothing_completed(self):
        package = self.assembly.create_research_package([], self.session, self.plan)
        self.assertEqual(package.overall_collection_status, OverallCollectionStatus.FAILED)

    def test_partial_when_some_but_not_all_completed(self):
        results = [make_result(KnowledgeSection.FINANCIAL_INFORMATION)]
        package = self.assembly.create_research_package(
            results, self.session, self.plan
        )
        self.assertEqual(package.overall_collection_status, OverallCollectionStatus.PARTIAL)


class TestSourcePreservation(unittest.TestCase):
    def test_sources_are_preserved_exactly(self):
        assembly = ResearchResultAssembly()
        session, plan = make_session_and_plan()
        original_sources = ["Filing A, retrieved 2026-07-09", "Filing B, retrieved 2026-07-08"]
        result = make_result(
            KnowledgeSection.FINANCIAL_INFORMATION, sources=list(original_sources)
        )
        package = assembly.create_research_package([result], session, plan)
        entry = next(
            e
            for e in package.knowledge_sections
            if e.knowledge_section == KnowledgeSection.FINANCIAL_INFORMATION
        )
        self.assertEqual(entry.sources, original_sources)

    def test_mutating_the_original_result_sources_does_not_affect_the_package(self):
        assembly = ResearchResultAssembly()
        session, plan = make_session_and_plan()
        original_sources = ["Filing A"]
        result = make_result(
            KnowledgeSection.FINANCIAL_INFORMATION, sources=original_sources
        )
        package = assembly.create_research_package([result], session, plan)
        original_sources.append("Filing B (added after assembly)")
        entry = next(
            e
            for e in package.knowledge_sections
            if e.knowledge_section == KnowledgeSection.FINANCIAL_INFORMATION
        )
        self.assertEqual(entry.sources, ["Filing A"])


class TestMetadataPreservation(unittest.TestCase):
    def test_collection_time_and_status_preserved_on_completed_entry(self):
        assembly = ResearchResultAssembly()
        session, plan = make_session_and_plan()
        collection_time = datetime(2026, 7, 9, 9, 6, 30)
        result = make_result(
            KnowledgeSection.FINANCIAL_INFORMATION, collection_time=collection_time
        )
        package = assembly.create_research_package([result], session, plan)
        entry = next(
            e
            for e in package.knowledge_sections
            if e.knowledge_section == KnowledgeSection.FINANCIAL_INFORMATION
        )
        self.assertEqual(entry.collection_time, collection_time)

    def test_metadata_section_treated_like_any_other_section(self):
        assembly = ResearchResultAssembly()
        session, plan = make_session_and_plan()
        result = make_result(KnowledgeSection.METADATA)
        package = assembly.create_research_package([result], session, plan)
        entry = next(
            e
            for e in package.knowledge_sections
            if e.knowledge_section == KnowledgeSection.METADATA
        )
        self.assertEqual(entry.status, SectionStatus.COMPLETED)


class TestInvalidInputHandling(unittest.TestCase):
    def setUp(self):
        self.assembly = ResearchResultAssembly()
        self.session, self.plan = make_session_and_plan()

    def test_result_for_a_section_outside_the_plan_is_rejected(self):
        # Market News is not part of a Stock Analysis plan's required sections.
        results = [make_result(KnowledgeSection.MARKET_NEWS)]
        with self.assertRaises(InvalidAssemblyInputError):
            self.assembly.create_research_package(results, self.session, self.plan)

    def test_duplicate_result_for_the_same_section_is_rejected(self):
        results = [
            make_result(KnowledgeSection.FINANCIAL_INFORMATION),
            make_result(KnowledgeSection.FINANCIAL_INFORMATION),
        ]
        with self.assertRaises(InvalidAssemblyInputError):
            self.assembly.create_research_package(results, self.session, self.plan)

    def test_mismatched_session_and_plan_category_is_rejected(self):
        mismatched_session = SessionManager().create_session(
            research_topic="Latest announcement.",
            research_profile="Sample Manufacturing Ltd (SMFG, NSE)",
            research_category="Market News",
        )
        with self.assertRaises(InvalidAssemblyInputError):
            self.assembly.create_research_package([], mismatched_session, self.plan)

    def test_invalid_input_never_produces_a_package(self):
        sequence_before = self.assembly._sequence
        with self.assertRaises(InvalidAssemblyInputError):
            self.assembly.create_research_package(
                [make_result(KnowledgeSection.MARKET_NEWS)], self.session, self.plan
            )
        self.assertEqual(self.assembly._sequence, sequence_before)


class TestAssemblyHasNoForeignDependencies(unittest.TestCase):
    def test_assembly_module_only_imports_allowed_modules_and_stdlib(self):
        import ast
        import pathlib

        allowed_stdlib = {"dataclasses", "datetime", "enum", "typing", "__future__"}
        allowed_absolute = {
            "research_engine.planner.research_plan",
            "research_engine.session.research_session",
        }

        package_dir = (
            pathlib.Path(__file__).resolve().parents[2] / "research_engine" / "assembly"
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
