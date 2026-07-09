# Research Engine
# IMP-08N - Products & Services Collector Implementation
# Version 1.0

Read and execute this document completely.

Work ONLY inside the current repository.

Do NOT modify anything outside this repository.

--------------------------------------------------

OBJECTIVE

Implement the Products & Services Collector.

Its responsibility is ONLY to collect Products and Services information and return a ProductsServicesResult.

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

research_engine/collectors/products_services/

    __init__.py

    products_services_collector.py

    products_services_result.py

--------------------------------------------------

IMPLEMENT

ProductsServicesResult dataclass

Fields:

• Company Name

• Products

• Services

• Business Segments

• Major Brands

• Key Customers

• Revenue Segments

• Geographic Presence

• Business Summary

• Sources

• Collection Time

• Collector Status

--------------------------------------------------

ProductsServicesCollector

Implement:

1. Collector Name

2. Knowledge Section

3. collect()

Input:

Research Topic

Output:

ProductsServicesResult

--------------------------------------------------

IMPORTANT

This phase DOES NOT perform live research.

collect() must return a valid ProductsServicesResult using placeholder/mock values only.

--------------------------------------------------

RULES

Must NEVER

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

1. Products & Services Collector created successfully.

2. All unit tests pass.

3. Python compilation passes.

4. Previously implemented collectors unchanged.

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