# Research Engine
# IMP-08I - Orders & Contracts Collector Implementation
# Version 1.0

Read and execute this document completely.

Work ONLY inside the current repository.

Do NOT modify anything outside this repository.

--------------------------------------------------

OBJECTIVE

Implement the Orders & Contracts Collector.

Its responsibility is ONLY to collect Orders and Contracts information and return an OrderContractResult.

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

research_engine/collectors/orders_contracts/

    __init__.py

    orders_contracts_collector.py

    order_contract_result.py

--------------------------------------------------

IMPLEMENT

OrderContractResult dataclass

Fields:

• Order Title

• Order Type

• Customer Name

• Contract Value

• Currency

• Announcement Date

• Execution Period

• Order Status

• Related Company

• Sources

• Collection Time

• Collector Status

--------------------------------------------------

OrdersContractsCollector

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

OrderContractResult

--------------------------------------------------

IMPORTANT

This phase DOES NOT perform live research.

collect() must return a valid OrderContractResult using placeholder/mock values only.

The objective is to validate the Collector architecture and Orders & Contracts data contract.

--------------------------------------------------

RULES

Orders & Contracts Collector must NEVER

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

1. Orders & Contracts Collector created successfully.

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

12. Collector Framework unchanged.

13. Session unchanged.

14. Planner unchanged.

15. Workflow unchanged.

16. Assembly unchanged.

17. Verification unchanged.

18. Human Review unchanged.

19. Database unchanged.

20. No SQLite.

21. No external APIs used.

Print the final report.