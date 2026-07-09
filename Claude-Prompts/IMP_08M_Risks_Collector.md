# Research Engine
# IMP-08M - Risks Collector Implementation
# Version 1.0

Read and execute this document completely.

Work ONLY inside the current repository.

Do NOT modify anything outside this repository.

--------------------------------------------------

OBJECTIVE

Implement the Risks Collector.

Its responsibility is ONLY to collect Risk information and return a RiskResult.

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

research_engine/collectors/risks/

    __init__.py

    risks_collector.py

    risk_result.py

--------------------------------------------------

IMPLEMENT

RiskResult dataclass

Fields:

• Company Name

• Business Risks

• Financial Risks

• Operational Risks

• Regulatory Risks

• Sector Risks

• Market Risks

• Key Risk Summary

• Risk Level

• Mitigation Factors

• Sources

• Collection Time

• Collector Status

--------------------------------------------------

RisksCollector

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

RiskResult

--------------------------------------------------

IMPORTANT

This phase DOES NOT perform live research.

collect() must return a valid RiskResult using placeholder/mock values only.

The objective is to validate the Collector architecture and Risk data contract.

--------------------------------------------------

RULES

Risks Collector must NEVER

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

1. Risks Collector created successfully.

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

15. Shareholding Collector unchanged.

16. Collector Framework unchanged.

17. Session unchanged.

18. Planner unchanged.

19. Workflow unchanged.

20. Assembly unchanged.

21. Verification unchanged.

22. Human Review unchanged.

23. Database unchanged.

24. No SQLite.

25. No external APIs used.

Print the final report.