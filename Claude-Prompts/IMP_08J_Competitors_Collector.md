# Research Engine
# IMP-08J - Competitors Collector Implementation
# Version 1.0

Read and execute this document completely.

Work ONLY inside the current repository.

Do NOT modify anything outside this repository.

--------------------------------------------------

OBJECTIVE

Implement the Competitors Collector.

Its responsibility is ONLY to collect Competitor information and return a CompetitorResult.

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

research_engine/collectors/competitors/

    __init__.py

    competitors_collector.py

    competitor_result.py

--------------------------------------------------

IMPLEMENT

CompetitorResult dataclass

Fields:

• Company Name

• Competitor Name

• Industry

• Comparison Summary

• Competitive Strengths

• Competitive Weaknesses

• Market Position

• Market Share

• Sources

• Collection Time

• Collector Status

--------------------------------------------------

CompetitorsCollector

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

CompetitorResult

--------------------------------------------------

IMPORTANT

This phase DOES NOT perform live research.

collect() must return a valid CompetitorResult using placeholder/mock values only.

The objective is to validate the Collector architecture and Competitor data contract.

--------------------------------------------------

RULES

Competitors Collector must NEVER

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

1. Competitors Collector created successfully.

2. All unit tests pass.

3. Python compilation passes.

4. Company Collector unchanged.

5. Financial Collector unchanged.

6. Market News Collector unchanged.

7. Sector Collector unchanged.

8. Technical Analysis Collector unchanged.

9. Government Policy Collector unchanged.

10. Historical Price Collector unchanged.

11. Corporate Action Collector unchanged.

12. Orders & Contracts Collector unchanged.

13. Collector Framework unchanged.

14. Session unchanged.

15. Planner unchanged.

16. Workflow unchanged.

17. Assembly unchanged.

18. Verification unchanged.

19. Human Review unchanged.

20. Database unchanged.

21. No SQLite.

22. No external APIs used.

Print the final report.