# Research Engine
# RE-06D - Architecture Cleanup
# Version 1.0

Read and execute this document completely.

Work ONLY inside the current repository.

Do NOT modify anything outside this repository.

--------------------------------------------------

OBJECTIVE

Review and resolve all remaining architecture inconsistencies before implementation begins.

This is the final architecture refinement phase.

No new features.

No implementation.

No code.

Only architecture consistency.

--------------------------------------------------

SOURCE OF TRUTH

Use ONLY:

project_documentation/RESEARCH_INPUT_STANDARD.md

project_documentation/RESEARCH_PLANNER.md

project_documentation/RESEARCH_WORKFLOW.md

project_documentation/RESEARCH_COLLECTORS.md

project_documentation/RESEARCH_SESSION.md

project_documentation/KNOWLEDGE_VERIFICATION.md

project_documentation/HUMAN_REVIEW.md

--------------------------------------------------

TASK

Review every document together.

Resolve only the following architecture findings.

--------------------------------------------------

1.

Assembly Model

There must be exactly ONE definition of how collector outputs become a unified Research Package.

Remove duplicate or conflicting descriptions.

The ownership of Assembly must be explicit.

--------------------------------------------------

2.

Decision Persistence

Define where Human Review decisions exist inside the architecture.

Explain:

Pending Review

Approved

Rejected

Needs Revision

The architecture must clearly state how these states persist after Human Review.

--------------------------------------------------

3.

Revision Loop

Define the complete revision flow.

Needs Revision

↓

Research Workflow

↓

Collectors

↓

Verification

↓

Human Review

No missing transition is allowed.

--------------------------------------------------

4.

Approval Status Consistency

Review all examples.

Ensure approval status is identical everywhere.

--------------------------------------------------

5.

Terminology

Review every document.

Use one consistent vocabulary.

Research Package

Verified Knowledge

Knowledge Section

Collector Result

Research Session

Approval Status

Remove synonyms that refer to the same thing.

--------------------------------------------------

6.

Ownership

Every stage must have exactly one owner.

Research Planner

Research Workflow

Research Collectors

Research Result Assembly

Knowledge Verification

Human Review

Research Session

No overlapping responsibility.

--------------------------------------------------

7.

Final Architecture Diagram

Produce one complete end-to-end Research Engine architecture.

--------------------------------------------------

RULES

Documentation only.

No Python.

No SQLite.

No implementation.

Do NOT create new architecture.

Only resolve inconsistencies.

--------------------------------------------------

VERIFY

Confirm:

1.

Only existing architecture documents were updated where necessary.

2.

No Python modified.

3.

No Database modified.

4.

No Schema modified.

5.

No new architecture added.

6.

Research Engine architecture is internally consistent.

Print the final report.