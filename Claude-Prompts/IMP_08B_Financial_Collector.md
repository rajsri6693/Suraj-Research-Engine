# Research Engine
# IMP-08B - Financial Collector Implementation
# Version 1.0

Read and execute this document completely.

Work ONLY inside the current repository.

Do NOT modify anything outside this repository.

--------------------------------------------------

OBJECTIVE

Implement the Financial Collector.

Its responsibility is ONLY to collect Financial Information and return a FinancialResult.

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

research_engine/collectors/financial/

    __init__.py

    financial_collector.py

    financial_result.py

--------------------------------------------------

IMPLEMENT

FinancialResult dataclass

Fields:

• Revenue

• Net Profit

• EPS

• Book Value

• PE Ratio

• ROE

• ROCE

• Debt to Equity

• Market Capitalization

• Dividend Yield

• Financial Year

• Sources

• Collection Time

• Collector Status

--------------------------------------------------

FinancialCollector

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

FinancialResult

--------------------------------------------------

IMPORTANT

This phase DOES NOT perform live research.

collect() must return a valid FinancialResult using placeholder/mock values only.

The objective is to validate the Collector architecture and Financial data contract.

--------------------------------------------------

RULES

Financial Collector must NEVER

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

1. Financial Collector created successfully.

2. All unit tests pass.

3. Python compilation passes.

4. Company Collector unchanged.

5. Collector Framework unchanged.

6. Session unchanged.

7. Planner unchanged.

8. Workflow unchanged.

9. Assembly unchanged.

10. Verification unchanged.

11. Human Review unchanged.

12. Database unchanged.

13. No SQLite.

14. No external APIs used.

Print the final report.