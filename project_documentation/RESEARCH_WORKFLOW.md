# Research Workflow

This document defines the Research Workflow — the component of the Research
Engine responsible for executing a Research Plan. It describes
responsibility and sequencing only — no schema, no SQL, no code.

--------------------------------------------------

## 1. Purpose

The Research Workflow executes the Research Plan produced by the Research
Planner. It coordinates every stage between "a plan exists" and "verified
knowledge is ready for a human to review" — triggering collectors,
assembling their results, gating them through verification, and handing
only verified knowledge to storage and the Knowledge Viewer.

The Research Workflow does NOT perform research itself. It does not decide
what to research (that is the Research Planner's responsibility) and it
does not gather, verify, or approve facts itself — it coordinates the
components that do.

--------------------------------------------------

## 2. Workflow Input

**Research Plan** — the Human-readable Research Plan produced by the
Research Planner, as defined in `RESEARCH_PLANNER.md`.

The Workflow accepts exactly one Research Plan per run and treats it as
authoritative: it does not re-derive depth, priority, or required Knowledge
Sections, and it does not alter the plan. It only acts on what the plan
states.

--------------------------------------------------

## 3. Workflow Output

**Verified Knowledge ready for Human Review.**

This means: for each Knowledge Section the Research Plan required, either
Verified Knowledge has been stored and is visible in the Knowledge Viewer,
or the section is explicitly absent (never silently guessed or filled in).
The output is a state, not an approval — a human reviewer still makes the
final acceptance decision. The Workflow's responsibility for a forward pass
ends at making Verified Knowledge visible and reviewable; see Section 9 for
how the Workflow is re-entered when a reviewer requests revision.

--------------------------------------------------

## 4. Execution Stages

The Research Workflow runs the following stages in order:

```
Stage 1 — Receive Research Plan
        ↓
Stage 2 — Identify Required Collectors
        ↓
Stage 3 — Run Collectors in Parallel
        ↓
Stage 4 — Collect Results
        ↓
Stage 5 — Research Result Assembly
        ↓
Stage 6 — Verification
        ↓
Stage 7 — Knowledge Storage
        ↓
Stage 8 — Knowledge Viewer
        ↓
Stage 9 — Ready for Human Review
```

**Stage 1 — Receive Research Plan**
The Workflow's entry point for a forward pass. It accepts one completed
Research Plan from the Research Planner as its trigger.

**Stage 2 — Identify Required Collectors**
The Workflow reads the plan's Required Knowledge Sections and maps each one
to its corresponding collector — one collector per section, per
`RESEARCH_PLANNER.md` Section 7.

**Stage 3 — Run Collectors in Parallel**
The Workflow triggers every identified collector at the same time, per the
plan's Research Mode. The Workflow does not gather data itself here — it
only starts and coordinates the collectors defined in
`RESEARCH_COLLECTORS.md`. This is also the stage the Workflow re-enters,
for a single flagged section, when a reviewer requests revision (Section
9).

**Stage 4 — Collect Results**
The Workflow gathers whatever each collector returns: one Collector Result
per section, per `RESEARCH_COLLECTORS.md`. Results arrive independently
and are held per section, not merged, as they come in — a section's
Collector Result is ready to hand to Stage 5 as soon as its collector
reaches a final outcome (Success, Partial, or Failed), regardless of
whether sibling collectors are still running.

**Stage 5 — Research Result Assembly**
**Owned exclusively by the Research Workflow.** Once every collector
triggered at Stage 3 has reached a final outcome, the Workflow organizes
the Collector Results gathered at Stage 4 into one **Research Package** for
the Research Session — a single structured container holding one entry per
required Knowledge Section. Assembly organizes; it does not merge. Each
Knowledge Section's Collector Result remains its own distinct entry inside
the Research Package, including sections whose collector failed (recorded
as absent, never fabricated). This is the one and only place in the
Research Engine where Collector Results become a Research Package, and the
Research Workflow is its one and only owner — no other document or
component performs or duplicates this step.

**Stage 6 — Verification**
Every Collector Result inside the Research Package is checked, one
Knowledge Section at a time, against the Verification Rules owned by
Knowledge Verification (`KNOWLEDGE_VERIFICATION.md`). Nothing proceeds past
this stage unverified. The Research Workflow enforces that this gate
exists; it does not itself define what counts as verified.

**Stage 7 — Knowledge Storage**
**Owned exclusively by the Research Workflow.** Only Collector Results that
passed Verification are written into the Knowledge Base, per the Knowledge
Storage Rules (Section 7 below). Knowledge Storage is also the sole place
where an Approval Status (Pending Review, Approved, Rejected, Needs
Revision) is persisted, once Human Review records a decision — see Section
7 and Section 9.

**Stage 8 — Knowledge Viewer**
Stored knowledge becomes visible through the Knowledge Viewer, organized by
Knowledge Section.

**Stage 9 — Ready for Human Review**
The Workflow's terminal state for a forward pass. The knowledge now visible
in the Knowledge Viewer is presented as ready for a human reviewer to
examine, per `HUMAN_REVIEW.md`. The Workflow does not grant approval
itself. A forward pass ends here; the Workflow is only re-entered, at Stage
3, through the Revision Loop described in Section 9.

--------------------------------------------------

## 5. Collector Execution Rules

**Parallel execution**
Collectors run concurrently, not sequentially, because each one gathers a
different Knowledge Section and no section depends on another to be
gathered. Running them in parallel is what the Research Plan's Research
Mode prescribes, and it minimizes the total time between Stage 1 and Stage
5.

**Collector independence**
Each collector is responsible for exactly one Knowledge Section. A
collector never reads another collector's output as an input, and one
collector's success, failure, or delay has no effect on any other
collector's execution.

**Partial completion**
The Workflow does not require every collector to succeed before proceeding
to Stage 5. Results are tracked per section: a section whose collector has
returned a Collector Result is ready for Assembly as soon as it is ready,
independent of whether sibling collectors are still running. Assembly
itself (Stage 5) begins once every triggered collector has reached *some*
final outcome — Success, Partial, or Failed — not once every collector has
*succeeded*. A slow or failed collector delays nothing beyond its own
section reaching a final outcome.

**Failure handling**
A collector that fails produces no Collector Result for its section. That
section is simply absent from the Research Package assembled at Stage 5 —
the Workflow never fabricates, estimates, or substitutes a placeholder for
a missing collector result. A failed section is excluded from Knowledge
Storage and is reflected as missing when the plan reaches Stage 9, so a
human reviewer can see what was not obtained rather than being shown an
incomplete record as if it were complete.

--------------------------------------------------

## 6. Verification Rules

Verification (Stage 6) is owned by Knowledge Verification
(`KNOWLEDGE_VERIFICATION.md`), which is the sole authority on what counts
as verified. The Research Workflow enforces only the following non-
negotiable gate conditions on top of that authority:

- Research is NOT stored before verification. Every Collector Result
  coming out of Stage 4 is unverified by definition; it must pass through
  Stage 5 (Assembly) and Stage 6 (Verification) before it can reach Stage 7
  (Knowledge Storage).
- Only verified knowledge enters the Knowledge Base. A section that fails
  verification is treated the same as a failed collector: it is excluded
  from this run, not stored in a partial or unverified state.

The Research Workflow does not itself define the detailed criteria a fact
must meet to count as verified — that judgment belongs entirely to
Knowledge Verification, per `KNOWLEDGE_VERIFICATION.md`.

--------------------------------------------------

## 7. Knowledge Storage Rules

Knowledge Storage (Stage 7) is owned exclusively by the Research Workflow
and is the single point where anything is written into the Knowledge Base.
It performs exactly two kinds of writes over a Research Session's
lifetime, and no other component performs either of them:

- **Verified Knowledge writes.** Only Collector Results that passed
  Verification (Stage 6) are written. Nothing unverified is ever written
  into the Knowledge Base — there is no "draft" or "pending" write path for
  unverified knowledge.
- **Approval Status writes.** Once Human Review (`HUMAN_REVIEW.md`) records
  a decision — Approved, Rejected, or Needs Revision — for a stored
  Knowledge Section, Knowledge Storage persists that Approval Status
  against the already-stored section. Human Review never writes this
  itself; it hands its recorded decision to Knowledge Storage, which
  performs the write. A stored Knowledge Section with no Approval Status
  yet recorded is implicitly **Pending Review** — this is the default state
  of any Verified, stored knowledge and requires no separate write.

Storage happens per Knowledge Section, consistent with the
Mandatory/Optional structure defined in `KNOWLEDGE_MODEL.md`: a company's
knowledge record can gain new verified sections, and gain or update
Approval Statuses, over successive workflow runs without requiring every
section to be complete at once.

--------------------------------------------------

## 8. Workflow Restrictions

The Research Workflow must NEVER:

- Perform research itself.
- Call APIs directly.
- Generate scripts.
- Generate videos.
- Approve data.
- Modify user input.

The Workflow's role is coordination between stages, not execution of any
stage's underlying work. Research gathering belongs to Research Collectors
(`RESEARCH_COLLECTORS.md`), fact verification belongs to Knowledge
Verification (`KNOWLEDGE_VERIFICATION.md`), approval belongs to a human
reviewer (`HUMAN_REVIEW.md`), and the Research Plan it receives is treated
as fixed, never edited in place. Research Result Assembly and Knowledge
Storage (Stages 5 and 7) are the two exceptions the Workflow performs
directly, as their sole owner — organizing and persisting, never
researching, verifying, or approving.

--------------------------------------------------

## 9. Revision Loop

When Human Review records **Needs Revision** for a Knowledge Section (only
possible for a section that had reached Verified — see `HUMAN_REVIEW.md`
Section 5), the Research Workflow is re-entered for that section alone,
with no missing transition:

```
Needs Revision (recorded by Human Review, persisted by Knowledge Storage)
        ↓
Research Workflow re-enters at Stage 3 — Run Collectors in Parallel
   (only the flagged Knowledge Section's collector is re-triggered)
        ↓
Stage 4 — Collect Results
        ↓
Stage 5 — Research Result Assembly
   (the fresh Collector Result replaces the section's prior entry
    in the Research Session's Research Package)
        ↓
Stage 6 — Verification
        ↓
Stage 7 — Knowledge Storage
        ↓
Stage 8 — Knowledge Viewer
        ↓
Stage 9 — Ready for Human Review
   (the section is presented to Human Review again)
```

The Research Planner is never re-invoked for a revision: the Research
Profile, Research Category, Research Topic, Research Depth, and Priority
do not change — only the flagged section's Collector Result is re-gathered
and re-verified. Stages 1 and 2 are not repeated. This loop is the only way
the Research Workflow goes backward to an earlier stage after reaching
Stage 9, and it always re-enters at Stage 3, never at Stage 1 or 2; see
`RESEARCH_SESSION.md` for how a Research Session tracks this as its one
permitted backward transition.

--------------------------------------------------

## 10. Ownership

Every responsibility in the Research Engine has exactly one owner. No two
of the following overlap:

| Component | Owns | Does NOT own |
|---|---|---|
| Research Planner (`RESEARCH_PLANNER.md`) | Converting Research Input into a Research Plan: depth, priority, required Knowledge Sections. | Running collectors, assembling results, verifying, storing, approving. |
| Research Workflow (this document) | Coordinating Stages 1–9, including Research Result Assembly (Stage 5) and Knowledge Storage (Stage 7, including Approval Status writes). | Gathering data, deciding verification criteria, approving knowledge. |
| Research Collectors (`RESEARCH_COLLECTORS.md`) | Gathering exactly one Collector Result per Knowledge Section. | Assembling results across sections, verifying, storing, approving. |
| Research Result Assembly | Owned by Research Workflow (Stage 5) — not a separate component. | — |
| Knowledge Verification (`KNOWLEDGE_VERIFICATION.md`) | Verification Status for every Collector Result, including resolving Needs Human Review through human input on conflicting facts. | Approving knowledge, writing to the Knowledge Base, gathering data. |
| Human Review (`HUMAN_REVIEW.md`) | Approval Status for Knowledge Sections that reached Verified. | Verifying facts, resolving Needs Human Review, writing to the Knowledge Base. |
| Research Session (`RESEARCH_SESSION.md`) | Tracking one Research Input's lifecycle end to end, including the Revision Loop's backward transition. | Performing research, verifying, writing to the Knowledge Base. |

--------------------------------------------------

## 11. Workflow Example

**Research Plan received** (from the `RESEARCH_PLANNER.md` example):

```
Subject: Sample Manufacturing Ltd (SMFG, NSE)
Category: Stock Analysis
Research Depth: Deep Research
Priority: High

Required Knowledge Sections:
Company Information, Business Overview, Financial Information,
Products & Services, Shareholding, Management, Risks, Market Data,
Historical Price (OHLC), Technical Analysis, Sources, Metadata
```

**Stage 1 — Receive Research Plan**
The Workflow accepts this plan as its trigger for Sample Manufacturing Ltd.

**Stage 2 — Identify Required Collectors**
Twelve sections are mapped to twelve collector tasks, one per section.

**Stage 3 — Run Collectors in Parallel**
All twelve collectors are triggered at the same time.

**Stage 4 — Collect Results**
Eleven collectors return a Collector Result. The Technical Analysis
collector fails — no historical price window was available to compute
indicators from — so it returns none. The Workflow proceeds once all
twelve have reached a final outcome.

**Stage 5 — Research Result Assembly**
The eleven Collector Results are organized into one Research Package for
Sample Manufacturing Ltd. Technical Analysis has no entry, reflecting its
collector's failure.

**Stage 6 — Verification**
Ten of the eleven Collector Results in the Package each carry at least one
valid source and pass verification. The Management result arrives with no
attributable source and fails verification.

**Stage 7 — Knowledge Storage**
The ten verified sections are written into the Knowledge Base for Sample
Manufacturing Ltd, each with an implicit Approval Status of Pending Review.
Technical Analysis (collector failure) and Management (verification
failure) are excluded from this run.

**Stage 8 — Knowledge Viewer**
The ten stored sections become visible for Sample Manufacturing Ltd.
Technical Analysis and Management show as not yet available.

**Stage 9 — Ready for Human Review**
A human reviewer sees a Stock Analysis record for Sample Manufacturing Ltd
that is largely complete, with Technical Analysis and Management flagged
as missing rather than silently omitted, and decides what happens next per
`HUMAN_REVIEW.md`.

--------------------------------------------------

## 12. Final Architecture Diagram

The complete, end-to-end Research Engine architecture, from Research Input
to a fully resolved record:

```
Research Input (RESEARCH_INPUT_STANDARD.md)
   Research Profile + Research Category + Research Topic
        ↓
Research Planner (RESEARCH_PLANNER.md)
   → Research Plan (Depth, Priority, Required Knowledge Sections)
        ↓
Research Workflow — Stage 1: Receive Research Plan
        ↓
Research Workflow — Stage 2: Identify Required Collectors
        ↓
Research Workflow — Stage 3: Run Collectors in Parallel  ◄────────────┐
   → Research Collectors (RESEARCH_COLLECTORS.md)                    │
        ↓                                                            │
Research Workflow — Stage 4: Collect Results                         │
   → one Collector Result per Knowledge Section                     │
        ↓                                                            │
Research Workflow — Stage 5: Research Result Assembly                │
   → one Research Package (per-section, not merged)                  │
        ↓                                                            │
Research Workflow — Stage 6: Verification                            │
   → Knowledge Verification (KNOWLEDGE_VERIFICATION.md)               │
   → Verification Status per section: Pending / Verified /           │
     Rejected / Needs Human Review (resolved here, by a human,       │
     if conflicting)                                                 │
        ↓                                                            │
Research Workflow — Stage 7: Knowledge Storage                       │
   → Verified sections written to the Knowledge Base                │
   → Approval Status writes also happen here (see below)             │
        ↓                                                            │
Research Workflow — Stage 8: Knowledge Viewer                        │
        ↓                                                            │
Research Workflow — Stage 9: Ready for Human Review                  │
        ↓                                                            │
Human Review (HUMAN_REVIEW.md)                                       │
   → Reviewer Action per Verified section only:                     │
     Approve / Reject / Request Revision / Skip                     │
   → Approval Status recorded: Pending Review / Approved /           │
     Rejected / Needs Revision                                       │
        │                                                            │
        ├─ Approved / Rejected → Knowledge Storage persists the      │
        │   final Approval Status. Section is closed out.            │
        │                                                            │
        └─ Needs Revision → Knowledge Storage persists it, then      │
            the Revision Loop re-enters Research Workflow ───────────┘
            at Stage 3 for that section alone (Section 9 above).

Research Session (RESEARCH_SESSION.md) tracks the whole path above,
end to end, for one Research Input, including the Revision Loop, until
every section presented for approval reaches Approved or Rejected —
at which point the session reaches Completed.
```

--------------------------------------------------

## Notes

- See `RESEARCH_INPUT_STANDARD.md` for the structure of Research Input.
- See `RESEARCH_PLANNER.md` for how Research Input becomes a Research Plan.
- See `RESEARCH_COLLECTORS.md` for how each Knowledge Section's Collector
  Result is gathered.
- See `KNOWLEDGE_VERIFICATION.md` for Verification Status and how Needs
  Human Review is resolved.
- See `HUMAN_REVIEW.md` for Approval Status and the Revision Loop's origin.
- See `RESEARCH_SESSION.md` for how one Research Input's progress, across
  every stage in this document, is tracked end to end.
- See `KNOWLEDGE_MODEL.md` for the definition of every Knowledge Section
  referenced in this document. What `KNOWLEDGE_MODEL.md` refers to as the
  Fact Validation Layer is the same component this document and every other
  Research Engine document calls Knowledge Verification
  (`KNOWLEDGE_VERIFICATION.md`) — one component, one name going forward.
