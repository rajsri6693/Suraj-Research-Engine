"""Unit tests for research_engine.planner.research_planner."""

import unittest

from research_engine.planner.research_plan import (
    CollectorMode,
    KnowledgeSection,
    PlannerStatus,
    ResearchCategory,
    ResearchDepth,
    ResearchPriority,
)
from research_engine.planner.research_planner import (
    InvalidResearchInputError,
    ResearchPlanner,
)


class TestCreateResearchPlan(unittest.TestCase):
    def setUp(self):
        self.planner = ResearchPlanner()

    def test_creates_a_fully_formed_plan(self):
        plan = self.planner.create_research_plan(
            research_profile="Sample Manufacturing Ltd (SMFG, NSE)",
            research_category=ResearchCategory.STOCK_ANALYSIS,
            research_topic="Full analysis ahead of quarterly results next week.",
        )
        self.assertEqual(plan.research_profile, ["Sample Manufacturing Ltd (SMFG, NSE)"])
        self.assertEqual(plan.research_category, ResearchCategory.STOCK_ANALYSIS)
        self.assertEqual(
            plan.research_topic,
            "Full analysis ahead of quarterly results next week.",
        )
        self.assertEqual(plan.planner_status, PlannerStatus.CREATED)
        self.assertEqual(plan.collector_mode, CollectorMode.PARALLEL)
        self.assertIsNotNone(plan.created_time)
        self.assertTrue(plan.depth_reason)
        self.assertTrue(plan.priority_reason)

    def test_accepts_a_single_profile_string_and_wraps_it(self):
        plan = self.planner.create_research_plan(
            research_profile="ABC Ltd",
            research_category=ResearchCategory.MARKET_NEWS,
            research_topic="Latest announcement.",
        )
        self.assertEqual(plan.research_profile, ["ABC Ltd"])

    def test_accepts_a_category_string_and_normalizes_it(self):
        plan = self.planner.create_research_plan(
            research_profile="ABC Ltd",
            research_category="Market News",
            research_topic="Latest announcement.",
        )
        self.assertEqual(plan.research_category, ResearchCategory.MARKET_NEWS)

    def test_assigns_unique_research_ids(self):
        first = self.planner.create_research_plan(
            research_profile="ABC Ltd",
            research_category=ResearchCategory.MARKET_NEWS,
            research_topic="Latest announcement.",
        )
        second = self.planner.create_research_plan(
            research_profile="ABC Ltd",
            research_category=ResearchCategory.MARKET_NEWS,
            research_topic="Latest announcement.",
        )
        self.assertNotEqual(first.research_id, second.research_id)

    def test_research_id_matches_documented_form(self):
        plan = self.planner.create_research_plan(
            research_profile="ABC Ltd",
            research_category=ResearchCategory.MARKET_NEWS,
            research_topic="Latest announcement.",
        )
        prefix, date_stamp, sequence = plan.research_id.split("-")
        self.assertEqual(prefix, "RP")
        self.assertEqual(len(date_stamp), 8)
        self.assertEqual(len(sequence), 3)

    def test_to_human_readable_contains_key_plan_facts(self):
        plan = self.planner.create_research_plan(
            research_profile="Sample Manufacturing Ltd (SMFG, NSE)",
            research_category=ResearchCategory.STOCK_ANALYSIS,
            research_topic="Full analysis ahead of quarterly results next week.",
        )
        rendered = plan.to_human_readable()
        self.assertIn("Sample Manufacturing Ltd (SMFG, NSE)", rendered)
        self.assertIn("Stock Analysis", rendered)
        self.assertIn("Deep Research", rendered)
        # This topic contains none of the three literal urgency phrases
        # RESEARCH_PLANNER.md Section 6 defines ("today," "breaking,"
        # "just announced"), so Stock Analysis correctly stays at its
        # Medium default rather than being raised to High.
        self.assertIn("Priority: Medium", rendered)
        self.assertIn("Parallel Collectors", rendered)
        self.assertIn("Financial Information", rendered)


class TestDetermineResearchDepth(unittest.TestCase):
    def setUp(self):
        self.planner = ResearchPlanner()

    def test_market_news_defaults_to_quick(self):
        depth, _ = self.planner.determine_research_depth(
            ResearchCategory.MARKET_NEWS, "Company opens a new plant."
        )
        self.assertEqual(depth, ResearchDepth.QUICK)

    def test_stock_update_defaults_to_quick(self):
        depth, _ = self.planner.determine_research_depth(
            ResearchCategory.STOCK_UPDATE, "Current price movement."
        )
        self.assertEqual(depth, ResearchDepth.QUICK)

    def test_topic_wording_upgrades_quick_category_to_deep(self):
        depth, reason = self.planner.determine_research_depth(
            ResearchCategory.STOCK_UPDATE, "Please give a full analysis of the move."
        )
        self.assertEqual(depth, ResearchDepth.DEEP)
        self.assertIn("full analysis", reason)

    def test_stock_analysis_is_always_deep(self):
        depth, _ = self.planner.determine_research_depth(
            ResearchCategory.STOCK_ANALYSIS, "Latest snapshot only, nothing more."
        )
        self.assertEqual(depth, ResearchDepth.DEEP)

    def test_sector_analysis_is_always_deep(self):
        depth, _ = self.planner.determine_research_depth(
            ResearchCategory.SECTOR_ANALYSIS, "What happened today."
        )
        self.assertEqual(depth, ResearchDepth.DEEP)

    def test_comparison_is_always_deep(self):
        depth, _ = self.planner.determine_research_depth(
            ResearchCategory.COMPARISON, "Latest price only."
        )
        self.assertEqual(depth, ResearchDepth.DEEP)

    def test_quick_signal_wording_does_not_change_quick_default(self):
        depth, _ = self.planner.determine_research_depth(
            ResearchCategory.MARKET_NEWS, "What happened today?"
        )
        self.assertEqual(depth, ResearchDepth.QUICK)


class TestDetermineResearchPriority(unittest.TestCase):
    def setUp(self):
        self.planner = ResearchPlanner()

    def test_market_news_is_always_high(self):
        priority, _ = self.planner.determine_research_priority(
            ResearchCategory.MARKET_NEWS, "A quiet, routine update."
        )
        self.assertEqual(priority, ResearchPriority.HIGH)

    def test_stock_update_is_always_high(self):
        priority, _ = self.planner.determine_research_priority(
            ResearchCategory.STOCK_UPDATE, "A quiet, routine update."
        )
        self.assertEqual(priority, ResearchPriority.HIGH)

    def test_stock_analysis_defaults_to_medium(self):
        priority, _ = self.planner.determine_research_priority(
            ResearchCategory.STOCK_ANALYSIS, "A general review of the business."
        )
        self.assertEqual(priority, ResearchPriority.MEDIUM)

    def test_urgency_wording_raises_stock_analysis_to_high(self):
        priority, reason = self.planner.determine_research_priority(
            ResearchCategory.STOCK_ANALYSIS, "Breaking news just came in."
        )
        self.assertEqual(priority, ResearchPriority.HIGH)
        self.assertIn("breaking", reason)

    def test_sector_analysis_defaults_to_low(self):
        priority, _ = self.planner.determine_research_priority(
            ResearchCategory.SECTOR_ANALYSIS, "General background reading."
        )
        self.assertEqual(priority, ResearchPriority.LOW)

    def test_comparison_defaults_to_low(self):
        priority, _ = self.planner.determine_research_priority(
            ResearchCategory.COMPARISON, "General background reading."
        )
        self.assertEqual(priority, ResearchPriority.LOW)

    def test_urgency_wording_raises_low_default_to_high(self):
        priority, reason = self.planner.determine_research_priority(
            ResearchCategory.COMPARISON, "Just announced: a merger between the two."
        )
        self.assertEqual(priority, ResearchPriority.HIGH)
        self.assertIn("just announced", reason)


class TestDetermineRequiredKnowledgeSections(unittest.TestCase):
    def setUp(self):
        self.planner = ResearchPlanner()

    def test_market_news_sections(self):
        sections = self.planner.determine_required_knowledge_sections(
            ResearchCategory.MARKET_NEWS, ["ABC Ltd"]
        )
        self.assertEqual(
            sections,
            [
                KnowledgeSection.COMPANY_INFORMATION,
                KnowledgeSection.MARKET_NEWS,
                KnowledgeSection.SOURCES,
                KnowledgeSection.METADATA,
            ],
        )

    def test_stock_update_sections(self):
        sections = self.planner.determine_required_knowledge_sections(
            ResearchCategory.STOCK_UPDATE, ["ABC Ltd"]
        )
        self.assertEqual(
            sections,
            [
                KnowledgeSection.COMPANY_INFORMATION,
                KnowledgeSection.MARKET_DATA,
                KnowledgeSection.HISTORICAL_PRICE_OHLC,
                KnowledgeSection.SOURCES,
                KnowledgeSection.METADATA,
            ],
        )

    def test_stock_analysis_sections(self):
        sections = self.planner.determine_required_knowledge_sections(
            ResearchCategory.STOCK_ANALYSIS, ["ABC Ltd"]
        )
        self.assertEqual(len(sections), 12)
        self.assertIn(KnowledgeSection.FINANCIAL_INFORMATION, sections)
        self.assertIn(KnowledgeSection.TECHNICAL_ANALYSIS, sections)
        self.assertIn(KnowledgeSection.SOURCES, sections)
        self.assertIn(KnowledgeSection.METADATA, sections)

    def test_sector_analysis_sections(self):
        sections = self.planner.determine_required_knowledge_sections(
            ResearchCategory.SECTOR_ANALYSIS, ["ABC Ltd", "XYZ Ltd"]
        )
        self.assertEqual(
            sections,
            [
                KnowledgeSection.SECTOR_INFORMATION,
                KnowledgeSection.GOVERNMENT_POLICIES,
                KnowledgeSection.COMPANY_INFORMATION,
                KnowledgeSection.BUSINESS_OVERVIEW,
                KnowledgeSection.COMPETITORS,
                KnowledgeSection.SOURCES,
                KnowledgeSection.METADATA,
            ],
        )

    def test_comparison_sections(self):
        sections = self.planner.determine_required_knowledge_sections(
            ResearchCategory.COMPARISON, ["ABC Ltd", "XYZ Ltd"]
        )
        self.assertEqual(
            sections,
            [
                KnowledgeSection.COMPANY_INFORMATION,
                KnowledgeSection.BUSINESS_OVERVIEW,
                KnowledgeSection.FINANCIAL_INFORMATION,
                KnowledgeSection.COMPETITORS,
                KnowledgeSection.MARKET_DATA,
                KnowledgeSection.SOURCES,
                KnowledgeSection.METADATA,
            ],
        )

    def test_every_mandatory_knowledge_model_section_is_present_somewhere(self):
        # Company Information, Business Overview, Sources, and Metadata are
        # mandatory in KNOWLEDGE_MODEL.md; every category-anchored plan
        # should draw on Sources and Metadata at minimum.
        for category in ResearchCategory:
            sections = self.planner.determine_required_knowledge_sections(
                category, ["ABC Ltd"]
            )
            self.assertIn(KnowledgeSection.SOURCES, sections)
            self.assertIn(KnowledgeSection.METADATA, sections)


class TestDetermineCollectorMode(unittest.TestCase):
    def test_collector_mode_is_always_parallel(self):
        planner = ResearchPlanner()
        self.assertEqual(planner.determine_collector_mode(), CollectorMode.PARALLEL)


class TestInvalidInputHandling(unittest.TestCase):
    def setUp(self):
        self.planner = ResearchPlanner()

    def test_empty_topic_is_rejected(self):
        with self.assertRaises(InvalidResearchInputError):
            self.planner.create_research_plan(
                research_profile="ABC Ltd",
                research_category=ResearchCategory.MARKET_NEWS,
                research_topic="   ",
            )

    def test_empty_profile_is_rejected(self):
        with self.assertRaises(InvalidResearchInputError):
            self.planner.create_research_plan(
                research_profile=[],
                research_category=ResearchCategory.MARKET_NEWS,
                research_topic="Latest announcement.",
            )

    def test_blank_profile_identifier_is_rejected(self):
        with self.assertRaises(InvalidResearchInputError):
            self.planner.create_research_plan(
                research_profile=["   "],
                research_category=ResearchCategory.MARKET_NEWS,
                research_topic="Latest announcement.",
            )

    def test_invalid_category_string_is_rejected(self):
        with self.assertRaises(InvalidResearchInputError):
            self.planner.create_research_plan(
                research_profile="ABC Ltd",
                research_category="Not A Real Category",
                research_topic="Latest announcement.",
            )

    def test_stock_analysis_rejects_multiple_companies(self):
        with self.assertRaises(InvalidResearchInputError):
            self.planner.create_research_plan(
                research_profile=["ABC Ltd", "XYZ Ltd"],
                research_category=ResearchCategory.STOCK_ANALYSIS,
                research_topic="Full analysis.",
            )

    def test_market_news_rejects_multiple_companies(self):
        with self.assertRaises(InvalidResearchInputError):
            self.planner.create_research_plan(
                research_profile=["ABC Ltd", "XYZ Ltd"],
                research_category=ResearchCategory.MARKET_NEWS,
                research_topic="Latest announcement.",
            )

    def test_comparison_rejects_a_single_company(self):
        with self.assertRaises(InvalidResearchInputError):
            self.planner.create_research_plan(
                research_profile=["ABC Ltd"],
                research_category=ResearchCategory.COMPARISON,
                research_topic="Compare margins.",
            )

    def test_comparison_accepts_two_companies(self):
        plan = self.planner.create_research_plan(
            research_profile=["ABC Ltd", "XYZ Ltd"],
            research_category=ResearchCategory.COMPARISON,
            research_topic="Compare margins.",
        )
        self.assertEqual(plan.research_profile, ["ABC Ltd", "XYZ Ltd"])

    def test_sector_analysis_accepts_a_single_representative_company(self):
        plan = self.planner.create_research_plan(
            research_profile=["ABC Ltd"],
            research_category=ResearchCategory.SECTOR_ANALYSIS,
            research_topic="Outlook for the sector.",
        )
        self.assertEqual(plan.research_profile, ["ABC Ltd"])

    def test_invalid_input_never_produces_a_plan(self):
        planner = ResearchPlanner()
        sequence_before = planner._sequence
        with self.assertRaises(InvalidResearchInputError):
            planner.create_research_plan(
                research_profile=[],
                research_category=ResearchCategory.MARKET_NEWS,
                research_topic="",
            )
        self.assertEqual(planner._sequence, sequence_before)


class TestPlannerHasNoForeignDependencies(unittest.TestCase):
    def test_planner_module_only_imports_from_itself_and_stdlib(self):
        import ast
        import pathlib

        module_path = (
            pathlib.Path(__file__).resolve().parents[2]
            / "research_engine"
            / "planner"
            / "research_planner.py"
        )
        tree = ast.parse(module_path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.level == 0 and not node.module.startswith(
                    ("dataclasses", "datetime", "enum", "typing", "__future__")
                ):
                    self.fail(f"Unexpected absolute import: {node.module}")
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    self.assertIn(
                        alias.name.split(".")[0],
                        {"dataclasses", "datetime", "enum", "typing"},
                    )


if __name__ == "__main__":
    unittest.main()
