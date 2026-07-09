"""Unit tests for research_engine.workflow.workflow_state."""

import unittest
from datetime import datetime

from research_engine.workflow.workflow_state import (
    REVISION_LOOP_TRANSITION,
    STAGE_ORDER,
    WorkflowStage,
    WorkflowState,
    WorkflowStatus,
)


class TestWorkflowStageVocabulary(unittest.TestCase):
    def test_nine_stages_defined(self):
        self.assertEqual(len(list(WorkflowStage)), 9)

    def test_stage_order_matches_research_workflow_md_section_4(self):
        self.assertEqual(
            STAGE_ORDER,
            [
                WorkflowStage.RECEIVE_RESEARCH_PLAN,
                WorkflowStage.IDENTIFY_REQUIRED_COLLECTORS,
                WorkflowStage.RUN_COLLECTORS_IN_PARALLEL,
                WorkflowStage.COLLECT_RESULTS,
                WorkflowStage.RESEARCH_RESULT_ASSEMBLY,
                WorkflowStage.VERIFICATION,
                WorkflowStage.KNOWLEDGE_STORAGE,
                WorkflowStage.KNOWLEDGE_VIEWER,
                WorkflowStage.READY_FOR_HUMAN_REVIEW,
            ],
        )

    def test_revision_loop_transition_is_ready_for_review_back_to_stage_three(self):
        self.assertEqual(
            REVISION_LOOP_TRANSITION,
            (
                WorkflowStage.READY_FOR_HUMAN_REVIEW,
                WorkflowStage.RUN_COLLECTORS_IN_PARALLEL,
            ),
        )


class TestWorkflowStateConstruction(unittest.TestCase):
    def test_defaults_to_empty_collector_sets_and_no_finished_time(self):
        state = WorkflowState(
            research_id="RS-20260709-001",
            current_stage=WorkflowStage.RECEIVE_RESEARCH_PLAN,
            workflow_status=WorkflowStatus.RUNNING,
            started_time=datetime(2026, 7, 9, 9, 0, 0),
        )
        self.assertEqual(state.active_collectors, set())
        self.assertEqual(state.completed_collectors, set())
        self.assertEqual(state.failed_collectors, set())
        self.assertIsNone(state.finished_time)

    def test_holds_the_fields_imp_03_requires(self):
        state = WorkflowState(
            research_id="RS-20260709-001",
            current_stage=WorkflowStage.RECEIVE_RESEARCH_PLAN,
            workflow_status=WorkflowStatus.RUNNING,
            started_time=datetime(2026, 7, 9, 9, 0, 0),
        )
        for attribute in (
            "research_id",
            "current_stage",
            "workflow_status",
            "active_collectors",
            "completed_collectors",
            "failed_collectors",
            "started_time",
            "finished_time",
        ):
            self.assertTrue(hasattr(state, attribute))


if __name__ == "__main__":
    unittest.main()
