"""
Research Workflow module.

Public entry point for the Research Workflow package, implementing
project_documentation/RESEARCH_WORKFLOW.md.
"""

from .research_workflow import (
    CollectorRegistrationError,
    InvalidWorkflowTransitionError,
    ResearchWorkflow,
    is_valid_stage_transition,
)
from .workflow_state import (
    REVISION_LOOP_TRANSITION,
    STAGE_ORDER,
    WorkflowStage,
    WorkflowState,
    WorkflowStatus,
)

__all__ = [
    "ResearchWorkflow",
    "WorkflowState",
    "WorkflowStage",
    "WorkflowStatus",
    "STAGE_ORDER",
    "REVISION_LOOP_TRANSITION",
    "InvalidWorkflowTransitionError",
    "CollectorRegistrationError",
    "is_valid_stage_transition",
]
