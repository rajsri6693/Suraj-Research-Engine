# Research Engine
# IMP-08L - Shareholding Collector Implementation
# Version 1.0

Read and execute this document completely.

Work ONLY inside the current repository.

Do NOT modify anything outside this repository.

--------------------------------------------------

OBJECTIVE

Implement the Shareholding Collector.

Its responsibility is ONLY to collect Shareholding information and return a ShareholdingResult.

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

research_engine/collectors/shareholding/

    __init__.py

    shareholding_collector.py

    shareholding_result.py

--------------------------------------------------

IMPLEMENT

ShareholdingResult dataclass

Fields:

• Company Name

• Quarter

• Promoter Holding

• FII Holding

• DII Holding

• Public Holding

• Government Holding

• Insider Holding

• Shareholding Changes

• Share Pledged

• Institutional Holding Summary

• Sources

• Collection Time

• Collector Status

--------------------------------------------------

ShareholdingCollector

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

ShareholdingResult

--------------------------------------------------

IMPORTANT

This phase DOES NOT perform live research.

collect() must return a valid ShareholdingResult using placeholder/mock values only.

The objective is to validate the Collector architecture and Shareholding data contract.

--------------------------------------------------

RULES

Shareholding Collector must NEVER

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

1. Shareholding Collector created successfully.

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

13. Competitors Collector unchanged.

14. Management Collector unchanged.

15. Collector Framework unchanged.

16. Session unchanged.

17. Planner unchanged.

18. Workflow unchanged.

19. Assembly unchanged.

20. Verification unchanged.

21. Human Review unchanged.

22. Database unchanged.

23. No SQLite.

24. No external APIs used.

Print the final report.