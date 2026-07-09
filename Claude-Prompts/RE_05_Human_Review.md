# Research Engine
# RE-05 - Human Review
# Version 1.0

Read and execute this document completely.

Work ONLY inside the current repository.

Do NOT modify anything outside this repository.

--------------------------------------------------

OBJECTIVE

Design the Human Review stage of the Research Engine.

The Human Review stage is the final decision point before knowledge is marked as Approved.

Human Review NEVER performs research.

Human Review NEVER verifies facts.

Human Review ONLY reviews the verified knowledge collected by the Research Engine.

--------------------------------------------------

SOURCE OF TRUTH

Use ONLY:

project_documentation/KNOWLEDGE_MODEL.md

project_documentation/RESEARCH_INPUT_STANDARD.md

project_documentation/RESEARCH_PLANNER.md

project_documentation/RESEARCH_WORKFLOW.md

project_documentation/KNOWLEDGE_VERIFICATION.md

--------------------------------------------------

TASK

Create ONLY:

project_documentation/HUMAN_REVIEW.md

--------------------------------------------------

The document must define

1.

Purpose of Human Review.

--------------------------------------------------

2.

Review Input

Verified Knowledge

Verification Report

Sources

Metadata

--------------------------------------------------

3.

Review Output

Approved

Rejected

Needs Revision

--------------------------------------------------

4.

Review Screen

Define exactly what the reviewer should see.

Include:

Research Topic

Research Category

Research Profile

Knowledge Sections

Verification Status

Sources

Confidence

Last Updated

--------------------------------------------------

5.

Reviewer Actions

Approve

Reject

Request Revision

Skip

Explain each action.

--------------------------------------------------

6.

Approval Rules

Only Human can approve.

The Research Engine can NEVER approve knowledge.

--------------------------------------------------

7.

Approval Status

Pending Review

Approved

Rejected

Needs Revision

Explain every status.

--------------------------------------------------

8.

Restrictions

Human Review must NEVER

Perform research

Modify collected knowledge

Generate scripts

Generate videos

Call APIs

Write directly to the database

--------------------------------------------------

9.

Human Review Example

Create one complete Human-readable review screen example.

--------------------------------------------------

RULES

Documentation only.

No Python.

No SQLite.

No implementation.

No code.

--------------------------------------------------

VERIFY

Confirm:

1. Only HUMAN_REVIEW.md created.

2. No Python modified.

3. No Database modified.

4. No Schema modified.

5. Only current repository modified.

Print the final report.