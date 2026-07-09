# Research Engine
# RE-03 - Research Workflow
# Version 1.0

Read and execute this document completely.

Work ONLY inside the current repository.

Do NOT modify anything outside this repository.

--------------------------------------------------

OBJECTIVE

Design the complete execution workflow of the Research Engine.

The Research Workflow is responsible for executing the Research Plan.

It does NOT perform research itself.

It coordinates every stage of the Research Engine.

--------------------------------------------------

SOURCE OF TRUTH

Use ONLY:

project_documentation/RESEARCH_INPUT_STANDARD.md

project_documentation/RESEARCH_PLANNER.md

project_documentation/KNOWLEDGE_MODEL.md

--------------------------------------------------

TASK

Create ONLY:

project_documentation/RESEARCH_WORKFLOW.md

--------------------------------------------------

The document must define

1.

Purpose of the Research Workflow.

--------------------------------------------------

2.

Workflow Input

Research Plan

--------------------------------------------------

3.

Workflow Output

Verified Knowledge ready for Human Review.

--------------------------------------------------

4.

Execution Stages

Stage 1

Receive Research Plan

↓

Stage 2

Identify Required Collectors

↓

Stage 3

Run Collectors in Parallel

↓

Stage 4

Collect Results

↓

Stage 5

Verification

↓

Stage 6

Knowledge Storage

↓

Stage 7

Knowledge Viewer

↓

Stage 8

Ready for Human Review

--------------------------------------------------

5.

Collector Execution Rules

Define:

• Parallel execution

• Collector independence

• Partial completion

• Failure handling

--------------------------------------------------

6.

Verification Rules

Research is NOT stored before verification.

Every knowledge section must have at least one valid source.

Only verified knowledge enters the Knowledge Base.

--------------------------------------------------

7.

Knowledge Storage Rules

Only verified knowledge is stored.

Nothing unverified is written into the database.

--------------------------------------------------

8.

Workflow Restrictions

Workflow must NEVER

Perform research itself

Call APIs directly

Generate scripts

Generate videos

Approve data

Modify user input

--------------------------------------------------

9.

Workflow Example

Create one complete Human-readable workflow example.

--------------------------------------------------

RULES

Documentation only.

No Python.

No SQLite.

No code.

No API implementation.

--------------------------------------------------

VERIFY

Confirm:

1.

Only RESEARCH_WORKFLOW.md created.

2.

No Python modified.

3.

No Database modified.

4.

No Schema modified.

5.

Only current repository modified.

Print the final report.