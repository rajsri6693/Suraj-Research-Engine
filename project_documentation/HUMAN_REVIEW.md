# Human Review

This document defines Human Review — the final decision point of the
Research Engine, where a human decides whether knowledge is marked
Approved. It describes responsibility and decision rules only — no schema,
no SQL, no implementation.

--------------------------------------------------

## 1. Purpose

Human Review is the last stage of the pipeline described in
`RESEARCH_WORKFLOW.md` — it is what Stage 9 (Ready for Human Review) hands
off to. Its purpose is to let a human look at the knowledge that Knowledge
Verification found trustworthy enough to store, and decide whether it is
actually fit to be marked Approved.

Human Review NEVER performs research. Human Review NEVER verifies facts —
source validation, duplicate detection, and every other trust check, along
with resolving Needs Human Review, belong to `KNOWLEDGE_VERIFICATION.md`
and are already complete by the time knowledge reaches this stage. Human
Review ONLY reviews what the Research Engine has already collected and
verified; it adds human judgment on top, it does not repeat or redo the
steps before it.

--------------------------------------------------

## 2. Review Input

Human Review receives, for a given Research Profile and Research Category:

- **Verified Knowledge** — the knowledge that reached Verified status under
  `KNOWLEDGE_VERIFICATION.md` and was stored at Research Workflow Stage 7,
  now visible through the Knowledge Viewer.
- **Verification Report** — the full Human-readable report produced by
  Knowledge Verification (Knowledge Section, Verification Status, Reason,
  Source Count, Confidence, Last Updated), covering every section that was
  evaluated, not only the ones that reached Verified. This gives the
  reviewer full context, including sections that are Rejected, Needs Human
  Review, or still Pending — shown for context only, per Section 4.
- **Sources** — the Collected Sources backing each section, per the Sources
  section of `KNOWLEDGE_MODEL.md`.
- **Metadata** — the record-level metadata defined by the Metadata section
  of `KNOWLEDGE_MODEL.md`, including freshness and completeness indicators.

--------------------------------------------------

## 3. Review Output

Human Review produces exactly one of three outcomes per Knowledge Section:

- **Approved**
- **Rejected**
- **Needs Revision**

Output is assigned at the same section granularity Knowledge Verification
already uses, so a reviewer can approve some sections of a record while
sending others back for revision. A record's overall status is the
aggregate of its individual sections — a Research Profile's knowledge is
not fully Approved until every section eligible for review has reached
Approved or Rejected (see Section 5 for eligibility).

--------------------------------------------------

## 4. Review Screen

The reviewer sees exactly the following, for one Research Profile and
Research Category at a time:

- **Research Topic** — the original topic text, restated from the Research
  Input that started this run.
- **Research Category** — restated from Research Input.
- **Research Profile** — the company or companies this record concerns,
  restated from Research Input.
- **Knowledge Sections** — one entry per section covered by the
  Verification Report.
- **Verification Status** — Pending, Verified, Rejected, or Needs Human
  Review, per `KNOWLEDGE_VERIFICATION.md`, shown for every section.
- **Sources** — the Collected Sources backing each section.
- **Confidence** — High, Medium, or Low, carried over from the Verification
  Report.
- **Last Updated** — the retrieval or collection timestamp for each
  section.

The Review Screen never shows more than what Knowledge Verification
already produced. It presents that output for a human to act on; it does
not add new facts, scores, or judgments of its own before the reviewer
acts. Sections whose Verification Status is not Verified are displayed for
context but carry no Reviewer Action controls — see Section 5.

--------------------------------------------------

## 5. Reviewer Actions

Only Knowledge Sections whose Verification Status is **Verified** are
eligible for any Reviewer Action. This applies to all four actions below,
without exception. A section at Rejected, Pending, or Needs Human Review is
never actionable here — Rejected and Pending sections were excluded from
storage entirely and never reached the Review Screen with a Reviewer
Action available, and a Needs Human Review section is still unresolved at
`KNOWLEDGE_VERIFICATION.md`: it is displayed on the Review Screen for
context only, exactly like Rejected and Pending sections, until Knowledge
Verification resolves it to Verified or Rejected.

- **Approve** — The reviewer confirms a Verified Knowledge Section is
  accurate and fit for use. This is the only action that results in
  Approved status.
- **Reject** — The reviewer determines a Verified Knowledge Section should
  not be treated as usable knowledge, despite having passed verification.
  The section is marked Rejected and excluded from the Approved record.
- **Request Revision** — The reviewer determines a Verified Knowledge
  Section is close but not yet acceptable — for example it needs
  re-collection with better sourcing, or a fresher snapshot. The section is
  marked Needs Revision and re-enters `RESEARCH_WORKFLOW.md` through the
  Revision Loop (Section 9 below) rather than being closed out.
- **Skip** — The reviewer defers a decision on a Verified Knowledge Section
  without approving, rejecting, or requesting revision. The section remains
  Pending Review so the same or another reviewer can return to it later.
  Skip is used when the reviewer needs more information or time before
  deciding.

--------------------------------------------------

## 6. Approval Rules

Only a Human can approve. The Research Engine — including Knowledge
Verification, Research Workflow, and every collector — can never mark
knowledge as Approved.

"Verified" and "Approved" are never the same thing. Verified is a
system-level trust judgment produced by `KNOWLEDGE_VERIFICATION.md`.
Approved is exclusively a human judgment produced by this stage. Verified
Knowledge that no reviewer has acted on stays at Pending Review
indefinitely — it never defaults to Approved simply because time has
passed or because no objection was raised.

--------------------------------------------------

## 7. Approval Status

Approval Status is assigned only to Knowledge Sections that reached
Verified and were stored; it is a separate, later status from Verification
Status, and it is persisted by Knowledge Storage (`RESEARCH_WORKFLOW.md`
Stage 7) — Human Review records the decision, but Knowledge Storage is what
writes it.

- **Pending Review** — A Verified Knowledge Section has reached the Review
  Screen but no Reviewer Action has been taken yet, or the reviewer chose
  Skip. This is the default status for every Verified section entering
  Human Review, and requires no separate write — it is the implicit state
  of any stored Verified section with no other Approval Status recorded.
- **Approved** — A human reviewer took the Approve action. This is the
  only status that represents knowledge as release-ready.
- **Rejected** — A human reviewer took the Reject action. The section is
  excluded from the Approved record.
- **Needs Revision** — A human reviewer took the Request Revision action.
  The section is not closed out; Knowledge Storage persists this status,
  and the section re-enters `RESEARCH_WORKFLOW.md` through the Revision
  Loop (Section 9 below) for another pass before it can be reconsidered.

Knowledge Sections that never reached Verified (Rejected, Needs Human
Review, or still Pending under `KNOWLEDGE_VERIFICATION.md`) are shown on
the Review Screen for context but do not receive an Approval Status of any
kind — they remain governed entirely by Verification Status until
Knowledge Verification resolves them.

--------------------------------------------------

## 8. Restrictions

Human Review must NEVER:

- Perform research.
- Modify collected knowledge.
- Generate scripts.
- Generate videos.
- Call APIs.
- Write directly to the database.

Human Review records a reviewer's decision; it does not carry that decision
out. Gathering knowledge belongs to Research Collectors
(`RESEARCH_COLLECTORS.md`), trust checks and resolving Needs Human Review
belong to `KNOWLEDGE_VERIFICATION.md`, and writing a recorded decision into
the Knowledge Base belongs exclusively to Knowledge Storage
(`RESEARCH_WORKFLOW.md` Stage 7) — Human Review only ever hands its
decision to that stage; it never performs the write itself.

--------------------------------------------------

## 9. Revision Loop

A Needs Revision decision is not a closed outcome — it is the start of a
fully defined loop back through `RESEARCH_WORKFLOW.md`:

```
Human Review records Needs Revision for a Knowledge Section
        ↓
Knowledge Storage persists Approval Status = Needs Revision
        ↓
Research Workflow re-enters at Stage 3 — Run Collectors in Parallel,
   for that Knowledge Section only
        ↓
Stage 4 — Collect Results  →  Stage 5 — Research Result Assembly
        ↓
Stage 6 — Verification
        ↓
Stage 7 — Knowledge Storage  →  Stage 8 — Knowledge Viewer
        ↓
Stage 9 — Ready for Human Review
        ↓
Human Review presents the section again, with a fresh Verification Status
```

The Research Planner is never re-invoked, and no new Research Plan is
produced — the Research Profile, Category, Topic, Depth, and Priority are
unchanged. Only the flagged section's Collector Result is re-gathered and
re-verified. See `RESEARCH_SESSION.md` for how a Research Session tracks
this loop as its one permitted backward transition.

--------------------------------------------------

## 10. Human Review Example

**Review Screen**

```
Research Profile: Sample Manufacturing Ltd (SMFG, NSE)
Research Category: Stock Analysis
Research Topic: Full analysis ahead of quarterly results next week.
```

| Knowledge Section | Verification Status | Sources | Confidence | Last Updated | Reviewer Action | Approval Status |
|---|---|---|---|---|---|---|
| Company Information | Verified | 2 | High | 2026-07-08 | Approve | Approved |
| Business Overview | Verified | 1 | Medium | 2026-07-08 | Approve | Approved |
| Financial Information | Needs Human Review | 2 | Low | 2026-07-09 | — (not eligible; unresolved at Knowledge Verification) | — |
| Products & Services | Verified | 1 | Medium | 2026-07-08 | Approve | Approved |
| Shareholding | Verified | 1 | Medium | 2026-07-07 | Skip | Pending Review |
| Management | Rejected | 0 | Low | 2026-07-09 | — (not eligible; never reached Verified) | — |
| Risks | Pending | 1 | — | 2026-07-09 | — (not eligible; never reached Verified) | — |
| Market Data | Verified | 1 | High | 2026-07-09 | Approve | Approved |
| Historical Price (OHLC) | Verified | 1 | High | 2026-07-08 | Reject | Rejected |

**Outcome:** Four sections are Approved. Shareholding was Skipped and
remains Pending Review for a future pass. Historical Price (OHLC) was
Rejected by the reviewer despite reaching Verified — passing verification
did not guarantee approval. Financial Information, Management, and Risks
never reached Verified, so none of them carry a Reviewer Action or an
Approval Status — Financial Information's conflicting figures are still
awaiting resolution back at Knowledge Verification, not here. The Research
Profile's record as a whole is not yet fully Approved: it remains partly
Pending Review, partly unresolved at Knowledge Verification, and partly
Rejected alongside its Approved sections.

--------------------------------------------------

## Notes

- See `RESEARCH_WORKFLOW.md` for how Human Review follows Stage 9 (Ready
  for Human Review), for the Revision Loop's full re-entry mechanics, and
  for the Ownership table confirming this document's boundaries.
- See `KNOWLEDGE_VERIFICATION.md` for the Verification Status and
  Verification Report that Human Review consumes as input, and for how
  Needs Human Review is resolved before a section ever reaches this stage.
- See `KNOWLEDGE_MODEL.md` for the definition of every section, and the
  Sources and Metadata fields, referenced in this document.
- This document defines review and approval responsibility only. Research
  gathering, verification, and storage are each owned by their own layer —
  see `ROADMAP.md`.
