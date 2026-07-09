# Research Engine
# IMP-09C - Approval Persistence & Telegram Notification
# Version 1.0

Read and execute this document completely.

Work ONLY inside the current repository.

Do NOT modify anything outside this repository.

--------------------------------------------------

OBJECTIVE

Implement the approval persistence workflow.

When Human Review returns APPROVED:

Review Result

↓

Save Approved Research

↓

Trigger Telegram Notification

Notification MUST be sent ONLY after the approved research has been successfully persisted.

--------------------------------------------------

SOURCE OF TRUTH

Use ONLY

project_documentation/

HUMAN_REVIEW.md

KNOWLEDGE_VERIFICATION.md

RESEARCH_WORKFLOW.md

--------------------------------------------------

IMPLEMENT

Create

research_engine/approval/

    __init__.py

    approval_service.py

research_engine/notifications/

    __init__.py

    telegram_notification.py

--------------------------------------------------

Approval Service

Responsibilities

1.

Receive ReviewResult

2.

If decision != APPROVED

Stop.

3.

If APPROVED

Persist the approved research using the project's existing persistence layer.

4.

Only after persistence succeeds

Trigger Telegram Notification.

--------------------------------------------------

Telegram Notification

Configuration

Enabled

Bot Token

Chat ID

Message Template

--------------------------------------------------

Notification Example

✅ Research Approved

Research ID

Topic

Category

Approval Time

Chart Included

Ready for Script Generation

--------------------------------------------------

DO NOT

Generate Scripts

Generate Videos

Call Collectors

Modify Planner

Modify Workflow

Modify Human Review logic

--------------------------------------------------

UNIT TESTS

Verify

Approved → Save → Telegram

Rejected → No Telegram

Revision → No Telegram

Persistence failure → No Telegram

Existing tests continue to pass

--------------------------------------------------

VERIFY

Confirm

1. Approval Service created.

2. Telegram Notification created.

3. Approved notification only after successful persistence.

4. Existing modules unchanged.

5. All tests pass.

6. Compilation passes.

Print the final report.