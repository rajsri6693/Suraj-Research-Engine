# Research Engine
# IMP-10I - Research Runtime & CLI
# Version 1.0

Read and execute this document completely.

Work ONLY inside the current repository.

Use the existing architecture exactly as implemented.

Do NOT redesign any existing architecture.

Do NOT redesign any existing workflow.

Do NOT modify Collectors unless required to fix a genuine defect.

Do NOT modify API Manager unless required to fix a genuine defect.

Do NOT modify Database Schema.

--------------------------------------------------

OBJECTIVE

Create the production runtime entry point for the Research Engine.

The project currently contains all core modules, collectors, API Manager, workflow, verification, review, approval, notifications and SQLite persistence.

The missing piece is the executable runtime that connects these existing modules together.

This phase must implement that runtime only.

--------------------------------------------------

RUNTIME

Create a production entry point.

Example:

python research.py

or another appropriate executable entry point if one better matches the current architecture.

The runtime must not replace the existing Knowledge Viewer.

Knowledge Viewer remains available.

--------------------------------------------------

WORKFLOW

The runtime must execute the existing workflow in this order:

User Input

↓

Research Planner

↓

Research Workflow

↓

Collectors

↓

API Manager

↓

SQLite Persistence

↓

Verification

↓

Human Review

↓

Approval

↓

Telegram Notification

↓

Completion

No workflow redesign.

--------------------------------------------------

USER INPUT

Accept research topics such as:

BEL

BEL with chart

TCS

RELIANCE

INFY

NIFTY 50

Detect whether chart generation is requested.

Use the existing Planner.

--------------------------------------------------

COLLECTORS

Use the existing Collector Registry and Collector Factory.

No Collector may be called directly from the runtime.

--------------------------------------------------

API MANAGER

Use the existing API Manager.

Verify:

Primary routing

Backup routing

Failover

Failback

No provider-specific logic inside runtime.

--------------------------------------------------

DATABASE

Persist using the existing SQLite Database Manager.

Read back the stored data where appropriate.

Do not redesign the database.

--------------------------------------------------

VERIFICATION

Run the existing Verification module.

--------------------------------------------------

HUMAN REVIEW

Run the existing Human Review module.

--------------------------------------------------

APPROVAL

Run the existing Approval module.

--------------------------------------------------

NOTIFICATIONS

Use the existing Telegram Notification module.

Send notification only after successful Approval.

--------------------------------------------------

ERROR HANDLING

Gracefully handle:

Invalid topic

API failure

SQLite failure

Telegram failure

Unexpected exception

Display meaningful runtime messages.

--------------------------------------------------

CLI

Provide a clean production console experience.

Example:

==================================

Suraj Research Engine

==================================

Enter Research Topic:

>

Display progress for each stage.

Display final success or failure.

--------------------------------------------------

TESTING

Run:

Runtime unit tests
Runtime integration tests
End-to-end workflow tests
Regression tests for existing IntegrationEngine behavior
Full repository test suite
Full repository compilation

--------------------------------------------------

VERIFY

Verify:

Planner executes.

Workflow executes.

Collectors execute.

API Manager executes.

SQLite persists.

Verification executes.

Human Review executes.

Approval executes.

Telegram executes.

Knowledge Viewer remains unaffected.

Also verify:

research.py contains only bootstrap/CLI logic and no business workflow logic.
IntegrationEngine remains the single source of truth for workflow orchestration.
Existing end-to-end behavior is unchanged except for removal of the duplicate orchestration path.

--------------------------------------------------

OUTPUT

Print:

1. Runtime Implementation Report

2. Workflow Execution Report

3. SQLite Report

4. API Manager Report

5. Telegram Report

6. Verification Report

7. Runtime Validation Report

If any genuine defect is found:

Fix it.

Re-run all affected validation.

Repeat until everything passes.

Do not commit.