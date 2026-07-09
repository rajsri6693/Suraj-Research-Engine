"""
Research Workflow

Implements ResearchWorkflow, the coordinator defined in
project_documentation/RESEARCH_WORKFLOW.md. It moves a WorkflowState
through the nine Execution Stages for one Research Session's Research
Plan.

It NEVER performs research, calls external APIs, implements collectors,
verifies knowledge, approves knowledge, accesses a database, or generates
scripts or videos. Per IMP-03's Implementation Rules, it depends only on
Research Session and Research Plan — nothing from any other module.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from research_engine.planner.research_plan import KnowledgeSection, ResearchPlan
from research_engine.session.research_session import ResearchSession

from .workflow_state import (
    REVISION_LOOP_TRANSITION,
    STAGE_ORDER,
    WorkflowStage,
    WorkflowState,
    WorkflowStatus,
)


class InvalidWorkflowTransitionError(Exception):
    """Raised when a Stage change would violate the transition rules
    defined in RESEARCH_WORKFLOW.md Section 4 (Execution Stages) or
    Section 9 (Revision Loop)."""


class CollectorRegistrationError(Exception):
    """Raised when a collector operation does not match the Research
    Plan's Required Knowledge Sections or the Workflow's current state."""


def is_valid_stage_transition(current: WorkflowStage, target: WorkflowStage) -> bool:
    """Return whether moving from `current` to `target` is legal.

    Enforces RESEARCH_WORKFLOW.md Section 4's forward order and Section
    9's one permitted backward transition (the Revision Loop). This check
    is stage-order only — it does not evaluate Assembly Readiness, which
    is stateful and checked separately by ResearchWorkflow.advance_stage.
    """
    if target == current:
        return False
    if (current, target) == REVISION_LOOP_TRANSITION:
        return True
    try:
        current_index = STAGE_ORDER.index(current)
        target_index = STAGE_ORDER.index(target)
    except ValueError:
        return False
    return target_index == current_index + 1


class ResearchWorkflow:
    """Coordinates one Research Workflow run for one Research Session and
    Research Plan.

    Holds the Research Session and Research Plan it was started with only
    to read their identity and Required Knowledge Sections — it never
    modifies either, and never calls back into the Session or Planner
    modules' own logic.
    """

    def __init__(self) -> None:
        self._state: Optional[WorkflowState] = None
        self._research_plan: Optional[ResearchPlan] = None

    @property
    def state(self) -> WorkflowState:
        """The current WorkflowState. Raises if the workflow has not
        been started yet."""
        if self._state is None:
            raise InvalidWorkflowTransitionError(
                "Workflow has not been started; call start_workflow first."
            )
        return self._state

    @property
    def research_plan(self) -> ResearchPlan:
        """The Research Plan this workflow run was started with."""
        if self._research_plan is None:
            raise InvalidWorkflowTransitionError(
                "Workflow has not been started; call start_workflow first."
            )
        return self._research_plan

    def start_workflow(
        self, research_session: ResearchSession, research_plan: ResearchPlan
    ) -> WorkflowState:
        """Start Workflow.

        Input: Research Session, Research Plan, per RESEARCH_WORKFLOW.md
        Section 2 (Workflow Input). Output: a fresh WorkflowState at
        Stage 1 - Receive Research Plan.
        """
        self._research_plan = research_plan
        self._state = WorkflowState(
            research_id=research_session.research_id,
            current_stage=WorkflowStage.RECEIVE_RESEARCH_PLAN,
            workflow_status=WorkflowStatus.RUNNING,
            started_time=datetime.now(),
        )
        return self._state

    def advance_stage(
        self, target_stage: Optional[WorkflowStage] = None
    ) -> WorkflowState:
        """Advance Stage.

        Moves through the defined Execution Stages, per
        RESEARCH_WORKFLOW.md Section 4. With no argument, advances to the
        natural next stage in sequence. With `target_stage` given,
        attempts that specific transition instead — used for the
        Revision Loop's Stage 9 -> Stage 3 re-entry, per Section 9.

        Moving from Research Result Assembly (Stage 5) to Verification
        (Stage 6) additionally requires Assembly Readiness (see
        is_assembly_ready / move_to_verification).
        """
        current = self.state.current_stage

        if target_stage is None:
            current_index = STAGE_ORDER.index(current)
            if current_index + 1 >= len(STAGE_ORDER):
                raise InvalidWorkflowTransitionError(
                    f"'{current.value}' has no natural next stage; Ready for Human "
                    "Review is terminal for a forward pass. Pass "
                    "target_stage=WorkflowStage.RUN_COLLECTORS_IN_PARALLEL for a "
                    "Revision Loop re-entry."
                )
            target_stage = STAGE_ORDER[current_index + 1]

        if not is_valid_stage_transition(current, target_stage):
            raise InvalidWorkflowTransitionError(
                f"Cannot move Research Workflow from '{current.value}' to "
                f"'{target_stage.value}'."
            )

        if (
            current == WorkflowStage.RESEARCH_RESULT_ASSEMBLY
            and target_stage == WorkflowStage.VERIFICATION
            and not self.is_assembly_ready()
        ):
            raise InvalidWorkflowTransitionError(
                "Cannot move to Verification before Assembly Readiness is "
                "reached -- every registered collector must have left Active "
                "Collectors."
            )

        is_revision_reentry = (current, target_stage) == REVISION_LOOP_TRANSITION
        self.state.current_stage = target_stage

        if is_revision_reentry:
            # A fresh Revision Loop pass only re-registers the flagged
            # section; every other required section is carried forward,
            # Skipped, per RESEARCH_RESULT_ASSEMBLY.md Section 6 -- so
            # this pass's collector tracking starts clean.
            self.state.active_collectors = set()
            self.state.completed_collectors = set()
            self.state.failed_collectors = set()
            self.state.workflow_status = WorkflowStatus.RUNNING
            self.state.finished_time = None
        elif target_stage == WorkflowStage.READY_FOR_HUMAN_REVIEW:
            self.state.workflow_status = WorkflowStatus.READY_FOR_HUMAN_REVIEW
            self.state.finished_time = datetime.now()

        return self.state

    def move_to_verification(self) -> WorkflowState:
        """Move to Verification Stage.

        Only valid from Research Result Assembly (Stage 5), and only once
        Assembly Readiness has been reached, per RESEARCH_WORKFLOW.md
        Section 6 (Verification Rules) / IMP-03 item 7. A thin, explicitly
        named wrapper around advance_stage's own Stage 5 -> Stage 6 gate.
        """
        return self.advance_stage(WorkflowStage.VERIFICATION)

    def register_collector(self, section: KnowledgeSection) -> WorkflowState:
        """Register Collector.

        Registers a collector for execution against one Required
        Knowledge Section of the Research Plan, per RESEARCH_WORKFLOW.md
        Stage 3 (Run Collectors in Parallel). No collector implementation
        is included here -- this only tracks that a section's collector
        has been triggered.
        """
        if self.state.current_stage != WorkflowStage.RUN_COLLECTORS_IN_PARALLEL:
            raise CollectorRegistrationError(
                "Collectors can only be registered while at Stage 3 - Run "
                f"Collectors in Parallel; workflow is at "
                f"'{self.state.current_stage.value}'."
            )
        if section not in self.research_plan.required_knowledge_sections:
            raise CollectorRegistrationError(
                f"'{section.value}' is not a Required Knowledge Section of this "
                "Research Plan."
            )
        if (
            section in self.state.completed_collectors
            or section in self.state.failed_collectors
        ):
            raise CollectorRegistrationError(
                f"'{section.value}' has already reached a final outcome this pass."
            )
        self.state.active_collectors.add(section)
        return self.state

    def mark_collector_complete(self, section: KnowledgeSection) -> WorkflowState:
        """Mark Collector Complete.

        Moves a section from Active Collectors to Completed Collectors,
        per RESEARCH_WORKFLOW.md Section 4 (Collect Results).
        """
        self._require_active(section)
        self.state.active_collectors.discard(section)
        self.state.completed_collectors.add(section)
        return self.state

    def mark_collector_failed(self, section: KnowledgeSection) -> WorkflowState:
        """Mark Collector Failed.

        Moves a section from Active Collectors to Failed Collectors, per
        RESEARCH_WORKFLOW.md Section 5 (Failure Handling) -- a failed
        collector produces no result, and never blocks the others.
        """
        self._require_active(section)
        self.state.active_collectors.discard(section)
        self.state.failed_collectors.add(section)
        return self.state

    def is_assembly_ready(self) -> bool:
        """Determine Assembly Readiness.

        True only once every collector registered this pass has left
        Active Collectors, reaching Completed or Failed, and at least one
        collector was registered this pass. A required Knowledge Section
        never registered this pass -- every section but the one being
        revised, during a Revision Loop pass -- is implicitly Skipped,
        per RESEARCH_RESULT_ASSEMBLY.md Section 6, and never blocks
        readiness, because it was never Active to begin with.
        """
        state = self.state
        attempted_something = bool(state.completed_collectors) or bool(
            state.failed_collectors
        )
        return len(state.active_collectors) == 0 and attempted_something

    def _require_active(self, section: KnowledgeSection) -> None:
        if section not in self.state.active_collectors:
            raise CollectorRegistrationError(
                f"'{section.value}' is not an Active Collector for this workflow."
            )
