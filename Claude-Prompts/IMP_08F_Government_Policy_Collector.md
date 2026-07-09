# Research Engine
# IMP-08F - Government Policy Collector Implementation
# Version 1.0

Read and execute this document completely.

Work ONLY inside the current repository.

Do NOT modify anything outside this repository.

--------------------------------------------------

OBJECTIVE

Implement the Government Policy Collector.

Its responsibility is ONLY to collect Government Policy information and return a GovernmentPolicyResult.

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

research_engine/collectors/government_policy/

    __init__.py

    government_policy_collector.py

    government_policy_result.py

--------------------------------------------------

IMPLEMENT

GovernmentPolicyResult dataclass

Fields:

• Policy Title

• Policy Category

• Policy Description

• Government Authority

• Effective Date

• Affected Sectors

• Affected Companies

• Expected Impact

• Policy Status

• Sources

• Collection Time

• Collector Status

--------------------------------------------------

GovernmentPolicyCollector

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

GovernmentPolicyResult

--------------------------------------------------

IMPORTANT

This phase DOES NOT perform live research.

collect() must return a valid GovernmentPolicyResult using placeholder/mock values only.

The objective is to validate the Collector architecture and Government Policy data contract.

--------------------------------------------------

RULES

Government Policy Collector must NEVER

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

1. Government Policy Collector created successfully.

2. All unit tests pass.

3. Python compilation passes.

4. Company Collector unchanged.

5. Financial Collector unchanged.

6. Market News Collector unchanged.

7. Sector Collector unchanged.

8. Technical Analysis Collector unchanged.

9. Collector Framework unchanged.

10. Session unchanged.

11. Planner unchanged.

12. Workflow unchanged.

13. Assembly unchanged.

14. Verification unchanged.

15. Human Review unchanged.

16. Database unchanged.

17. No SQLite.

18. No external APIs used.

Print the final report.