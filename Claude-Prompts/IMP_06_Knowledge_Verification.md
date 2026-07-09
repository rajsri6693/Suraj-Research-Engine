# Research Engine
# IMP-06 - Knowledge Verification Implementation
# Version 1.0

Read and execute this document completely.

Work ONLY inside the current repository.

Do NOT modify anything outside this repository.

--------------------------------------------------

OBJECTIVE

Implement the Knowledge Verification module.

The Knowledge Verification module validates collected knowledge before Human Review.

It NEVER performs research.

It NEVER calls APIs.

It NEVER approves knowledge.

It NEVER writes directly to the database.

--------------------------------------------------

SOURCE OF TRUTH

Use ONLY:

project_documentation/KNOWLEDGE_VERIFICATION.md

project_documentation/RESEARCH_RESULT_ASSEMBLY.md

project_documentation/KNOWLEDGE_MODEL.md

--------------------------------------------------

IMPLEMENT ONLY

Create:

research_engine/verification/

    __init__.py

    verification_result.py

    verification_report.py

    knowledge_verifier.py

--------------------------------------------------

IMPLEMENT

VerificationResult dataclass

Fields:

• Knowledge Section

• Verification Status

• Reason

• Source Count

• Confidence

• Last Updated

--------------------------------------------------

VerificationReport dataclass

Fields:

• Research ID

• Verification Results

• Overall Status

• Verified Sections

• Failed Sections

• Pending Sections

• Generated Time

--------------------------------------------------

KnowledgeVerifier

Implement:

1.

Verify Research Package

Input:

Research Package

Output:

Verification Report

--------------------------------------------------

2.

Validate Sources

--------------------------------------------------

3.

Detect Missing Sections

--------------------------------------------------

4.

Detect Duplicate Sections

--------------------------------------------------

5.

Determine Verification Status

--------------------------------------------------

6.

Generate Overall Verification Report

--------------------------------------------------

RULES

Knowledge Verification must NEVER

Perform research

Call APIs

Approve knowledge

Modify collected knowledge

Access database

Generate scripts

Generate videos

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

Verification Report creation

Source validation

Duplicate detection

Missing section detection

Verification status

Overall report generation

Invalid input handling

--------------------------------------------------

VERIFY

Confirm:

1. Verification module created successfully.

2. All unit tests pass.

3. Python compilation passes.

4. No Session module modified.

5. No Planner module modified.

6. No Workflow module modified.

7. No Assembly module modified.

8. No Collector module modified.

9. No Database modified.

10. No SQLite.

11. Verification follows KNOWLEDGE_VERIFICATION.md exactly.

Print the final report.