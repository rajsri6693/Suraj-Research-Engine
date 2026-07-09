# Research Engine
# RE-04 - Knowledge Verification
# Version 1.0

Read and execute this document completely.

Work ONLY inside the current repository.

Do NOT modify anything outside this repository.

--------------------------------------------------

OBJECTIVE

Design the Knowledge Verification layer of the Research Engine.

The Knowledge Verification layer is responsible for deciding whether collected knowledge is trustworthy enough to enter the Verified Knowledge Database.

It NEVER performs research.

It NEVER generates scripts.

It NEVER approves data.

Human approval is always the final authority.

--------------------------------------------------

SOURCE OF TRUTH

Use ONLY:

project_documentation/KNOWLEDGE_MODEL.md

project_documentation/RESEARCH_INPUT_STANDARD.md

project_documentation/RESEARCH_PLANNER.md

project_documentation/RESEARCH_WORKFLOW.md

--------------------------------------------------

TASK

Create ONLY:

project_documentation/KNOWLEDGE_VERIFICATION.md

--------------------------------------------------

The document must define

1.

Purpose of Knowledge Verification.

--------------------------------------------------

2.

Verification Input

Collected Knowledge

Collected Sources

Metadata

--------------------------------------------------

3.

Verification Output

Verified Knowledge

OR

Rejected Knowledge

--------------------------------------------------

4.

Verification Rules

Define:

• Source validation

• Duplicate detection

• Missing information

• Time-sensitive knowledge

• Conflicting information

• Metadata requirements

--------------------------------------------------

5.

Verification Status

Pending

Verified

Rejected

Needs Human Review

Explain each status.

--------------------------------------------------

6.

Verification Report

The output must be Human-readable.

Include:

Knowledge Section

Verification Status

Reason

Source Count

Confidence

Last Updated

--------------------------------------------------

7.

Restrictions

Knowledge Verification must NEVER

Perform research

Call APIs

Generate scripts

Generate videos

Approve data

Modify collected knowledge

--------------------------------------------------

8.

Human Review

Explain that Human Review is always the final decision.

Verification never replaces Human approval.

--------------------------------------------------

9.

Verification Example

Create one complete Human-readable verification report.

--------------------------------------------------

RULES

Documentation only.

No Python.

No SQLite.

No implementation.

No API.

--------------------------------------------------

VERIFY

Confirm:

1. Only KNOWLEDGE_VERIFICATION.md created.

2. No Python modified.

3. No Database modified.

4. No Schema modified.

5. Only current repository modified.

Print the final report.