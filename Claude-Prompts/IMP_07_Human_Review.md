# Research Engine
# IMP-07 - Human Review Implementation
# Version 1.0

Read and execute this document completely.

Work ONLY inside the current repository.

Do NOT modify anything outside this repository.

--------------------------------------------------

OBJECTIVE

Implement the Human Review module.

The Human Review module is the only component that allows a human reviewer to make the final decision on verified knowledge.

It NEVER performs research.

It NEVER performs verification.

It NEVER calls APIs.

It NEVER writes directly to the database.

--------------------------------------------------

SOURCE OF TRUTH

Use ONLY:

project_documentation/HUMAN_REVIEW.md

project_documentation/KNOWLEDGE_VERIFICATION.md

project_documentation/RESEARCH_SESSION.md

--------------------------------------------------

IMPLEMENT ONLY

Create:

research_engine/review/

    __init__.py

    review_decision.py

    review_result.py

    human_review.py

--------------------------------------------------

IMPLEMENT

ReviewDecision enum

Values:

• APPROVED

• REJECTED

• NEEDS_REVISION

• SKIPPED

--------------------------------------------------

ReviewResult dataclass

Fields:

• Research ID

• Review Decision

• Review Notes

• Reviewed By

• Review Time

• Reviewed Sections

• Revision Sections

--------------------------------------------------

HumanReview

Implement:

1.

Review Verification Report

Input:

Verification Report

Output:

Review Result

--------------------------------------------------

2.

Approve

--------------------------------------------------

3.

Reject

--------------------------------------------------

4.

Request Revision

--------------------------------------------------

5.

Skip

--------------------------------------------------

RULES

Human Review must NEVER

Perform research

Verify knowledge

Modify collected knowledge

Access database

Generate scripts

Generate videos

Call APIs

--------------------------------------------------

IMPLEMENTATION RULES

Use only standard Python.

No APIs.

No HTTP.

No Database.

No SQLite.

No AI.

--------------------------------------------------

UNIT TESTS

Create comprehensive tests.

Verify:

Approve

Reject

Needs Revision

Skip

Review Result creation

Invalid review handling

--------------------------------------------------

VERIFY

Confirm:

1. Review module created successfully.

2. All unit tests pass.

3. Python compilation passes.

4. No Session module modified.

5. No Planner module modified.

6. No Workflow module modified.

7. No Assembly module modified.

8. No Collector module modified.

9. No Verification module modified.

10. No Database modified.

11. No SQLite.

12. Human Review follows HUMAN_REVIEW.md exactly.

Print the final report.