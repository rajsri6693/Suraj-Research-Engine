# Research Engine
# IMP-08G - Historical Price Collector Implementation
# Version 1.0

Read and execute this document completely.

Work ONLY inside the current repository.

Do NOT modify anything outside this repository.

--------------------------------------------------

OBJECTIVE

Implement the Historical Price Collector.

Its responsibility is ONLY to collect Historical Price information and return a HistoricalPriceResult.

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

research_engine/collectors/historical_price/

    __init__.py

    historical_price_collector.py

    historical_price_result.py

--------------------------------------------------

IMPLEMENT

HistoricalPriceResult dataclass

Fields:

• Symbol

• Exchange

• Timeframe

• Start Date

• End Date

• OHLC Records

• Total Trading Days

• Adjusted Prices

• Sources

• Collection Time

• Collector Status

--------------------------------------------------

HistoricalPriceCollector

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

HistoricalPriceResult

--------------------------------------------------

IMPORTANT

This phase DOES NOT perform live research.

collect() must return a valid HistoricalPriceResult using placeholder/mock values only.

The objective is to validate the Collector architecture and Historical Price data contract.

--------------------------------------------------

RULES

Historical Price Collector must NEVER

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

1. Historical Price Collector created successfully.

2. All unit tests pass.

3. Python compilation passes.

4. Company Collector unchanged.

5. Financial Collector unchanged.

6. Market News Collector unchanged.

7. Sector Collector unchanged.

8. Technical Analysis Collector unchanged.

9. Government Policy Collector unchanged.

10. Collector Framework unchanged.

11. Session unchanged.

12. Planner unchanged.

13. Workflow unchanged.

14. Assembly unchanged.

15. Verification unchanged.

16. Human Review unchanged.

17. Database unchanged.

18. No SQLite.

19. No external APIs used.

Print the final report.