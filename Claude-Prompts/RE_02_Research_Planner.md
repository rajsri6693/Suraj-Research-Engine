# Research Engine
# RE-02 - Research Planner
# Version 1.0

Read and execute this document completely.

Work ONLY inside the current repository.

Do NOT modify anything outside this repository.

--------------------------------------------------

OBJECTIVE

Design the Research Planner.

The Research Planner is the decision-making component of the Research Engine.

It does NOT perform research.

It does NOT call APIs.

It does NOT access the database.

It ONLY converts Research Input into a Human-readable Research Plan.

--------------------------------------------------

SOURCE OF TRUTH

Use ONLY:

project_documentation/KNOWLEDGE_MODEL.md

project_documentation/RESEARCH_INPUT_STANDARD.md

--------------------------------------------------

TASK

Create ONLY:

project_documentation/RESEARCH_PLANNER.md

--------------------------------------------------

The document must define:

1.

Purpose of the Research Planner.

--------------------------------------------------

2.

Planner Input

Research Profile

Research Category

Research Topic

--------------------------------------------------

3.

Planner Output

Human-readable Research Plan.

--------------------------------------------------

4.

Research Depth Rules

Quick Research

Deep Research

--------------------------------------------------

5.

Knowledge Selection Rules

Define which Knowledge Model sections are required for each Research Category.

Categories:

• Market News

• Stock Update

• Stock Analysis

• Sector Analysis

• Comparison

--------------------------------------------------

6.

Research Priority

High

Medium

Low

Explain how priority is assigned.

--------------------------------------------------

7.

Research Mode

Parallel Collectors

Explain why collectors work in parallel.

--------------------------------------------------

8.

Planner Restrictions

The Planner must NEVER:

Perform research

Call APIs

Save data

Verify data

Generate scripts

Generate videos

Modify the database

--------------------------------------------------

9.

Planner Output Example

Create one complete Human-readable Research Plan example.

--------------------------------------------------

RULES

Documentation only.

No Python.

No SQLite.

No AI implementation.

No API implementation.

No code.

--------------------------------------------------

VERIFY

Confirm:

1.

Only RESEARCH_PLANNER.md created.

2.

No Python modified.

3.

No Database modified.

4.

No Schema modified.

5.

Only current repository modified.

Print the final report.