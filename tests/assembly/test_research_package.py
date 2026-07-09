"""Unit tests for research_engine.assembly.research_package."""

import unittest
from datetime import datetime

from research_engine.assembly.collector_result import CollectorStatus
from research_engine.assembly.research_package import (
    AssembledSection,
    CollectorSummaryEntry,
    OverallCollectionStatus,
    ResearchPackage,
    SectionStatus,
)
from research_engine.planner.research_plan import KnowledgeSection, ResearchCategory


class TestSectionStatusVocabulary(unittest.TestCase):
    def test_four_statuses_defined(self):
        self.assertEqual(
            {status.value for status in SectionStatus},
            {"Completed", "Failed", "Missing", "Skipped"},
        )


class TestOverallCollectionStatusVocabulary(unittest.TestCase):
    def test_three_statuses_defined(self):
        self.assertEqual(
            {status.value for status in OverallCollectionStatus},
            {"Complete", "Partial", "Failed"},
        )


def make_package(**overrides) -> ResearchPackage:
    defaults = dict(
        research_id="RPK-20260709-001",
        research_session="RS-20260709-001",
        research_topic="Full analysis ahead of quarterly results next week.",
        research_profile=["Sample Manufacturing Ltd (SMFG, NSE)"],
        research_category=ResearchCategory.STOCK_ANALYSIS,
        knowledge_sections=[
            AssembledSection(
                knowledge_section=KnowledgeSection.FINANCIAL_INFORMATION,
                status=SectionStatus.COMPLETED,
                collected_knowledge="Q4 revenue of 412 crore.",
                sources=["Quarterly filing"],
                collection_time=datetime(2026, 7, 9, 9, 6, 0),
            ),
            AssembledSection(
                knowledge_section=KnowledgeSection.TECHNICAL_ANALYSIS,
                status=SectionStatus.FAILED,
                collected_knowledge=None,
                sources=[],
                collection_time=datetime(2026, 7, 9, 9, 9, 0),
            ),
        ],
        collector_summary=[
            CollectorSummaryEntry(
                collector_name="Financial Information Collector",
                execution_status=CollectorStatus.SUCCESS,
                completion_time=datetime(2026, 7, 9, 9, 6, 0),
            ),
            CollectorSummaryEntry(
                collector_name="Technical Analysis Collector",
                execution_status=CollectorStatus.FAILED,
                completion_time=datetime(2026, 7, 9, 9, 9, 0),
            ),
        ],
        missing_sections=[
            AssembledSection(
                knowledge_section=KnowledgeSection.TECHNICAL_ANALYSIS,
                status=SectionStatus.FAILED,
                collected_knowledge=None,
                sources=[],
                collection_time=datetime(2026, 7, 9, 9, 9, 0),
            ),
        ],
        overall_collection_status=OverallCollectionStatus.PARTIAL,
        collection_completed_time=datetime(2026, 7, 9, 9, 10, 0),
    )
    defaults.update(overrides)
    return ResearchPackage(**defaults)


class TestResearchPackageConstruction(unittest.TestCase):
    def test_holds_every_field(self):
        package = make_package()
        self.assertEqual(package.research_id, "RPK-20260709-001")
        self.assertEqual(package.research_session, "RS-20260709-001")
        self.assertEqual(
            package.research_profile, ["Sample Manufacturing Ltd (SMFG, NSE)"]
        )
        self.assertEqual(package.research_category, ResearchCategory.STOCK_ANALYSIS)
        self.assertEqual(len(package.knowledge_sections), 2)
        self.assertEqual(len(package.collector_summary), 2)
        self.assertEqual(len(package.missing_sections), 1)
        self.assertEqual(package.overall_collection_status, OverallCollectionStatus.PARTIAL)


class TestResearchPackageHumanReadable(unittest.TestCase):
    def test_renders_all_key_facts(self):
        rendered = make_package().to_human_readable()
        self.assertIn("Research Package", rendered)
        self.assertIn("RS-20260709-001", rendered)
        self.assertIn("Sample Manufacturing Ltd (SMFG, NSE)", rendered)
        self.assertIn("Stock Analysis", rendered)
        self.assertIn("Financial Information — Completed", rendered)
        self.assertIn("Technical Analysis — Failed", rendered)
        self.assertIn("Financial Information Collector", rendered)
        self.assertIn("Overall Collection Status: Partial", rendered)

    def test_renders_none_placeholder_when_nothing_missing(self):
        package = make_package(missing_sections=[])
        rendered = package.to_human_readable()
        self.assertIn("(none)", rendered)


if __name__ == "__main__":
    unittest.main()
