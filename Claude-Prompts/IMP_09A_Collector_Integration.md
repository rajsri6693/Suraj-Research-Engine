# Research Engine
# IMP-09A - Collector Integration
# Version 1.0

Read and execute this document completely.

Work ONLY inside the current repository.

Do NOT modify anything outside this repository.

--------------------------------------------------

OBJECTIVE

Integrate the completed Research Engine components into one end-to-end execution pipeline.

This phase connects:

Research Planner
↓

Workflow

↓

Collector Factory

↓

Collector Registry

↓

Collectors

↓

Research Result Assembly

↓

Knowledge Verification

↓

Human Review

It DOES NOT implement live APIs.

It DOES NOT implement Script Generation.

--------------------------------------------------

SOURCE OF TRUTH

Use ONLY

project_documentation/

RESEARCH_WORKFLOW.md

RESEARCH_PLANNER.md

RESEARCH_RESULT_ASSEMBLY.md

KNOWLEDGE_VERIFICATION.md

HUMAN_REVIEW.md

RESEARCH_SESSION.md

--------------------------------------------------

IMPLEMENT

Create

research_engine/integration/

    __init__.py

    integration_engine.py

--------------------------------------------------

Responsibilities

Integration Engine must

1.

Receive ResearchPlan

2.

Create Research Session

3.

Determine required collectors

4.

Execute collectors in workflow order

5.

Collect all Collector Results

6.

Generate Research Package

7.

Run Knowledge Verification

8.

Produce Human Review Package

9.

Return final Integration Result

--------------------------------------------------

DO NOT

Run APIs

Access Internet

Generate Scripts

Generate Videos

Modify Database

--------------------------------------------------

UNIT TESTS

Verify

Research Plan executes correctly

Collectors execute in correct order

Research Package created

Verification executed

Human Review Package produced

All existing tests continue to pass

--------------------------------------------------

VERIFY

Confirm

1. Integration Engine created

2. Existing modules unchanged

3. All tests pass

4. Compilation passes

5. No database modified

6. No SQLite

7. No APIs

Print the final report.