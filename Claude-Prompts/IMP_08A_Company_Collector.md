# Research Engine
# IMP-08A - Company Collector Implementation
# Version 1.0

Read and execute this document completely.

Work ONLY inside the current repository.

Do NOT modify anything outside this repository.

--------------------------------------------------

OBJECTIVE

Implement the Company Collector.

This is the first real Research Collector.

Its responsibility is ONLY to collect Company information and return a Collector Result.

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

research_engine/collectors/company/

    __init__.py

    company_collector.py

    company_result.py

--------------------------------------------------

IMPLEMENT

CompanyResult dataclass

Fields:

• Company Name

• NSE Symbol

• BSE Symbol

• ISIN

• Sector

• Industry

• Headquarters

• Founded Year

• Business Description

• Official Website

• Sources

• Collection Time

• Collector Status

--------------------------------------------------

CompanyCollector

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

CompanyResult

--------------------------------------------------

IMPORTANT

This phase DOES NOT perform live research.

The collect() method must return a valid CompanyResult structure using placeholder/mock values only.

The goal of this phase is to validate the Collector architecture, interfaces, and data contracts—not external data retrieval.

--------------------------------------------------

RULES

Company Collector must NEVER

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

1. Company Collector created successfully.

2. All unit tests pass.

3. Python compilation passes.

4. Collector Framework unchanged.

5. Session unchanged.

6. Planner unchanged.

7. Workflow unchanged.

8. Assembly unchanged.

9. Verification unchanged.

10. Human Review unchanged.

11. Database unchanged.

12. No SQLite.

13. No external APIs used.

Print the final report.