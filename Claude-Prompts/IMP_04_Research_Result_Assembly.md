# Research Engine
# IMP-04 - Research Result Assembly Implementation
# Version 1.0

Read and execute this document completely.

Work ONLY inside the current repository.

Do NOT modify anything outside this repository.

--------------------------------------------------

OBJECTIVE

Implement the Research Result Assembly module.

The Research Result Assembly combines Collector Results into one unified Research Package.

It NEVER performs research.

It NEVER verifies knowledge.

It NEVER approves knowledge.

It NEVER writes to the database.

--------------------------------------------------

SOURCE OF TRUTH

Use ONLY:

project_documentation/RESEARCH_RESULT_ASSEMBLY.md

project_documentation/RESEARCH_WORKFLOW.md

project_documentation/RESEARCH_SESSION.md

project_documentation/KNOWLEDGE_MODEL.md

--------------------------------------------------

IMPLEMENT ONLY

Create:

research_engine/assembly/

    __init__.py

    collector_result.py

    research_package.py

    result_assembly.py

--------------------------------------------------

IMPLEMENT

CollectorResult dataclass

Fields:

• Collector Name

• Knowledge Section

• Collected Knowledge

• Sources

• Collection Time

• Collector Status

--------------------------------------------------

ResearchPackage dataclass

Fields:

• Research ID

• Research Session

• Research Topic

• Research Profile

• Research Category

• Knowledge Sections

• Collector Summary

• Missing Sections

• Overall Collection Status

• Collection Completed Time

--------------------------------------------------

ResearchResultAssembly

Implement:

1.

Create Research Package

Input:

Collector Results

Research Session

Research Plan

Output:

Research Package

--------------------------------------------------

2.

Merge Collector Results

--------------------------------------------------

3.

Preserve Sources

--------------------------------------------------

4.

Preserve Metadata

--------------------------------------------------

5.

Identify Missing Sections

--------------------------------------------------

6.

Generate Collector Summary

--------------------------------------------------

7.

Determine Overall Collection Status

--------------------------------------------------

RULES

The Assembly module must NEVER

Perform research

Call APIs

Verify knowledge

Approve knowledge

Modify collected knowledge

Access database

Generate scripts

Generate videos

--------------------------------------------------

IMPLEMENTATION RULES

Use only standard Python.

No dependency on future modules.

May depend only on:

Research Session

Research Plan

Workflow State

--------------------------------------------------

UNIT TESTS

Create comprehensive tests.

Verify:

Research Package creation

Collector Result merge

Missing Section detection

Collector Summary generation

Overall Status generation

Source preservation

Metadata preservation

Invalid input handling

--------------------------------------------------

VERIFY

Confirm:

1.

Assembly module created successfully.

2.

All unit tests pass.

3.

Python compilation passes.

4.

No Session module modified.

5.

No Planner module modified.

6.

No Workflow module modified.

7.

No Database modified.

8.

No SQLite.

9.

Assembly follows RESEARCH_RESULT_ASSEMBLY.md exactly.

Print the final report.