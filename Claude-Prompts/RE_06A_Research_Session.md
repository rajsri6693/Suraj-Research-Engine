# Research Engine
# RE-06A - Research Session
# Version 1.0

Read and execute this document completely.

Work ONLY inside the current repository.

Do NOT modify anything outside this repository.

--------------------------------------------------

OBJECTIVE

Design the Research Session architecture.

A Research Session represents one complete research lifecycle.

It tracks the progress of research from start until Human Review.

It NEVER performs research.

It NEVER verifies knowledge.

It NEVER writes to the database.

--------------------------------------------------

SOURCE OF TRUTH

Use ONLY:

project_documentation/RESEARCH_INPUT_STANDARD.md

project_documentation/RESEARCH_PLANNER.md

project_documentation/RESEARCH_WORKFLOW.md

--------------------------------------------------

TASK

Create ONLY:

project_documentation/RESEARCH_SESSION.md

--------------------------------------------------

The document must define

1.

Purpose of Research Session.

2.

Session Lifecycle.

3.

Session Information.

Research ID

Research Topic

Research Profile

Research Category

Start Time

End Time

Duration

Current Stage

Overall Status

4.

Session Status

Created

Planning

Collecting

Assembling

Verifying

Waiting Human Review

Completed

Failed

Cancelled

5.

Session Rules.

6.

Session Example.

--------------------------------------------------

RULES

Documentation only.

No Python.

No SQLite.

No implementation.

--------------------------------------------------

VERIFY

Confirm:

1. Only RESEARCH_SESSION.md created.

2. No Python modified.

3. No Database modified.

4. No Schema modified.

5. Only current repository modified.

Print the final report.