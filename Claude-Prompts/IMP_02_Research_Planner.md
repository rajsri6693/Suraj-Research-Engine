# Research Engine
# IMP-02 - Research Planner Implementation
# Version 1.0

Read and execute this document completely.

Work ONLY inside the current repository.

Do NOT modify anything outside this repository.

--------------------------------------------------

OBJECTIVE

Implement the Research Planner module.

The Research Planner converts a Research Input into a Human-readable Research Plan.

It is a pure decision engine.

It NEVER performs research.

It NEVER calls APIs.

It NEVER writes to the database.

It NEVER verifies knowledge.

--------------------------------------------------

SOURCE OF TRUTH

Use ONLY:

project_documentation/RESEARCH_INPUT_STANDARD.md

project_documentation/RESEARCH_PLANNER.md

project_documentation/KNOWLEDGE_MODEL.md

--------------------------------------------------

IMPLEMENT ONLY

Create:

research_engine/planner/

    __init__.py

    research_plan.py

    research_planner.py

--------------------------------------------------

RESEARCH PLAN

Implement a ResearchPlan dataclass.

It must contain:

• Research ID

• Research Profile

• Research Category

• Research Topic

• Research Depth

• Research Priority

• Required Knowledge Sections

• Collector Mode

• Planner Status

• Created Time

--------------------------------------------------

RESEARCH PLANNER

Implement ResearchPlanner.

It must provide:

1.

Create Research Plan

Input

Research Profile

Research Category

Research Topic

Output

ResearchPlan

--------------------------------------------------

2.

Determine Research Depth

Quick Research

Deep Research

--------------------------------------------------

3.

Determine Research Priority

High

Medium

Low

--------------------------------------------------

4.

Determine Required Knowledge Sections

Based ONLY on

Research Category

Research Profile

Knowledge Model

--------------------------------------------------

5.

Determine Collector Mode

Parallel

--------------------------------------------------

RULES

The Planner must NEVER

Perform research

Call APIs

Call Collectors

Call Workflow

Access Database

Verify Knowledge

Generate Scripts

Generate Videos

--------------------------------------------------

IMPLEMENTATION RULES

Keep the Planner completely independent.

No dependency on any future module.

Only standard Python.

--------------------------------------------------

UNIT TESTS

Create comprehensive tests.

Verify:

Research Plan creation

Research Depth selection

Priority selection

Knowledge Section selection

Collector Mode

Invalid input handling

--------------------------------------------------

VERIFY

Confirm:

1.

Planner module created successfully.

2.

All unit tests pass.

3.

Python compilation passes.

4.

No other Research Engine module modified.

5.

No database changes.

6.

No SQLite.

7.

Planner follows RESEARCH_PLANNER.md exactly.

Print the final report.