# Research Engine
# IMP-08D - Sector Collector Implementation
# Version 1.0

Read and execute this document completely.

Work ONLY inside the current repository.

Do NOT modify anything outside this repository.

--------------------------------------------------

OBJECTIVE

Implement the Sector Collector.

Its responsibility is ONLY to collect Sector information and return a SectorResult.

It MUST NOT verify data.

It MUST NOT approve data.

It MUST NOT write to the database.

--------------------------------------------------

SOURCE OF TRUTH

Use ONLY:

project_documentation/KNOWLEDGE_MODEL.md

project_documentation/RESEARCH_COLLECTORS.md

project_documentation/COLLECTOR_SOURCE_STRATEGY.md

--------------------------------------------------

IMPLEMENT ONLY

Create:

research_engine/collectors/sector/

    __init__.py

    sector_collector.py

    sector_result.py

--------------------------------------------------

IMPLEMENT

SectorResult dataclass

Fields:

• Sector Name

• Industry

• Sector Description

• Sector Performance

• Top Companies

• Growth Drivers

• Major Risks

• Related Government Policies

• Sources

• Collection Time

• Collector Status

--------------------------------------------------

SectorCollector

Implement:

1.

Collector Name

2.

Knowledge Section

3.

collect()

Input

Research Topic

Output

SectorResult

--------------------------------------------------

IMPORTANT

This phase DOES NOT perform live research.

collect() must return a valid SectorResult using placeholder/mock values only.

The objective is to validate the Collector architecture and Sector data contract.

--------------------------------------------------

RULES

Sector Collector must NEVER

Call APIs

Access Internet

Perform Verification

Access Database

Write SQLite

Generate Scripts

Generate Videos

Call any other Collector

--------------------------------------------------

IMPLEMENTATION RULES

Use only standard Python.

No HTTP.

No Requests.

No AI.

No external libraries.

--------------------------------------------------

UNIT TESTS

Verify:

Collector creation

Collector metadata

collect() return type

Returned structure validity

Invalid topic handling

--------------------------------------------------

VERIFY

Confirm:

1. Sector Collector created successfully.

2. All unit tests pass.

3. Python compilation passes.

4. Company Collector unchanged.

5. Financial Collector unchanged.

6. Market News Collector unchanged.

7. Collector Framework unchanged.

8. Session unchanged.

9. Planner unchanged.

10. Workflow unchanged.

11. Assembly unchanged.

12. Verification unchanged.

13. Human Review unchanged.

14. Database unchanged.

15. No SQLite.

16. No external APIs used.

Print the final report.