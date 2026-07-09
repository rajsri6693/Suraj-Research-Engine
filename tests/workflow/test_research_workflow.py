"""Unit tests for research_engine.workflow.research_workflow."""

import unittest

from research_engine.planner.research_plan import KnowledgeSection, ResearchCategory
from research_engine.planner.research_planner import ResearchPlanner
from research_engine.session.session_manager import SessionManager
from research_engine.workflow.research_workflow import (
    CollectorRegistrationError,
    InvalidWorkflowTransitionError,
    ResearchWorkflow,
    is_valid_stage_transition,
)
from research_engine.workflow.workflow_state import WorkflowStage, WorkflowStatus


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


def start_workflow_at_stage_three(workflow: ResearchWorkflow):
    workflow.advance_stage()  # Stage 1 -> Stage 2
    workflow.advance_stage()  # Stage 2 -> Stage 3
    return workflow


class TestIsValidStageTransition(unittest.TestCase):
    def test_full_forward_path_is_valid_one_step_at_a_time(self):
        ordered = [
            WorkflowStage.RECEIVE_RESEARCH_PLAN,
            WorkflowStage.IDENTIFY_REQUIRED_COLLECTORS,
            WorkflowStage.RUN_COLLECTORS_IN_PARALLEL,
            WorkflowStage.COLLECT_RESULTS,
            WorkflowStage.RESEARCH_RESULT_ASSEMBLY,
            WorkflowStage.VERIFICATION,
            WorkflowStage.KNOWLEDGE_STORAGE,
            WorkflowStage.KNOWLEDGE_VIEWER,
            WorkflowStage.READY_FOR_HUMAN_REVIEW,
        ]
        for current, nxt in zip(ordered, ordered[1:]):
            self.assertTrue(is_valid_stage_transition(current, nxt), f"{current} -> {nxt}")

    def test_skipping_a_stage_is_invalid(self):
        self.assertFalse(
            is_valid_stage_transition(
                WorkflowStage.RECEIVE_RESEARCH_PLAN,
                WorkflowStage.RUN_COLLECTORS_IN_PARALLEL,
            )
        )

    def test_backward_move_off_the_one_permitted_exception_is_invalid(self):
        self.assertFalse(
            is_valid_stage_transition(
                WorkflowStage.RESEARCH_RESULT_ASSEMBLY,
                WorkflowStage.IDENTIFY_REQUIRED_COLLECTORS,
            )
        )

    def test_revision_loop_transition_is_valid(self):
        self.assertTrue(
            is_valid_stage_transition(
                WorkflowStage.READY_FOR_HUMAN_REVIEW,
                WorkflowStage.RUN_COLLECTORS_IN_PARALLEL,
            )
        )

    def test_same_stage_is_invalid(self):
        self.assertFalse(
            is_valid_stage_transition(
                WorkflowStage.COLLECT_RESULTS, WorkflowStage.COLLECT_RESULTS
            )
        )


class TestStartWorkflow(unittest.TestCase):
    def test_start_workflow_produces_initial_state(self):
        session, plan = make_session_and_plan()
        workflow = ResearchWorkflow()
        state = workflow.start_workflow(session, plan)

        self.assertEqual(state.research_id, session.research_id)
        self.assertEqual(state.current_stage, WorkflowStage.RECEIVE_RESEARCH_PLAN)
        self.assertEqual(state.workflow_status, WorkflowStatus.RUNNING)
        self.assertIsNotNone(state.started_time)
        self.assertIsNone(state.finished_time)
        self.assertEqual(state.active_collectors, set())

    def test_state_property_raises_before_start(self):
        workflow = ResearchWorkflow()
        with self.assertRaises(InvalidWorkflowTransitionError):
            _ = workflow.state

    def test_research_plan_property_raises_before_start(self):
        workflow = ResearchWorkflow()
        with self.assertRaises(InvalidWorkflowTransitionError):
            _ = workflow.research_plan


class TestAdvanceStage(unittest.TestCase):
    def setUp(self):
        session, plan = make_session_and_plan()
        self.workflow = ResearchWorkflow()
        self.workflow.start_workflow(session, plan)

    def test_advance_stage_moves_to_natural_next_stage(self):
        state = self.workflow.advance_stage()
        self.assertEqual(state.current_stage, WorkflowStage.IDENTIFY_REQUIRED_COLLECTORS)

    def test_advance_stage_walks_the_full_pre_assembly_path(self):
        self.workflow.advance_stage()  # Stage 2
        self.workflow.advance_stage()  # Stage 3
        self.workflow.advance_stage()  # Stage 4
        state = self.workflow.advance_stage()  # Stage 5
        self.assertEqual(state.current_stage, WorkflowStage.RESEARCH_RESULT_ASSEMBLY)

    def test_advance_stage_from_ready_for_human_review_with_no_target_raises(self):
        self._advance_to_ready_for_human_review()
        with self.assertRaises(InvalidWorkflowTransitionError):
            self.workflow.advance_stage()

    def test_advance_stage_rejects_skipping_a_stage(self):
        with self.assertRaises(InvalidWorkflowTransitionError):
            self.workflow.advance_stage(WorkflowStage.RUN_COLLECTORS_IN_PARALLEL)

    def test_advance_stage_rejects_arbitrary_backward_move(self):
        self.workflow.advance_stage()
        self.workflow.advance_stage()
        self.workflow.advance_stage()
        self.workflow.advance_stage()  # now at Stage 5
        with self.assertRaises(InvalidWorkflowTransitionError):
            self.workflow.advance_stage(WorkflowStage.COLLECT_RESULTS)

    def test_advance_stage_blocks_verification_until_assembly_ready(self):
        self.workflow.advance_stage()
        self.workflow.advance_stage()
        self.workflow.advance_stage()
        self.workflow.advance_stage()  # Stage 5, nothing registered
        with self.assertRaises(InvalidWorkflowTransitionError):
            self.workflow.advance_stage(WorkflowStage.VERIFICATION)

    def _advance_to_ready_for_human_review(self):
        while self.workflow.state.current_stage != WorkflowStage.READY_FOR_HUMAN_REVIEW:
            if self.workflow.state.current_stage == WorkflowStage.RUN_COLLECTORS_IN_PARALLEL:
                for section in self.workflow.research_plan.required_knowledge_sections:
                    self.workflow.register_collector(section)
                    self.workflow.mark_collector_complete(section)
            self.workflow.advance_stage()
        return self.workflow.state


class TestRegisterCollector(unittest.TestCase):
    def setUp(self):
        session, plan = make_session_and_plan()
        self.workflow = ResearchWorkflow()
        self.workflow.start_workflow(session, plan)

    def test_register_collector_requires_stage_three(self):
        with self.assertRaises(CollectorRegistrationError):
            self.workflow.register_collector(KnowledgeSection.FINANCIAL_INFORMATION)

    def test_register_collector_at_stage_three_succeeds(self):
        start_workflow_at_stage_three(self.workflow)
        state = self.workflow.register_collector(KnowledgeSection.FINANCIAL_INFORMATION)
        self.assertIn(KnowledgeSection.FINANCIAL_INFORMATION, state.active_collectors)

    def test_register_collector_rejects_a_section_outside_the_plan(self):
        start_workflow_at_stage_three(self.workflow)
        # Market News is not part of a Stock Analysis plan's required sections.
        with self.assertRaises(CollectorRegistrationError):
            self.workflow.register_collector(KnowledgeSection.MARKET_NEWS)

    def test_register_collector_rejects_a_section_already_completed(self):
        start_workflow_at_stage_three(self.workflow)
        self.workflow.register_collector(KnowledgeSection.FINANCIAL_INFORMATION)
        self.workflow.mark_collector_complete(KnowledgeSection.FINANCIAL_INFORMATION)
        with self.assertRaises(CollectorRegistrationError):
            self.workflow.register_collector(KnowledgeSection.FINANCIAL_INFORMATION)


class TestMarkCollectorComplete(unittest.TestCase):
    def setUp(self):
        session, plan = make_session_and_plan()
        self.workflow = ResearchWorkflow()
        self.workflow.start_workflow(session, plan)
        start_workflow_at_stage_three(self.workflow)

    def test_mark_complete_moves_section_from_active_to_completed(self):
        self.workflow.register_collector(KnowledgeSection.FINANCIAL_INFORMATION)
        state = self.workflow.mark_collector_complete(
            KnowledgeSection.FINANCIAL_INFORMATION
        )
        self.assertNotIn(KnowledgeSection.FINANCIAL_INFORMATION, state.active_collectors)
        self.assertIn(KnowledgeSection.FINANCIAL_INFORMATION, state.completed_collectors)

    def test_mark_complete_on_unregistered_section_raises(self):
        with self.assertRaises(CollectorRegistrationError):
            self.workflow.mark_collector_complete(KnowledgeSection.FINANCIAL_INFORMATION)


class TestMarkCollectorFailed(unittest.TestCase):
    def setUp(self):
        session, plan = make_session_and_plan()
        self.workflow = ResearchWorkflow()
        self.workflow.start_workflow(session, plan)
        start_workflow_at_stage_three(self.workflow)

    def test_mark_failed_moves_section_from_active_to_failed(self):
        self.workflow.register_collector(KnowledgeSection.TECHNICAL_ANALYSIS)
        state = self.workflow.mark_collector_failed(KnowledgeSection.TECHNICAL_ANALYSIS)
        self.assertNotIn(KnowledgeSection.TECHNICAL_ANALYSIS, state.active_collectors)
        self.assertIn(KnowledgeSection.TECHNICAL_ANALYSIS, state.failed_collectors)

    def test_one_collector_failing_does_not_affect_others(self):
        self.workflow.register_collector(KnowledgeSection.TECHNICAL_ANALYSIS)
        self.workflow.register_collector(KnowledgeSection.FINANCIAL_INFORMATION)
        self.workflow.mark_collector_failed(KnowledgeSection.TECHNICAL_ANALYSIS)
        state = self.workflow.state
        self.assertIn(KnowledgeSection.FINANCIAL_INFORMATION, state.active_collectors)
        self.assertIn(KnowledgeSection.TECHNICAL_ANALYSIS, state.failed_collectors)

    def test_mark_failed_on_unregistered_section_raises(self):
        with self.assertRaises(CollectorRegistrationError):
            self.workflow.mark_collector_failed(KnowledgeSection.TECHNICAL_ANALYSIS)


class TestAssemblyReadiness(unittest.TestCase):
    def setUp(self):
        session, plan = make_session_and_plan()
        self.workflow = ResearchWorkflow()
        self.workflow.start_workflow(session, plan)
        start_workflow_at_stage_three(self.workflow)

    def test_not_ready_when_nothing_registered(self):
        self.assertFalse(self.workflow.is_assembly_ready())

    def test_not_ready_while_any_collector_still_active(self):
        self.workflow.register_collector(KnowledgeSection.FINANCIAL_INFORMATION)
        self.workflow.register_collector(KnowledgeSection.TECHNICAL_ANALYSIS)
        self.workflow.mark_collector_complete(KnowledgeSection.FINANCIAL_INFORMATION)
        self.assertFalse(self.workflow.is_assembly_ready())

    def test_ready_once_every_registered_collector_reaches_a_final_outcome(self):
        self.workflow.register_collector(KnowledgeSection.FINANCIAL_INFORMATION)
        self.workflow.register_collector(KnowledgeSection.TECHNICAL_ANALYSIS)
        self.workflow.mark_collector_complete(KnowledgeSection.FINANCIAL_INFORMATION)
        self.workflow.mark_collector_failed(KnowledgeSection.TECHNICAL_ANALYSIS)
        self.assertTrue(self.workflow.is_assembly_ready())

    def test_unregistered_required_sections_do_not_block_readiness(self):
        # Only one of the plan's twelve required sections is registered
        # and completed this pass -- the rest are implicitly Skipped.
        self.workflow.register_collector(KnowledgeSection.FINANCIAL_INFORMATION)
        self.workflow.mark_collector_complete(KnowledgeSection.FINANCIAL_INFORMATION)
        self.assertTrue(self.workflow.is_assembly_ready())


class TestMoveToVerification(unittest.TestCase):
    def setUp(self):
        session, plan = make_session_and_plan()
        self.workflow = ResearchWorkflow()
        self.workflow.start_workflow(session, plan)
        start_workflow_at_stage_three(self.workflow)
        self.workflow.advance_stage()  # Stage 4
        self.workflow.advance_stage()  # Stage 5

    def test_move_to_verification_blocked_until_ready(self):
        with self.assertRaises(InvalidWorkflowTransitionError):
            self.workflow.move_to_verification()

    def test_move_to_verification_succeeds_once_ready(self):
        # Registering collectors requires Stage 3, so this uses a fresh
        # workflow driven correctly through Stage 3 collection first,
        # rather than the Stage-5 workflow this class's setUp produces.
        session, plan = make_session_and_plan()
        workflow = ResearchWorkflow()
        workflow.start_workflow(session, plan)
        start_workflow_at_stage_three(workflow)
        for section in plan.required_knowledge_sections:
            workflow.register_collector(section)
            workflow.mark_collector_complete(section)
        workflow.advance_stage()  # Stage 4
        workflow.advance_stage()  # Stage 5
        state = workflow.move_to_verification()
        self.assertEqual(state.current_stage, WorkflowStage.VERIFICATION)

    def test_move_to_verification_from_wrong_stage_raises(self):
        session, plan = make_session_and_plan()
        workflow = ResearchWorkflow()
        workflow.start_workflow(session, plan)
        with self.assertRaises(InvalidWorkflowTransitionError):
            workflow.move_to_verification()


class TestFullForwardPass(unittest.TestCase):
    def test_reaches_ready_for_human_review_with_finished_time_set(self):
        session, plan = make_session_and_plan()
        workflow = ResearchWorkflow()
        workflow.start_workflow(session, plan)

        workflow.advance_stage()  # Stage 2
        workflow.advance_stage()  # Stage 3
        for section in plan.required_knowledge_sections:
            workflow.register_collector(section)
            workflow.mark_collector_complete(section)
        workflow.advance_stage()  # Stage 4
        workflow.advance_stage()  # Stage 5
        workflow.move_to_verification()  # Stage 6
        workflow.advance_stage()  # Stage 7
        workflow.advance_stage()  # Stage 8
        state = workflow.advance_stage()  # Stage 9

        self.assertEqual(state.current_stage, WorkflowStage.READY_FOR_HUMAN_REVIEW)
        self.assertEqual(state.workflow_status, WorkflowStatus.READY_FOR_HUMAN_REVIEW)
        self.assertIsNotNone(state.finished_time)


class TestRevisionLoop(unittest.TestCase):
    def _drive_to_ready_for_human_review(self, workflow, plan):
        workflow.advance_stage()  # Stage 2
        workflow.advance_stage()  # Stage 3
        for section in plan.required_knowledge_sections:
            workflow.register_collector(section)
            workflow.mark_collector_complete(section)
        workflow.advance_stage()  # Stage 4
        workflow.advance_stage()  # Stage 5
        workflow.move_to_verification()  # Stage 6
        workflow.advance_stage()  # Stage 7
        workflow.advance_stage()  # Stage 8
        return workflow.advance_stage()  # Stage 9

    def test_needs_revision_reenters_at_stage_three_and_clears_collector_state(self):
        session, plan = make_session_and_plan()
        workflow = ResearchWorkflow()
        workflow.start_workflow(session, plan)
        self._drive_to_ready_for_human_review(workflow, plan)

        state = workflow.advance_stage(WorkflowStage.RUN_COLLECTORS_IN_PARALLEL)

        self.assertEqual(state.current_stage, WorkflowStage.RUN_COLLECTORS_IN_PARALLEL)
        self.assertEqual(state.workflow_status, WorkflowStatus.RUNNING)
        self.assertIsNone(state.finished_time)
        self.assertEqual(state.active_collectors, set())
        self.assertEqual(state.completed_collectors, set())
        self.assertEqual(state.failed_collectors, set())

    def test_revision_pass_can_reach_ready_for_human_review_again(self):
        session, plan = make_session_and_plan()
        workflow = ResearchWorkflow()
        workflow.start_workflow(session, plan)
        self._drive_to_ready_for_human_review(workflow, plan)
        workflow.advance_stage(WorkflowStage.RUN_COLLECTORS_IN_PARALLEL)

        # Only the flagged section is re-collected this pass; every other
        # required section is implicitly Skipped and does not block
        # readiness.
        flagged_section = plan.required_knowledge_sections[0]
        workflow.register_collector(flagged_section)
        workflow.mark_collector_complete(flagged_section)
        workflow.advance_stage()  # Stage 4
        workflow.advance_stage()  # Stage 5
        self.assertTrue(workflow.is_assembly_ready())
        workflow.move_to_verification()  # Stage 6
        workflow.advance_stage()  # Stage 7
        workflow.advance_stage()  # Stage 8
        state = workflow.advance_stage()  # Stage 9

        self.assertEqual(state.current_stage, WorkflowStage.READY_FOR_HUMAN_REVIEW)
        self.assertIsNotNone(state.finished_time)


class TestWorkflowHasOnlyAllowedDependencies(unittest.TestCase):
    def test_workflow_module_only_imports_session_planner_and_stdlib(self):
        import ast
        import pathlib

        allowed_stdlib = {
            "dataclasses",
            "datetime",
            "enum",
            "typing",
            "__future__",
        }
        allowed_relative_or_internal = {
            "research_engine.planner.research_plan",
            "research_engine.session.research_session",
        }

        package_dir = (
            pathlib.Path(__file__).resolve().parents[2]
            / "research_engine"
            / "workflow"
        )
        for module_path in package_dir.glob("*.py"):
            tree = ast.parse(module_path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    if node.level > 0:
                        continue  # relative import within this package
                    if node.module in allowed_relative_or_internal:
                        continue
                    if node.module in allowed_stdlib:
                        continue
                    self.fail(
                        f"{module_path.name}: unexpected import '{node.module}'"
                    )
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
