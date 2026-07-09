# Research Engine
# RE-06 - Research Collectors
# Version 1.0

Read and execute this document completely.

Work ONLY inside the current repository.

Do NOT modify anything outside this repository.

--------------------------------------------------

OBJECTIVE

Design the complete Research Collectors architecture.

Research Collectors are responsible ONLY for collecting knowledge.

They NEVER verify knowledge.

They NEVER approve knowledge.

They NEVER write directly to the database.

--------------------------------------------------

SOURCE OF TRUTH

Use ONLY:

project_documentation/KNOWLEDGE_MODEL.md

project_documentation/RESEARCH_INPUT_STANDARD.md

project_documentation/RESEARCH_PLANNER.md

project_documentation/RESEARCH_WORKFLOW.md

--------------------------------------------------

TASK

Create ONLY:

project_documentation/RESEARCH_COLLECTORS.md

--------------------------------------------------

The document must define

1.

Purpose of Research Collectors.

--------------------------------------------------

2.

Collector Responsibilities.

Collectors ONLY collect information.

No verification.

No approval.

No database writing.

--------------------------------------------------

3.

Collector Selection Rules.

The Research Planner decides which collectors are required.

Collectors never decide themselves.

--------------------------------------------------

4.

Collector Execution.

Collectors run independently.

Collectors may run in parallel.

Failure of one collector must not stop the others.

--------------------------------------------------

5.

Collector Output.

Each collector returns Human-readable collected knowledge.

Every collected item must include:

Knowledge Section

Collected Data

Sources

Collection Time

Collector Status

--------------------------------------------------

6.

Knowledge Sections.

Define which collector is responsible for each section.

Company Information

Business Overview

Products & Services

Management

Shareholding

Financial Information

Orders & Contracts

Competitors

Risks

Market News

Sector

Government Policies

Market Data

Historical Price

Technical Analysis

Corporate Actions

Sources

Metadata

--------------------------------------------------

7.

Collector Restrictions.

Collectors must NEVER

Verify information

Approve information

Generate scripts

Generate videos

Write directly into the database

Modify user input

--------------------------------------------------

8.

Collector Example.

Create one complete Human-readable collector output example.

--------------------------------------------------

RULES

Documentation only.

No Python.

No SQLite.

No API implementation.

No code.

--------------------------------------------------

VERIFY

Confirm:

1. Only RESEARCH_COLLECTORS.md created.

2. No Python modified.

3. No Database modified.

4. No Schema modified.

5. Only current repository modified.

Print the final report.