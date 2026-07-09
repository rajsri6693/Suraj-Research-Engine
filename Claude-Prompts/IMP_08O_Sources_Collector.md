# Research Engine
# IMP-08O - Sources Collector Implementation
# Version 1.0

Read and execute this document completely.

Work ONLY inside the current repository.

Do NOT modify anything outside this repository.

--------------------------------------------------

OBJECTIVE

Implement the Sources Collector.

Its responsibility is ONLY to collect source metadata used during research and return a SourcesResult.

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

research_engine/collectors/sources/

    __init__.py

    sources_collector.py

    sources_result.py

--------------------------------------------------

IMPLEMENT

SourcesResult dataclass

Fields:

• Source Name

• Source Type

• Source Category

• Source Priority

• Source Reliability

• Source Language

• Collection Timestamp

• Source Notes

• Sources

• Collection Time

• Collector Status

--------------------------------------------------

SourcesCollector

Implement:

1. Collector Name

2. Knowledge Section

3. collect()

Input

Research Topic

Output

SourcesResult

--------------------------------------------------

IMPORTANT

This phase DOES NOT perform live research.

collect() must return a valid SourcesResult using placeholder/mock values only.

The objective is to validate the Collector architecture and Source metadata contract.

--------------------------------------------------

RULES

Sources Collector must NEVER

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

1. Sources Collector created successfully.

2. All unit tests pass.

3. Python compilation passes.

4. All previously implemented collectors unchanged.

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