# Research Engine
# IMP-08E - Technical Analysis Collector Implementation
# Version 1.0

Read and execute this document completely.

Work ONLY inside the current repository.

Do NOT modify anything outside this repository.

--------------------------------------------------

OBJECTIVE

Implement the Technical Analysis Collector.

Its responsibility is ONLY to collect Technical Analysis information and return a TechnicalAnalysisResult.

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

research_engine/collectors/technical_analysis/

    __init__.py

    technical_analysis_collector.py

    technical_analysis_result.py

--------------------------------------------------

IMPLEMENT

TechnicalAnalysisResult dataclass

Fields:

• Current Price

• Support Levels

• Resistance Levels

• Trend

• Moving Averages

• RSI

• MACD

• Volume Analysis

• Pattern

• Technical Summary

• Sources

• Collection Time

• Collector Status

--------------------------------------------------

TechnicalAnalysisCollector

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

TechnicalAnalysisResult

--------------------------------------------------

IMPORTANT

This phase DOES NOT perform live research.

collect() must return a valid TechnicalAnalysisResult using placeholder/mock values only.

The objective is to validate the Collector architecture and Technical Analysis data contract.

--------------------------------------------------

RULES

Technical Analysis Collector must NEVER

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

1. Technical Analysis Collector created successfully.

2. All unit tests pass.

3. Python compilation passes.

4. Company Collector unchanged.

5. Financial Collector unchanged.

6. Market News Collector unchanged.

7. Sector Collector unchanged.

8. Collector Framework unchanged.

9. Session unchanged.

10. Planner unchanged.

11. Workflow unchanged.

12. Assembly unchanged.

13. Verification unchanged.

14. Human Review unchanged.

15. Database unchanged.

16. No SQLite.

17. No external APIs used.

Print the final report.