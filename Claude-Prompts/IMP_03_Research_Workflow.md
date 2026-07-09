# Research Engine
# IMP-03 - Research Workflow Implementation
# Version 1.0

Read and execute this document completely.

Work ONLY inside the current repository.

Do NOT modify anything outside this repository.

--------------------------------------------------

OBJECTIVE

Implement the Research Workflow module.

The Research Workflow coordinates the execution of the Research Engine.

It NEVER performs research.

It NEVER calls external APIs.

It NEVER verifies knowledge.

It NEVER writes directly to the database.

--------------------------------------------------

SOURCE OF TRUTH

Use ONLY:

project_documentation/RESEARCH_WORKFLOW.md

project_documentation/RESEARCH_SESSION.md

project_documentation/RESEARCH_PLANNER.md

project_documentation/RESEARCH_RESULT_ASSEMBLY.md

--------------------------------------------------

IMPLEMENT ONLY

Create:

research_engine/workflow/

    __init__.py

    workflow_state.py

    research_workflow.py

--------------------------------------------------

WORKFLOW STATE

Implement a WorkflowState dataclass.

It must contain:

• Research ID

• Current Stage

• Workflow Status

• Active Collectors

• Completed Collectors

• Failed Collectors

• Started Time

• Finished Time

--------------------------------------------------

RESEARCH WORKFLOW

Implement ResearchWorkflow.

It must provide:

1.

Start Workflow

Input:

Research Session

Research Plan

Output:

WorkflowState

--------------------------------------------------

2.

Advance Stage

Move through the defined workflow stages.

--------------------------------------------------

3.

Register Collector

Register a collector for execution.

(No collector implementation.)

--------------------------------------------------

4.

Mark Collector Complete

Update workflow state.

--------------------------------------------------

5.

Mark Collector Failed

Update workflow state.

--------------------------------------------------

6.

Determine Assembly Readiness

Return True only when all required collectors have either:

Completed

Failed

Skipped

--------------------------------------------------

7.

Move to Verification Stage

Only after Assembly Ready.

--------------------------------------------------

RULES

Workflow must NEVER

Perform research

Call APIs

Implement collectors

Verify knowledge

Approve knowledge

Access database

Generate scripts

Generate videos

--------------------------------------------------

IMPLEMENTATION RULES

Keep Workflow completely independent.

No dependency on future modules.

Only standard Python.

The workflow may depend only on:

Research Session

Research Plan

--------------------------------------------------

UNIT TESTS

Create comprehensive tests.

Verify:

Workflow creation

Stage transitions

Collector registration

Collector completion

Collector failure

Assembly readiness

Invalid transitions

--------------------------------------------------

VERIFY

Confirm:

1.

Workflow module created successfully.

2.

All unit tests pass.

3.

Python compilation passes.

4.

No Session module modified.

5.

No Planner module modified.

6.

No Database modified.

7.

No SQLite.

8.

Workflow follows RESEARCH_WORKFLOW.md exactly.

Print the final report.