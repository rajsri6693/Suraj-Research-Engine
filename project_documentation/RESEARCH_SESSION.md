# Research Session

This document defines the Research Session architecture — the structure
that tracks one complete research lifecycle in the Research Engine. It
describes responsibility and tracking structure only — no schema, no SQL,
no implementation.

--------------------------------------------------

## 1. Purpose

A Research Session represents one complete research lifecycle: everything
that happens from the moment a Research Input is received until every
Knowledge Section presented for approval has reached a final Human Review
decision. It is the thread that ties one Research Input, through the
Research Planner and every stage of `RESEARCH_WORKFLOW.md` — including any
number of passes through the Revision Loop — into a single trackable unit,
so the progress of one research request can be observed as one thing, not
as a scattered set of independent steps.

A Research Session NEVER performs research. It NEVER verifies knowledge.
It NEVER writes to the database. It is a record of progress, not an actor
— it observes and reports where a research request currently stands; it
does not do the work that moves it forward.

--------------------------------------------------

## 2. Session Lifecycle

A Research Session moves through the following stages, in order:

```
Created
   ↓
Planning
   ↓
Collecting  ◄────────────────────────┐
   ↓                                 │
Assembling                           │
   ↓                                 │
Verifying                            │
   ↓                                 │
Waiting Human Review ─── Needs Revision on any section ───┘
   ↓
   (every section presented for approval has reached
    Approved or Rejected)
   ↓
Completed
```

Failed and Cancelled are exits that can occur from any stage before
Completed — they are not steps in the normal forward path. Waiting Human
Review → Collecting is the one permitted backward transition, taken only
when Human Review records Needs Revision for a section (see Section 5).

- **Created** — A Research Input, per `RESEARCH_INPUT_STANDARD.md`, has
  been received and the session has been initialized. No plan exists yet.
- **Planning** — The Research Planner is converting the Research Input into
  a Research Plan, per `RESEARCH_PLANNER.md`. This stage runs exactly once
  per session — it is never repeated, even across a Revision Loop.
- **Collecting** — Research Workflow Stages 2–4 are underway: required
  collectors have been identified and triggered in parallel, per
  `RESEARCH_WORKFLOW.md`. On the first pass this covers every required
  Knowledge Section; on a Revision Loop pass it covers only the section(s)
  flagged Needs Revision.
- **Assembling** — Research Workflow Stage 5 (Research Result Assembly) is
  underway: the Collector Results gathered so far are being organized,
  per section and without merging, into the session's Research Package.
- **Verifying** — Research Workflow Stage 6 is underway: the Research
  Package's Collector Results are being evaluated for trustworthiness by
  Knowledge Verification.
- **Waiting Human Review** — Verified knowledge has passed through Research
  Workflow Stages 7 and 8 (Knowledge Storage, Knowledge Viewer) and reached
  Stage 9 (Ready for Human Review). The session sits here until Human
  Review has acted on every eligible section.
- **Completed** — Every Knowledge Section presented for approval has
  reached a final Approval Status of Approved or Rejected — none remain at
  Pending Review or Needs Revision. This is the session's normal terminal
  status.

--------------------------------------------------

## 3. Session Information

Every Research Session carries the following information:

- **Research ID** — a unique identifier for this session, distinguishing
  it from every other Research Session.
- **Research Topic** — restated from the Research Input, per
  `RESEARCH_INPUT_STANDARD.md`.
- **Research Profile** — restated from the Research Input.
- **Research Category** — restated from the Research Input.
- **Start Time** — the timestamp the session entered Created.
- **End Time** — the timestamp the session reached a terminal status
  (Completed, Failed, or Cancelled). Not present while the session is
  still active.
- **Duration** — the elapsed time between Start Time and End Time. While
  the session is still active, this reflects elapsed time since Start Time
  rather than a final figure, and accumulates across any Revision Loop
  passes.
- **Current Stage** — the specific point within `RESEARCH_WORKFLOW.md`'s
  nine execution stages the session is presently at (for example, "Stage
  3 — Run Collectors in Parallel"). This is a finer-grained pointer than
  Overall Status.
- **Overall Status** — one value from the Session Status list (Section 4).
  Each Overall Status can span more than one underlying Workflow stage —
  for example, Collecting covers Workflow Stages 2 through 4.

--------------------------------------------------

## 4. Session Status

- **Created** — The session exists; a Research Input has been received but
  no Research Plan has been produced yet.
- **Planning** — The Research Planner is producing the Research Plan for
  this session's Research Input.
- **Collecting** — Collectors identified by the Research Plan are running,
  per Research Workflow Stages 2–4 — the full required set on the first
  pass, or a single flagged section during a Revision Loop pass.
- **Assembling** — Research Workflow Stage 5 is underway: Collector Results
  are being organized into the session's Research Package.
- **Verifying** — Research Workflow Stage 6 is underway.
- **Waiting Human Review** — Verified knowledge has been stored and made
  visible, and the session is waiting on Human Review decisions.
- **Completed** — Every section presented for approval has reached Approved
  or Rejected. The session's tracked work has concluded successfully.
- **Failed** — The session could not proceed due to a session-level
  failure — for example, the Research Input could not produce a valid
  Research Plan, or no collector returned any usable result at all.
  Ordinary partial completion, where some collectors succeed and others do
  not, is expected behavior under `RESEARCH_WORKFLOW.md` and does NOT by
  itself make a session Failed.
- **Cancelled** — The session was deliberately stopped before reaching
  Completed. Unlike Failed, Cancelled reflects a deliberate stop rather
  than a breakdown.

--------------------------------------------------

## 5. Session Rules

- A Research Session tracks exactly one Research Input — one Research
  Profile, one Research Category, one Research Topic. A session never
  spans more than one Research Input.
- A session's Overall Status only moves forward through the lifecycle in
  Section 2, with exactly one permitted exception: Waiting Human Review may
  move back to Collecting when Human Review records Needs Revision for at
  least one Knowledge Section. This is not "reopening a closed session" —
  the session has not reached a terminal status while any section remains
  at Needs Revision or Pending Review, so it was never closed. Failed and
  Cancelled remain reachable from any active, non-terminal status.
- A session observes and records the status of work happening in the
  Research Planner, `RESEARCH_WORKFLOW.md`, `KNOWLEDGE_VERIFICATION.md`,
  and `HUMAN_REVIEW.md`. It never performs research, never verifies
  knowledge, and never writes to the database — it never substitutes its
  own action for the layer responsible for that work.
- A session never mutates the Research Plan or the knowledge collected
  under it. It only tracks their state.
- Partial completion among collectors, as described in
  `RESEARCH_WORKFLOW.md`, does not by itself move a session to Failed —
  only a session-level failure does (see Section 4).
- Once a session reaches a terminal status (Completed, Failed, or
  Cancelled), its status does not change again. A new research need is
  tracked by starting a new session, never by reopening a closed one. A
  Revision Loop pass never counts as starting a new session — it continues
  the same, still-active session.
- End Time and Duration are only final once a session reaches a terminal
  status.

--------------------------------------------------

## 6. Session Example

```
Research ID: RS-2026-0709-001
Research Topic: Full analysis ahead of quarterly results next week.
Research Profile: Sample Manufacturing Ltd (SMFG, NSE)
Research Category: Stock Analysis

Start Time: 2026-07-09 09:00
End Time: (not yet reached)
Duration: 00:17:00 (elapsed so far)

Current Stage: Stage 6 — Verification
Overall Status: Verifying
```

At this point in the session, the Research Planner has already produced
the Research Plan (Planning complete), the required collectors have run
and their results have been organized into the session's Research Package
(Collecting and Assembling complete), and that Package is now being
evaluated under `RESEARCH_WORKFLOW.md` Stage 6. The session has not yet
reached Waiting Human Review, so End Time and final Duration are not yet
set. If Human Review later records Needs Revision for any section, this
session will return to Overall Status Collecting rather than reaching
Completed — Completed only follows once every section presented for
approval is Approved or Rejected.

--------------------------------------------------

## Notes

- See `RESEARCH_INPUT_STANDARD.md` for the structure of Research Topic,
  Research Profile, and Research Category.
- See `RESEARCH_PLANNER.md` for what happens during the Planning stage.
- See `RESEARCH_WORKFLOW.md` for the nine execution stages a session's
  Collecting, Assembling, Verifying, and Waiting Human Review statuses map
  onto, and for the Revision Loop this session's one backward transition
  follows.
- See `HUMAN_REVIEW.md` for how a Needs Revision decision is recorded and
  why it sends a session back to Collecting instead of to Completed.
- This document defines session tracking responsibility only. Research
  gathering, verification, storage, and human approval are each owned by
  their own layer — see `ROADMAP.md`.
