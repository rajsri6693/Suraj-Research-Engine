# Research Engine
# IMP-09B - Human Review Integration
# Version 1.0

Read and execute this document completely.

Work ONLY inside the current repository.

Do NOT modify anything outside this repository.

--------------------------------------------------

OBJECTIVE

Integrate the Human Review module into the completed Research Engine pipeline.

The Integration Engine must now deliver a complete Review Package to the Human Review layer.

This phase DOES NOT implement any user interface.

It only connects the existing Review module to the workflow.

--------------------------------------------------

SOURCE OF TRUTH

Use ONLY

project_documentation/

HUMAN_REVIEW.md

RESEARCH_WORKFLOW.md

KNOWLEDGE_VERIFICATION.md

RESEARCH_RESULT_ASSEMBLY.md

--------------------------------------------------

IMPLEMENT

Update only the Integration layer.

When Verification completes:

↓

Create Human Review Package

↓

Populate:

• Research Session

• Research Plan

• Research Package

• Verification Report

• Review Status

• Eligible Sections

↓

Pass the package to the existing Human Review module.

--------------------------------------------------

DO NOT

Modify Collectors

Modify Verification logic

Modify Planner

Modify Session

Modify Database

Implement UI

--------------------------------------------------

UNIT TESTS

Verify:

Human Review Package created

Verification Report attached

Eligible sections correct

Review module invoked

Existing tests continue to pass

--------------------------------------------------

VERIFY

Confirm:

1. Human Review integration completed.

2. Existing modules unchanged.

3. All tests pass.

4. Compilation passes.

5. No database modified.

6. No SQLite.

7. No APIs.

Print the final report.