"""Unit tests for research_engine.integration.integration_engine."""

import unittest

from research_engine.assembly.collector_result import CollectorStatus as AssemblyCollectorStatus
from research_engine.assembly.research_package import (
    OverallCollectionStatus,
    ResearchPackage,
    SectionStatus,
)
from research_engine.chart.chart_generator import GeneratedChart
from research_engine.integration.integration_engine import (
    IntegrationEngine,
    IntegrationResult,
)
from research_engine.integration.review_package import (
    HumanReviewPackage,
    ReviewPackageStatus,
)
from research_engine.planner.research_plan import KnowledgeSection, ResearchCategory
from research_engine.planner.research_planner import ResearchPlanner
from research_engine.review.review_decision import ReviewDecision
from research_engine.verification.verification_report import OverallVerificationStatus
from research_engine.workflow.workflow_state import WorkflowStage, WorkflowStatus


def make_stock_analysis_plan():
    return ResearchPlanner().create_research_plan(
        research_profile="Sample Manufacturing Ltd (SMFG, NSE)",
        research_category=ResearchCategory.STOCK_ANALYSIS,
        research_topic="Full analysis ahead of quarterly results next week.",
    )


def make_market_news_plan():
    return ResearchPlanner().create_research_plan(
        research_profile="Sample Manufacturing Ltd (SMFG, NSE)",
        research_category=ResearchCategory.MARKET_NEWS,
        research_topic="Latest announcement.",
    )


def make_chart_requested_plan():
    return ResearchPlanner().create_research_plan(
        research_profile="Sample Manufacturing Ltd (SMFG, NSE)",
        research_category=ResearchCategory.STOCK_ANALYSIS,
        research_topic="BEL analysis with chart",
    )


class TestResearchPlanExecutesCorrectly(unittest.TestCase):
    def test_run_returns_a_fully_formed_integration_result(self):
        plan = make_stock_analysis_plan()
        result = IntegrationEngine().run(plan)

        self.assertIsInstance(result, IntegrationResult)
        self.assertEqual(
            result.research_session.research_topic,
            "Full analysis ahead of quarterly results next week.",
        )
        self.assertEqual(
            result.research_package.research_session,
            result.research_session.research_id,
        )
        self.assertEqual(
            result.verification_report.research_id, result.research_session.research_id
        )
        self.assertEqual(
            result.human_review_package.research_id, result.verification_report.research_id
        )


class TestCollectorsExecuteInCorrectOrder(unittest.TestCase):
    def test_workflow_reaches_ready_for_human_review(self):
        plan = make_stock_analysis_plan()
        result = IntegrationEngine().run(plan)

        self.assertEqual(
            result.workflow_state.current_stage, WorkflowStage.READY_FOR_HUMAN_REVIEW
        )
        self.assertEqual(
            result.workflow_state.workflow_status, WorkflowStatus.READY_FOR_HUMAN_REVIEW
        )
        self.assertIsNotNone(result.workflow_state.finished_time)

    def test_only_sections_with_a_real_collector_are_registered_and_completed(self):
        plan = make_stock_analysis_plan()
        result = IntegrationEngine().run(plan)

        # Business Overview and Market Data have no real collector
        # implementation among the sixteen built so far.
        self.assertIn(
            KnowledgeSection.FINANCIAL_INFORMATION,
            result.workflow_state.completed_collectors,
        )
        self.assertIn(
            KnowledgeSection.COMPANY_INFORMATION,
            result.workflow_state.completed_collectors,
        )
        self.assertNotIn(
            KnowledgeSection.BUSINESS_OVERVIEW,
            result.workflow_state.active_collectors
            | result.workflow_state.completed_collectors
            | result.workflow_state.failed_collectors,
        )


class TestResearchPackageCreated(unittest.TestCase):
    def test_package_contains_one_entry_per_required_section(self):
        plan = make_stock_analysis_plan()
        result = IntegrationEngine().run(plan)

        self.assertIsInstance(result.research_package, ResearchPackage)
        self.assertEqual(
            [entry.knowledge_section for entry in result.research_package.knowledge_sections],
            plan.required_knowledge_sections,
        )

    def test_sections_without_a_real_collector_are_reported_missing(self):
        plan = make_stock_analysis_plan()
        result = IntegrationEngine().run(plan)

        missing_sections = {
            entry.knowledge_section for entry in result.research_package.missing_sections
        }
        self.assertIn(KnowledgeSection.BUSINESS_OVERVIEW, missing_sections)
        self.assertIn(KnowledgeSection.MARKET_DATA, missing_sections)

        business_overview_entry = next(
            entry
            for entry in result.research_package.knowledge_sections
            if entry.knowledge_section == KnowledgeSection.BUSINESS_OVERVIEW
        )
        self.assertEqual(business_overview_entry.status, SectionStatus.MISSING)

    def test_sections_with_a_real_collector_are_completed_with_adapted_data(self):
        plan = make_stock_analysis_plan()
        result = IntegrationEngine().run(plan)

        financial_entry = next(
            entry
            for entry in result.research_package.knowledge_sections
            if entry.knowledge_section == KnowledgeSection.FINANCIAL_INFORMATION
        )
        self.assertEqual(financial_entry.status, SectionStatus.COMPLETED)
        self.assertIsNotNone(financial_entry.collected_knowledge)
        self.assertIn("FinancialResult", financial_entry.collected_knowledge)
        self.assertTrue(len(financial_entry.sources) > 0)

    def test_collector_status_is_correctly_adapted_to_assembly_type(self):
        plan = make_market_news_plan()
        result = IntegrationEngine().run(plan)

        summary_row = result.research_package.collector_summary[0]
        self.assertIsInstance(summary_row.execution_status, AssemblyCollectorStatus)
        self.assertEqual(summary_row.execution_status, AssemblyCollectorStatus.SUCCESS)

    def test_market_news_plan_has_no_missing_sections(self):
        # Company Information, Market News, Sources, and Metadata all
        # have real collectors, so a Market News plan should fully
        # succeed with nothing missing.
        plan = make_market_news_plan()
        result = IntegrationEngine().run(plan)

        self.assertEqual(result.research_package.missing_sections, [])
        self.assertEqual(
            result.research_package.overall_collection_status,
            OverallCollectionStatus.COMPLETE,
        )


class TestVerificationExecuted(unittest.TestCase):
    def test_verification_report_reflects_completed_sections_as_verified(self):
        plan = make_stock_analysis_plan()
        result = IntegrationEngine().run(plan)

        self.assertIn(
            KnowledgeSection.FINANCIAL_INFORMATION,
            result.verification_report.verified_sections,
        )
        self.assertIn(
            KnowledgeSection.COMPANY_INFORMATION,
            result.verification_report.verified_sections,
        )

    def test_missing_sections_are_reflected_as_failed_in_verification(self):
        plan = make_stock_analysis_plan()
        result = IntegrationEngine().run(plan)

        self.assertIn(
            KnowledgeSection.BUSINESS_OVERVIEW, result.verification_report.failed_sections
        )

    def test_market_news_plan_verifies_fully(self):
        plan = make_market_news_plan()
        result = IntegrationEngine().run(plan)

        self.assertEqual(
            result.verification_report.overall_status, OverallVerificationStatus.VERIFIED
        )


class TestHumanReviewPackageProduced(unittest.TestCase):
    def test_review_package_lists_every_verified_section_as_eligible(self):
        plan = make_stock_analysis_plan()
        result = IntegrationEngine().run(plan)

        self.assertEqual(result.human_review_package.review_decision, ReviewDecision.SKIPPED)
        self.assertIsNone(result.human_review_package.reviewed_by)
        self.assertEqual(
            set(result.human_review_package.reviewed_sections),
            set(result.verification_report.verified_sections),
        )


class TestIntegrationEngineIsReusable(unittest.TestCase):
    def test_two_runs_produce_two_distinct_sessions(self):
        engine = IntegrationEngine()
        first = engine.run(make_market_news_plan())
        second = engine.run(make_market_news_plan())
        self.assertNotEqual(
            first.research_session.research_id, second.research_session.research_id
        )


class TestHumanReviewPackageCreated(unittest.TestCase):
    def test_review_package_is_a_human_review_package(self):
        plan = make_stock_analysis_plan()
        result = IntegrationEngine().run(plan)
        self.assertIsInstance(result.review_package, HumanReviewPackage)

    def test_review_package_carries_the_same_session_plan_and_package(self):
        plan = make_stock_analysis_plan()
        result = IntegrationEngine().run(plan)

        self.assertIs(result.review_package.research_session, result.research_session)
        self.assertIs(result.review_package.research_plan, plan)
        self.assertIs(result.review_package.research_package, result.research_package)

    def test_review_status_is_pending_review_at_handoff(self):
        plan = make_stock_analysis_plan()
        result = IntegrationEngine().run(plan)
        self.assertEqual(
            result.review_package.review_status, ReviewPackageStatus.PENDING_REVIEW
        )


class TestVerificationReportAttachedToReviewPackage(unittest.TestCase):
    def test_verification_report_is_attached(self):
        plan = make_stock_analysis_plan()
        result = IntegrationEngine().run(plan)
        self.assertIs(
            result.review_package.verification_report, result.verification_report
        )


class TestEligibleSectionsCorrect(unittest.TestCase):
    def test_eligible_sections_match_verified_sections(self):
        plan = make_stock_analysis_plan()
        result = IntegrationEngine().run(plan)
        self.assertEqual(
            result.review_package.eligible_sections,
            result.verification_report.verified_sections,
        )

    def test_eligible_sections_exclude_missing_sections(self):
        plan = make_stock_analysis_plan()
        result = IntegrationEngine().run(plan)
        self.assertNotIn(
            KnowledgeSection.BUSINESS_OVERVIEW, result.review_package.eligible_sections
        )
        self.assertNotIn(
            KnowledgeSection.MARKET_DATA, result.review_package.eligible_sections
        )

    def test_eligible_sections_non_empty_for_a_fully_verified_plan(self):
        plan = make_market_news_plan()
        result = IntegrationEngine().run(plan)
        self.assertTrue(len(result.review_package.eligible_sections) > 0)
        self.assertEqual(
            set(result.review_package.eligible_sections),
            set(result.verification_report.verified_sections),
        )


class TestReviewModuleInvokedFromPackage(unittest.TestCase):
    def test_human_review_result_derives_from_the_packages_verification_report(self):
        plan = make_stock_analysis_plan()
        result = IntegrationEngine().run(plan)
        self.assertEqual(
            result.human_review_package.research_id,
            result.review_package.verification_report.research_id,
        )

    def test_human_review_reviewed_sections_match_package_eligible_sections(self):
        plan = make_stock_analysis_plan()
        result = IntegrationEngine().run(plan)
        self.assertEqual(
            set(result.human_review_package.reviewed_sections),
            set(result.review_package.eligible_sections),
        )


class TestChartGenerationSkippedWhenNotRequired(unittest.TestCase):
    def test_generated_chart_is_none_when_chart_not_required(self):
        plan = make_stock_analysis_plan()
        self.assertFalse(plan.chart_required)
        result = IntegrationEngine().run(plan)
        self.assertIsNone(result.generated_chart)

    def test_review_package_reports_chart_unavailable_when_chart_not_required(self):
        plan = make_stock_analysis_plan()
        result = IntegrationEngine().run(plan)
        self.assertFalse(result.review_package.chart_available)
        self.assertIsNone(result.review_package.chart_type)
        self.assertIsNone(result.review_package.chart_dataset)


class TestChartGenerationRunsWhenRequired(unittest.TestCase):
    def test_plan_from_a_chart_keyword_topic_has_chart_required_true(self):
        plan = make_chart_requested_plan()
        self.assertTrue(plan.chart_required)

    def test_generated_chart_is_produced_when_chart_required(self):
        plan = make_chart_requested_plan()
        result = IntegrationEngine().run(plan)
        self.assertIsInstance(result.generated_chart, GeneratedChart)

    def test_review_package_exposes_chart_available_type_and_dataset(self):
        plan = make_chart_requested_plan()
        result = IntegrationEngine().run(plan)

        self.assertTrue(result.review_package.chart_available)
        self.assertEqual(
            result.review_package.chart_type, result.generated_chart.chart_type
        )
        self.assertEqual(
            result.review_package.chart_dataset, result.generated_chart.price_dataset
        )


if __name__ == "__main__":
    unittest.main()
