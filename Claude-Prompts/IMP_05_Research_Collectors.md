# Research Engine
# IMP-05 - Research Collectors Implementation
# Version 1.0

Read and execute this document completely.

Work ONLY inside the current repository.

Do NOT modify anything outside this repository.

--------------------------------------------------

OBJECTIVE

Implement the Research Collectors framework.

This phase implements ONLY the collector framework.

It does NOT implement actual research.

It does NOT call APIs.

It does NOT collect live data.

It does NOT verify knowledge.

--------------------------------------------------

SOURCE OF TRUTH

Use ONLY:

project_documentation/RESEARCH_COLLECTORS.md

project_documentation/KNOWLEDGE_MODEL.md

project_documentation/RESEARCH_WORKFLOW.md

--------------------------------------------------

IMPLEMENT ONLY

Create:

research_engine/collectors/

    __init__.py

    base_collector.py

    collector_registry.py

    collector_factory.py

--------------------------------------------------

IMPLEMENT

BaseCollector

Define the common collector interface.

Every collector must implement:

• collector_name

• knowledge_section

• collect()

The default collect() method must raise NotImplementedError.

--------------------------------------------------

CollectorRegistry

Implement:

• Register Collector

• Unregister Collector

• Get Collector

• List Collectors

• Prevent duplicate registration

--------------------------------------------------

CollectorFactory

Implement:

• Create Collector

• Validate collector availability

• Return collector instance

--------------------------------------------------

RULES

This phase must NOT create:

Company Collector

Financial Collector

News Collector

Technical Collector

Government Collector

Corporate Action Collector

or any real collector implementation.

Only the framework.

--------------------------------------------------

IMPLEMENTATION RULES

Only standard Python.

No APIs.

No HTTP.

No Database.

No SQLite.

No AI.

No Workflow execution.

No Verification.

--------------------------------------------------

UNIT TESTS

Create comprehensive tests.

Verify:

BaseCollector interface

NotImplementedError behavior

Registry registration

Duplicate registration

Collector lookup

Collector removal

Factory creation

Factory invalid collector handling

--------------------------------------------------

VERIFY

Confirm:

1. Collector framework created successfully.

2. All unit tests pass.

3. Python compilation passes.

4. No Session module modified.

5. No Planner module modified.

6. No Workflow module modified.

7. No Assembly module modified.

8. No Database modified.

9. No SQLite.

10. No actual collectors implemented.

Print the final report.