"""
Workflow State

Implements the WorkflowState data model and the Workflow Stage vocabulary
defined in project_documentation/RESEARCH_WORKFLOW.md. WorkflowState is a
plain record of where one Research Workflow run currently stands — it
performs no research, calls no APIs, verifies nothing, and writes to no
database.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Set

from research_engine.planner.research_plan import KnowledgeSection


class WorkflowStage(Enum):
    """The nine Execution Stages of a Research Workflow run, per
    RESEARCH_WORKFLOW.md Section 4, in order."""

    RECEIVE_RESEARCH_PLAN = "Stage 1 - Receive Research Plan"
    IDENTIFY_REQUIRED_COLLECTORS = "Stage 2 - Identify Required Collectors"
    RUN_COLLECTORS_IN_PARALLEL = "Stage 3 - Run Collectors in Parallel"
    COLLECT_RESULTS = "Stage 4 - Collect Results"
    RESEARCH_RESULT_ASSEMBLY = "Stage 5 - Research Result Assembly"
    VERIFICATION = "Stage 6 - Verification"
    KNOWLEDGE_STORAGE = "Stage 7 - Knowledge Storage"
    KNOWLEDGE_VIEWER = "Stage 8 - Knowledge Viewer"
    READY_FOR_HUMAN_REVIEW = "Stage 9 - Ready for Human Review"


class WorkflowStatus(Enum):
    """Coarse status of a Research Workflow run, alongside Current Stage."""

    RUNNING = "Running"
    READY_FOR_HUMAN_REVIEW = "Ready for Human Review"


# The forward order of the Execution Stages, per RESEARCH_WORKFLOW.md
# Section 4. A workflow may only advance one stage at a time along this
# order, except for the one permitted backward transition below.
STAGE_ORDER = [
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

# The one permitted backward transition: the Revision Loop re-enters at
# Run Collectors in Parallel from Ready for Human Review. See
# RESEARCH_WORKFLOW.md Section 9 (Revision Loop).
REVISION_LOOP_TRANSITION = (
    WorkflowStage.READY_FOR_HUMAN_REVIEW,
    WorkflowStage.RUN_COLLECTORS_IN_PARALLEL,
)


@dataclass
class WorkflowState:
    """Where one Research Workflow run currently stands.

    Fields per IMP-03: Research ID, Current Stage, Workflow Status,
    Active/Completed/Failed Collectors, Started Time, Finished Time.
    Collectors are tracked by the Knowledge Section they were registered
    for, per RESEARCH_PLANNER.md's one-collector-per-section model.
    """

    research_id: str
    current_stage: WorkflowStage
    workflow_status: WorkflowStatus
    started_time: datetime
    active_collectors: Set[KnowledgeSection] = field(default_factory=set)
    completed_collectors: Set[KnowledgeSection] = field(default_factory=set)
    failed_collectors: Set[KnowledgeSection] = field(default_factory=set)
    finished_time: Optional[datetime] = None
