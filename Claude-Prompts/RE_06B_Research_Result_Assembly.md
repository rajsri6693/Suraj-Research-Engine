# Research Engine
# RE-06B - Research Result Assembly
# Version 1.0

Read and execute this document completely.

Work ONLY inside the current repository.

Do NOT modify anything outside this repository.

--------------------------------------------------

OBJECTIVE

Design the Research Result Assembly stage.

Research Result Assembly is responsible for combining all Collector Results into one complete Research Package.

It is a stage of the Research Workflow.

It NEVER performs research.

It NEVER verifies knowledge.

It NEVER approves knowledge.

It NEVER writes directly to the database.

--------------------------------------------------

SOURCE OF TRUTH

Use ONLY:

project_documentation/KNOWLEDGE_MODEL.md

project_documentation/RESEARCH_PLANNER.md

project_documentation/RESEARCH_WORKFLOW.md

project_documentation/RESEARCH_COLLECTORS.md

project_documentation/RESEARCH_SESSION.md

--------------------------------------------------

TASK

Create ONLY:

project_documentation/RESEARCH_RESULT_ASSEMBLY.md

--------------------------------------------------

The document must define

1.

Purpose

Explain why Research Result Assembly exists.

--------------------------------------------------

2.

Assembly Input

The Assembly receives only Collector Results.

Each Collector Result contains:

• Knowledge Section

• Collected Knowledge

• Sources

• Collection Time

• Collector Status

--------------------------------------------------

3.

Assembly Output

Create one unified Human-readable Research Package.

The Research Package must contain:

Research Session

Research Topic

Research Profile

Research Category

Knowledge Sections

Collector Summary

Missing Sections

Overall Collection Status

Collection Completed Time

--------------------------------------------------

4.

Assembly Responsibilities

Research Result Assembly MUST:

Combine Collector Results

Preserve every Knowledge Section

Preserve Sources

Preserve Metadata

Report missing sections

Produce one unified Research Package

--------------------------------------------------

5.

Assembly Restrictions

Research Result Assembly must NEVER:

Perform research

Verify knowledge

Approve knowledge

Modify collected knowledge

Generate scripts

Generate videos

Write to the database

Call APIs

--------------------------------------------------

6.

Missing Section Handling

Explain how missing Collector Results are represented.

The Research Package must clearly distinguish:

Completed

Missing

Failed

Skipped

--------------------------------------------------

7.

Collector Summary

Produce one summary showing:

Collector Name

Execution Status

Completion Time

--------------------------------------------------

8.

Workflow Ownership

Clearly state that:

Research Result Assembly belongs to the Research Workflow.

It is NOT an independent workflow.

It executes after all required Collectors finish.

--------------------------------------------------

9.

Research Package Example

Create one complete Human-readable Research Package example.

--------------------------------------------------

RULES

Documentation only.

No Python.

No SQLite.

No implementation.

No API integration.

No code.

--------------------------------------------------

VERIFY

Confirm:

1. Only RESEARCH_RESULT_ASSEMBLY.md created.

2. No Python modified.

3. No Database modified.

4. No Schema modified.

5. Only current repository modified.

6. Research Result Assembly is explicitly defined as a stage of the Research Workflow.

Print the final report.