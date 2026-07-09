# Research Engine
# IMP-08C - Market News Collector Implementation
# Version 1.0

Read and execute this document completely.

Work ONLY inside the current repository.

Do NOT modify anything outside this repository.

--------------------------------------------------

OBJECTIVE

Implement the Market News Collector.

Its responsibility is ONLY to collect Market News information and return a MarketNewsResult.

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

research_engine/collectors/market_news/

    __init__.py

    market_news_collector.py

    market_news_result.py

--------------------------------------------------

IMPLEMENT

MarketNewsResult dataclass

Fields:

• News Title

• News Summary

• News Category

• Published Time

• Source Name

• Related Companies

• Related Sectors

• Impact

• Sources

• Collection Time

• Collector Status

--------------------------------------------------

MarketNewsCollector

Implement:

1.

Collector Name

2.

Knowledge Section

3.

collect()

Input:

Research Topic

Output:

MarketNewsResult

--------------------------------------------------

IMPORTANT

This phase DOES NOT perform live research.

collect() must return a valid MarketNewsResult using placeholder/mock values only.

The objective is to validate the Collector architecture and Market News data contract.

--------------------------------------------------

RULES

Market News Collector must NEVER

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

1. Market News Collector created successfully.

2. All unit tests pass.

3. Python compilation passes.

4. Company Collector unchanged.

5. Financial Collector unchanged.

6. Collector Framework unchanged.

7. Session unchanged.

8. Planner unchanged.

9. Workflow unchanged.

10. Assembly unchanged.

11. Verification unchanged.

12. Human Review unchanged.

13. Database unchanged.

14. No SQLite.

15. No external APIs used.

Print the final report.