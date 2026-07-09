"""Unit tests for research_engine.planner.research_plan."""

import unittest
from datetime import datetime

from research_engine.planner.research_plan import (
    CollectorMode,
    KnowledgeSection,
    PlannerStatus,
    ResearchCategory,
    ResearchDepth,
    ResearchPlan,
    ResearchPriority,
)


def make_plan(**overrides) -> ResearchPlan:
    defaults = dict(
        research_id="RP-20260709-001",
        research_profile=["Sample Manufacturing Ltd (SMFG, NSE)"],
        research_category=ResearchCategory.STOCK_ANALYSIS,
        research_topic="Full analysis ahead of quarterly results next week.",
        research_depth=ResearchDepth.DEEP,
        depth_reason="Stock Analysis is always Deep Research.",
        research_priority=ResearchPriority.HIGH,
        priority_reason="Tied to an imminent event.",
        required_knowledge_sections=[
            KnowledgeSection.COMPANY_INFORMATION,
            KnowledgeSection.FINANCIAL_INFORMATION,
            KnowledgeSection.SOURCES,
            KnowledgeSection.METADATA,
        ],
        collector_mode=CollectorMode.PARALLEL,
        planner_status=PlannerStatus.CREATED,
        created_time=datetime(2026, 7, 9, 9, 0, 0),
        chart_required=False,
    )
    defaults.update(overrides)
    return ResearchPlan(**defaults)


class TestResearchPlanConstruction(unittest.TestCase):
    def test_holds_every_required_field(self):
        plan = make_plan()
        self.assertEqual(plan.research_id, "RP-20260709-001")
        self.assertEqual(
            plan.research_profile, ["Sample Manufacturing Ltd (SMFG, NSE)"]
        )
        self.assertEqual(plan.research_category, ResearchCategory.STOCK_ANALYSIS)
        self.assertEqual(plan.research_depth, ResearchDepth.DEEP)
        self.assertEqual(plan.research_priority, ResearchPriority.HIGH)
        self.assertEqual(plan.collector_mode, CollectorMode.PARALLEL)
        self.assertEqual(plan.planner_status, PlannerStatus.CREATED)
        self.assertIsInstance(plan.created_time, datetime)

    def test_required_knowledge_sections_preserve_order(self):
        plan = make_plan()
        self.assertEqual(
            plan.required_knowledge_sections,
            [
                KnowledgeSection.COMPANY_INFORMATION,
                KnowledgeSection.FINANCIAL_INFORMATION,
                KnowledgeSection.SOURCES,
                KnowledgeSection.METADATA,
            ],
        )


class TestResearchPlanHumanReadable(unittest.TestCase):
    def test_renders_all_key_facts(self):
        plan = make_plan()
        rendered = plan.to_human_readable()
        self.assertIn("Research Plan", rendered)
        self.assertIn("Sample Manufacturing Ltd (SMFG, NSE)", rendered)
        self.assertIn("Stock Analysis", rendered)
        self.assertIn("Full analysis ahead of quarterly results next week.", rendered)
        self.assertIn("Deep Research", rendered)
        self.assertIn("Stock Analysis is always Deep Research.", rendered)
        self.assertIn("High", rendered)
        self.assertIn("Tied to an imminent event.", rendered)
        self.assertIn("Company Information", rendered)
        self.assertIn("Financial Information", rendered)
        self.assertIn("Chart Required: No", rendered)
        self.assertIn("Parallel Collectors", rendered)
        self.assertIn("End of Plan.", rendered)

    def test_chart_required_true_renders_yes(self):
        plan = make_plan(chart_required=True)
        rendered = plan.to_human_readable()
        self.assertIn("Chart Required: Yes", rendered)

    def test_joins_multiple_profile_identifiers(self):
        plan = make_plan(
            research_profile=["ABC Ltd", "XYZ Ltd"],
            research_category=ResearchCategory.COMPARISON,
        )
        rendered = plan.to_human_readable()
        self.assertIn("ABC Ltd, XYZ Ltd", rendered)


class TestKnowledgeSectionEnumCompleteness(unittest.TestCase):
    def test_all_eighteen_knowledge_model_sections_are_represented(self):
        expected = {
            "Company Information",
            "Business Overview",
            "Products & Services",
            "Financial Information",
            "Orders & Contracts",
            "Shareholding",
            "Management",
            "Competitors",
            "Risks",
            "Market News",
            "Sector Information",
            "Government Policies",
            "Market Data",
            "Historical Price (OHLC)",
            "Technical Analysis",
            "Corporate Actions",
            "Sources",
            "Metadata",
        }
        actual = {section.value for section in KnowledgeSection}
        self.assertEqual(actual, expected)


class TestResearchCategoryEnumCompleteness(unittest.TestCase):
    def test_matches_research_input_standard_fixed_set(self):
        expected = {
            "Market News",
            "Stock Update",
            "Stock Analysis",
            "Sector Analysis",
            "Comparison",
        }
        actual = {category.value for category in ResearchCategory}
        self.assertEqual(actual, expected)


if __name__ == "__main__":
    unittest.main()
