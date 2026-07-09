# Research Engine
# IMP-09E - End-to-End Integration Test
# Version 1.0

Read and execute this document completely.

Work ONLY inside the current repository.

Do NOT modify architecture unless a test exposes a real defect.

--------------------------------------------------

OBJECTIVE

Perform a complete end-to-end validation of the Research Engine.

This phase is a TEST ONLY phase.

Do not implement new features.

Do not redesign modules.

Only fix genuine bugs discovered during testing.

--------------------------------------------------

SOURCE OF TRUTH

Use ONLY the implemented Research Engine.

--------------------------------------------------

TEST FLOW

Execute the complete pipeline.

Research Topic

↓

Research Planner

↓

Research Session

↓

Workflow

↓

Collector Integration

↓

Collectors

↓

Research Result Assembly

↓

Knowledge Verification

↓

Human Review Package

↓

Human Review

↓

Approval

↓

Database Persistence

↓

Telegram Notification

--------------------------------------------------

SCENARIO 1

Input

BEL

Verify

✓ Planner executes

✓ Session created

✓ Workflow completes

✓ Required collectors execute

✓ Research Package assembled

✓ Verification completes

✓ Human Review Package created

✓ Approval succeeds

✓ Database updated

✓ Telegram notification sent only after successful persistence

✓ Chart NOT generated

--------------------------------------------------

SCENARIO 2

Input

BEL with chart

Verify

✓ chart_required=True

✓ Historical Price Collector executed

✓ Technical Analysis Collector executed

✓ Chart Generator executed

✓ Chart attached to Review Package

✓ Chart metadata persisted after approval

✓ Telegram notification indicates chart included

--------------------------------------------------

SCENARIO 3

Rejected Review

Verify

✓ Database NOT updated

✓ Telegram NOT sent

--------------------------------------------------

SCENARIO 4

Needs Revision

Verify

✓ Revision workflow starts

✓ Telegram NOT sent

--------------------------------------------------

SCENARIO 5

Collector Failure

Simulate one collector failure.

Verify

✓ Workflow continues

✓ Failure reported correctly

✓ Remaining collectors execute

--------------------------------------------------

SCENARIO 6

Verification Failure

Simulate failed verification.

Verify

✓ Human Review receives correct report

✓ Approval blocked

--------------------------------------------------

REGRESSION TESTS

Run the complete test suite.

Verify all existing tests continue to pass.

--------------------------------------------------

DO NOT

Do not implement Script Generation.

Do not implement Video Generation.

Do not implement live market APIs.

Do not redesign architecture.

--------------------------------------------------

IF BUGS ARE FOUND

Fix ONLY the bug required to make the test pass.

Do not refactor unrelated modules.

--------------------------------------------------

FINAL REPORT

Include:

1. Number of scenarios executed

2. Number passed

3. Number failed

4. Existing unit tests

5. Compilation status

6. Modules modified (if any)

7. Bugs fixed (if any)

8. Database verification

9. Telegram verification

10. Chart verification

11. Final conclusion

Print the complete report.