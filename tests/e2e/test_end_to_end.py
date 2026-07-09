"""End-to-end integration tests for the Research Engine, per
Claude-Prompts/IMP_09E_End_To_End_Test.md.

Each scenario below drives the real pipeline --

    Research Topic -> Research Planner -> Research Session -> Workflow
    -> Collector Integration -> Collectors -> Research Result Assembly
    -> Knowledge Verification -> Human Review Package -> Human Review
    -> Approval -> Database Persistence -> Telegram Notification

-- through its real, already-implemented components. This is a TEST
ONLY phase: no architecture is modified here, and Telegram is
configured Enabled with its outbound network call replaced by
in-memory recording, so real send() logic runs end-to-end without ever
reaching a real Telegram server. Every database write uses an
isolated, temp-file-backed DatabaseManager -- never the real project
database file.
"""

import os
import tempfile
import unittest
from datetime import datetime

from research_engine.approval.approval_service import ApprovalService
from research_engine.assembly.research_package import (
    OverallCollectionStatus,
    SectionStatus,
)
from research_engine.chart.chart_generator import GeneratedChart
from research_engine.collectors.base_collector import BaseCollector
from research_engine.integration.integration_engine import IntegrationEngine
from research_engine.notifications.telegram_notification import (
    TelegramConfig,
    TelegramNotificationService,
)
from research_engine.planner.research_plan import (
    CollectorMode,
    KnowledgeSection,
    PlannerStatus,
    ResearchCategory,
    ResearchDepth,
    ResearchPlan,
    ResearchPriority,
)
from research_engine.planner.research_planner import ResearchPlanner
from research_engine.review.human_review import HumanReview, InvalidReviewError
from research_engine.review.review_decision import ReviewDecision
from research_engine.verification.verification_report import OverallVerificationStatus
from research_engine.workflow.workflow_state import WorkflowStage, WorkflowStatus
from research_database.database_manager import DatabaseError, DatabaseManager


class RecordingTelegramNotificationService(TelegramNotificationService):
    """A TelegramNotificationService configured Enabled, with its actual
    outbound network call replaced by in-memory recording, so this
    end-to-end suite exercises real send() logic -- the Enabled/Bot
    Token/Chat ID gate, message construction, the "Chart Included"
    line -- without ever reaching a real Telegram server. `calls`
    records every send() invocation, in order, so a scenario can assert
    a notification was (or was never) triggered at all."""

    def __init__(self):
        super().__init__(
            TelegramConfig(enabled=True, bot_token="e2e-test-token", chat_id="e2e-test-chat")
        )
        self.calls = []

    def send(self, **kwargs):
        result = super().send(**kwargs)
        self.calls.append(kwargs)
        return result

    def _send_via_telegram_api(self, message: str) -> None:
        return  # No real network call in this end-to-end suite.


def make_isolated_database_manager() -> DatabaseManager:
    """A temp-file-backed DatabaseManager, isolated from the real
    project database file, matching the pattern already established in
    tests/approval/test_approval_service.py."""
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    os.remove(db_path)  # DatabaseManager creates it on first use.
    manager = DatabaseManager(db_path)
    manager.e2e_db_path = db_path  # type: ignore[attr-defined]
    return manager


def close_isolated_database_manager(manager: DatabaseManager) -> None:
    manager.close()
    db_path = getattr(manager, "e2e_db_path", None)
    if db_path and os.path.exists(db_path):
        os.remove(db_path)


def run_pipeline(
    research_topic: str,
    research_category: ResearchCategory = ResearchCategory.STOCK_ANALYSIS,
    research_profile="BEL",
):
    """Drive Research Topic through Research Planner and the full
    IntegrationEngine pipeline: Research Session -> Workflow ->
    Collector Integration -> Collectors -> Research Result Assembly ->
    Knowledge Verification -> Human Review Package. Returns
    (plan, integration_result, engine)."""
    plan = ResearchPlanner().create_research_plan(
        research_profile=research_profile,
        research_category=research_category,
        research_topic=research_topic,
    )
    engine = IntegrationEngine()
    integration_result = engine.run(plan)
    return plan, integration_result, engine


def make_verification_failure_plan() -> ResearchPlan:
    """A ResearchPlan requiring Business Overview and Market Data
    (neither has a registered real collector among the sixteen built so
    far, so both come back Missing and Rejected) alongside Sources
    (which does have a real collector, so at least one collector is
    attempted this pass -- every real Planner-produced plan always
    includes at least Sources and Metadata, per
    _REQUIRED_SECTIONS_BY_CATEGORY, so this mirrors what a genuine
    Research Plan looks like when most, but not all, of its required
    sections cannot be collected)."""
    return ResearchPlan(
        research_id="RP-E2E-SCENARIO6",
        research_profile=["BEL"],
        research_category=ResearchCategory.STOCK_ANALYSIS,
        research_topic="BEL",
        research_depth=ResearchDepth.DEEP,
        depth_reason="End-to-end Scenario 6 fixture.",
        research_priority=ResearchPriority.MEDIUM,
        priority_reason="End-to-end Scenario 6 fixture.",
        required_knowledge_sections=[
            KnowledgeSection.BUSINESS_OVERVIEW,
            KnowledgeSection.MARKET_DATA,
            KnowledgeSection.SOURCES,
        ],
        collector_mode=CollectorMode.PARALLEL,
        planner_status=PlannerStatus.CREATED,
        created_time=datetime.now(),
        chart_required=False,
    )


class FailingFinancialCollector(BaseCollector):
    """A stand-in collector that always raises, so Scenario 5 can
    exercise IntegrationEngine's real per-collector failure handling
    without altering any production collector."""

    @property
    def collector_name(self) -> str:
        return "Failing Financial Collector (E2E Scenario 5)"

    @property
    def knowledge_section(self) -> str:
        return "Financial Information"

    def collect(self, research_topic: str):
        raise RuntimeError("Simulated collector failure for E2E Scenario 5.")


class Scenario1NoChartTestCase(unittest.TestCase):
    """SCENARIO 1: Input "BEL" -- full pipeline through Approval, with
    no chart requested."""

    @classmethod
    def setUpClass(cls):
        cls.plan, cls.integration_result, cls.engine = run_pipeline("BEL")

        cls.reviewer = HumanReview()
        cls.review_result = cls.reviewer.approve(
            cls.integration_result.verification_report,
            cls.integration_result.verification_report.verified_sections,
            reviewed_by="qa.reviewer",
            review_notes="E2E Scenario 1 approval.",
        )

        cls.database_manager = make_isolated_database_manager()
        cls.notifier = RecordingTelegramNotificationService()
        cls.approval_service = ApprovalService(
            database_manager=cls.database_manager, notifier=cls.notifier
        )
        cls.outcome = cls.approval_service.process(
            cls.review_result,
            research_topic=cls.plan.research_topic,
            research_category=cls.plan.research_category.value,
            chart_available=cls.integration_result.review_package.chart_available,
            chart_type=cls.integration_result.review_package.chart_type,
        )

    @classmethod
    def tearDownClass(cls):
        close_isolated_database_manager(cls.database_manager)

    def test_planner_executes(self):
        self.assertEqual(self.plan.research_topic, "BEL")
        self.assertFalse(self.plan.chart_required)

    def test_session_created(self):
        self.assertEqual(
            self.integration_result.research_session.research_topic, "BEL"
        )

    def test_workflow_completes(self):
        self.assertEqual(
            self.integration_result.workflow_state.current_stage,
            WorkflowStage.READY_FOR_HUMAN_REVIEW,
        )
        self.assertEqual(
            self.integration_result.workflow_state.workflow_status,
            WorkflowStatus.READY_FOR_HUMAN_REVIEW,
        )
        self.assertIsNotNone(self.integration_result.workflow_state.finished_time)

    def test_required_collectors_execute(self):
        self.assertIn(
            KnowledgeSection.COMPANY_INFORMATION,
            self.integration_result.workflow_state.completed_collectors,
        )
        self.assertIn(
            KnowledgeSection.FINANCIAL_INFORMATION,
            self.integration_result.workflow_state.completed_collectors,
        )

    def test_research_package_assembled(self):
        self.assertEqual(
            [
                entry.knowledge_section
                for entry in self.integration_result.research_package.knowledge_sections
            ],
            self.plan.required_knowledge_sections,
        )

    def test_verification_completes(self):
        self.assertIn(
            KnowledgeSection.COMPANY_INFORMATION,
            self.integration_result.verification_report.verified_sections,
        )

    def test_human_review_package_created(self):
        self.assertEqual(
            self.integration_result.review_package.research_session,
            self.integration_result.research_session,
        )
        self.assertTrue(len(self.integration_result.review_package.eligible_sections) > 0)

    def test_approval_succeeds(self):
        self.assertTrue(self.outcome.persisted)

    def test_database_updated(self):
        rows = self.database_manager.fetch_all(
            "SELECT * FROM approved_research WHERE research_id = ?",
            (self.review_result.research_id,),
        )
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["chart_available"], 0)

    def test_telegram_notification_sent_only_after_persistence(self):
        self.assertTrue(self.outcome.persisted)
        self.assertEqual(len(self.notifier.calls), 1)
        self.assertTrue(self.outcome.notified)
        self.assertTrue(self.outcome.notification.sent)

    def test_chart_not_generated(self):
        self.assertIsNone(self.integration_result.generated_chart)
        self.assertFalse(self.integration_result.review_package.chart_available)
        self.assertIn("Chart Included: No", self.outcome.notification.message)


class Scenario2WithChartTestCase(unittest.TestCase):
    """SCENARIO 2: Input "BEL with chart" -- chart_required=True drives
    Historical Price -> Technical Analysis -> Chart Generator, and the
    chart is carried through Human Review and Approval."""

    @classmethod
    def setUpClass(cls):
        cls.plan, cls.integration_result, cls.engine = run_pipeline("BEL with chart")

        cls.reviewer = HumanReview()
        cls.review_result = cls.reviewer.approve(
            cls.integration_result.verification_report,
            cls.integration_result.verification_report.verified_sections,
            reviewed_by="qa.reviewer",
            review_notes="E2E Scenario 2 approval.",
        )

        cls.database_manager = make_isolated_database_manager()
        cls.notifier = RecordingTelegramNotificationService()
        cls.approval_service = ApprovalService(
            database_manager=cls.database_manager, notifier=cls.notifier
        )
        cls.outcome = cls.approval_service.process(
            cls.review_result,
            research_topic=cls.plan.research_topic,
            research_category=cls.plan.research_category.value,
            chart_available=cls.integration_result.review_package.chart_available,
            chart_type=cls.integration_result.review_package.chart_type,
        )

    @classmethod
    def tearDownClass(cls):
        close_isolated_database_manager(cls.database_manager)

    def test_chart_required_true(self):
        self.assertTrue(self.plan.chart_required)

    def test_historical_price_and_technical_analysis_collectors_executed(self):
        self.assertIn(
            KnowledgeSection.HISTORICAL_PRICE_OHLC,
            self.integration_result.workflow_state.completed_collectors,
        )
        self.assertIn(
            KnowledgeSection.TECHNICAL_ANALYSIS,
            self.integration_result.workflow_state.completed_collectors,
        )

    def test_chart_generator_executed_even_when_not_part_of_required_sections(self):
        # Market News's required sections never include Historical Price
        # or Technical Analysis, per the Planner's own category table --
        # proving Chart Generator runs from chart_required alone, not
        # from what the Research Plan otherwise required.
        market_news_plan, market_news_result, _ = run_pipeline(
            "BEL with chart", research_category=ResearchCategory.MARKET_NEWS
        )
        self.assertNotIn(
            KnowledgeSection.HISTORICAL_PRICE_OHLC,
            market_news_plan.required_knowledge_sections,
        )
        self.assertNotIn(
            KnowledgeSection.TECHNICAL_ANALYSIS,
            market_news_plan.required_knowledge_sections,
        )
        self.assertIsInstance(market_news_result.generated_chart, GeneratedChart)

    def test_chart_attached_to_review_package(self):
        self.assertTrue(self.integration_result.review_package.chart_available)
        self.assertIsInstance(self.integration_result.review_package.chart_type, str)
        self.assertEqual(
            self.integration_result.review_package.chart_dataset,
            self.integration_result.generated_chart.price_dataset,
        )

    def test_chart_metadata_persisted_after_approval(self):
        self.assertTrue(self.outcome.persisted)
        rows = self.database_manager.fetch_all(
            "SELECT * FROM approved_research WHERE research_id = ?",
            (self.review_result.research_id,),
        )
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["chart_available"], 1)
        self.assertEqual(
            rows[0]["chart_type"], self.integration_result.generated_chart.chart_type
        )

    def test_telegram_notification_indicates_chart_included(self):
        self.assertTrue(self.outcome.notified)
        self.assertIn("Chart Included: Yes", self.outcome.notification.message)


class Scenario3RejectedReviewTestCase(unittest.TestCase):
    """SCENARIO 3: A Rejected reviewer decision must never persist or
    notify."""

    @classmethod
    def setUpClass(cls):
        _, integration_result, _ = run_pipeline("BEL")
        reviewer = HumanReview()
        cls.review_result = reviewer.reject(
            integration_result.verification_report,
            integration_result.verification_report.verified_sections,
            reviewed_by="qa.reviewer",
            review_notes="E2E Scenario 3 rejection.",
        )
        cls.database_manager = make_isolated_database_manager()
        cls.notifier = RecordingTelegramNotificationService()
        cls.outcome = ApprovalService(
            database_manager=cls.database_manager, notifier=cls.notifier
        ).process(cls.review_result)

    @classmethod
    def tearDownClass(cls):
        close_isolated_database_manager(cls.database_manager)

    def test_database_not_updated(self):
        self.assertFalse(self.outcome.persisted)
        with self.assertRaises(DatabaseError):
            self.database_manager.fetch_all("SELECT * FROM approved_research")

    def test_telegram_not_sent(self):
        self.assertFalse(self.outcome.notified)
        self.assertEqual(self.notifier.calls, [])


class Scenario4NeedsRevisionTestCase(unittest.TestCase):
    """SCENARIO 4: A Needs Revision reviewer decision starts the
    Revision workflow (Revision Sections populated) and must never
    notify or persist to Approval."""

    @classmethod
    def setUpClass(cls):
        _, integration_result, _ = run_pipeline("BEL")
        reviewer = HumanReview()
        cls.review_result = reviewer.request_revision(
            integration_result.verification_report,
            integration_result.verification_report.verified_sections,
            reviewed_by="qa.reviewer",
            review_notes="E2E Scenario 4 revision request.",
        )
        cls.database_manager = make_isolated_database_manager()
        cls.notifier = RecordingTelegramNotificationService()
        cls.outcome = ApprovalService(
            database_manager=cls.database_manager, notifier=cls.notifier
        ).process(cls.review_result)

    @classmethod
    def tearDownClass(cls):
        close_isolated_database_manager(cls.database_manager)

    def test_revision_workflow_starts(self):
        self.assertEqual(self.review_result.review_decision, ReviewDecision.NEEDS_REVISION)
        self.assertTrue(len(self.review_result.revision_sections) > 0)

    def test_telegram_not_sent(self):
        self.assertFalse(self.outcome.persisted)
        self.assertFalse(self.outcome.notified)
        self.assertEqual(self.notifier.calls, [])


class Scenario5CollectorFailureTestCase(unittest.TestCase):
    """SCENARIO 5: One collector (Financial Information) is replaced
    with one that always raises. The rest of the pipeline must still
    complete."""

    @classmethod
    def setUpClass(cls):
        plan = ResearchPlanner().create_research_plan(
            research_profile="BEL",
            research_category=ResearchCategory.STOCK_ANALYSIS,
            research_topic="BEL",
        )
        engine = IntegrationEngine()
        engine._registry.unregister_collector("Financial Information")
        engine._registry.register_collector(
            "Financial Information", FailingFinancialCollector
        )
        cls.plan = plan
        cls.integration_result = engine.run(plan)

    def test_workflow_continues(self):
        self.assertEqual(
            self.integration_result.workflow_state.workflow_status,
            WorkflowStatus.READY_FOR_HUMAN_REVIEW,
        )

    def test_failure_reported_correctly(self):
        self.assertIn(
            KnowledgeSection.FINANCIAL_INFORMATION,
            self.integration_result.workflow_state.failed_collectors,
        )
        self.assertNotIn(
            KnowledgeSection.FINANCIAL_INFORMATION,
            self.integration_result.workflow_state.completed_collectors,
        )
        failed_entry = next(
            entry
            for entry in self.integration_result.research_package.knowledge_sections
            if entry.knowledge_section == KnowledgeSection.FINANCIAL_INFORMATION
        )
        self.assertEqual(failed_entry.status, SectionStatus.MISSING)
        self.assertIn(
            KnowledgeSection.FINANCIAL_INFORMATION,
            self.integration_result.verification_report.failed_sections,
        )

    def test_remaining_collectors_execute(self):
        self.assertIn(
            KnowledgeSection.COMPANY_INFORMATION,
            self.integration_result.workflow_state.completed_collectors,
        )
        self.assertEqual(
            self.integration_result.research_package.overall_collection_status,
            OverallCollectionStatus.PARTIAL,
        )


class Scenario6VerificationFailureTestCase(unittest.TestCase):
    """SCENARIO 6: A Research Plan where most, but not all, required
    sections cannot be collected -- Verification must reject those
    sections, and Approval must be blocked from acting on them."""

    @classmethod
    def setUpClass(cls):
        cls.plan = make_verification_failure_plan()
        cls.integration_result = IntegrationEngine().run(cls.plan)

    def test_human_review_receives_correct_report(self):
        self.assertEqual(
            self.integration_result.verification_report.overall_status,
            OverallVerificationStatus.PARTIAL,
        )
        self.assertIn(
            KnowledgeSection.BUSINESS_OVERVIEW,
            self.integration_result.verification_report.failed_sections,
        )
        self.assertIn(
            KnowledgeSection.MARKET_DATA,
            self.integration_result.verification_report.failed_sections,
        )
        self.assertNotIn(
            KnowledgeSection.BUSINESS_OVERVIEW,
            self.integration_result.review_package.eligible_sections,
        )
        self.assertNotIn(
            KnowledgeSection.MARKET_DATA,
            self.integration_result.review_package.eligible_sections,
        )

    def test_approval_blocked_for_failed_sections(self):
        reviewer = HumanReview()
        with self.assertRaises(InvalidReviewError):
            reviewer.approve(
                self.integration_result.verification_report,
                [KnowledgeSection.BUSINESS_OVERVIEW, KnowledgeSection.MARKET_DATA],
                reviewed_by="qa.reviewer",
            )


if __name__ == "__main__":
    unittest.main()
