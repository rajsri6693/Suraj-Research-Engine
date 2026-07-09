# Research Engine
# IMP-08H - Corporate Action Collector Implementation
# Version 1.0

Read and execute this document completely.

Work ONLY inside the current repository.

Do NOT modify anything outside this repository.

--------------------------------------------------

OBJECTIVE

Implement the Corporate Action Collector.

Its responsibility is ONLY to collect Corporate Action information and return a CorporateActionResult.

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

research_engine/collectors/corporate_actions/

    __init__.py

    corporate_action_collector.py

    corporate_action_result.py

--------------------------------------------------

IMPLEMENT

CorporateActionResult dataclass

Fields:

• Action Type

• Action Title

• Announcement Date

• Effective Date

• Record Date

• Description

• Impact Summary

• Related Company

• Sources

• Collection Time

• Collector Status

--------------------------------------------------

CorporateActionCollector

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

CorporateActionResult

--------------------------------------------------

IMPORTANT

This phase DOES NOT perform live research.

collect() must return a valid CorporateActionResult using placeholder/mock values only.

The objective is to validate the Collector architecture and Corporate Action data contract.

--------------------------------------------------

RULES

Corporate Action Collector must NEVER

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

1. Corporate Action Collector created successfully.

2. All unit tests pass.

3. Python compilation passes.

4. Company Collector unchanged.

5. Financial Collector unchanged.

6. Market News Collector unchanged.

7. Sector Collector unchanged.

8. Technical Analysis Collector unchanged.

9. Government Policy Collector unchanged.

10. Historical Price Collector unchanged.

11. Collector Framework unchanged.

12. Session unchanged.

13. Planner unchanged.

14. Workflow unchanged.

15. Assembly unchanged.

16. Verification unchanged.

17. Human Review unchanged.

18. Database unchanged.

19. No SQLite.

20. No external APIs used.

Print the final report.