# Research Result Assembly

This document defines Research Result Assembly — Stage 5 of
`RESEARCH_WORKFLOW.md`, responsible for combining all Collector Results
into one complete Research Package. It describes responsibility and output
structure only — no schema, no SQL, no implementation.

--------------------------------------------------

## 1. Purpose

Every required Knowledge Section is gathered by its own independent
collector, running in parallel, per `RESEARCH_COLLECTORS.md`. Each
collector returns its own Collector Result, on its own schedule, with no
awareness of any other collector. Something has to turn that scattered set
of per-section results into one coherent, reviewable object before
Verification, Storage, or a human can make sense of it — that is why
Research Result Assembly exists.

Research Result Assembly organizes; it never merges facts together, never
judges them, and never acts on them. It takes whatever Collector Results
exist for a Research Workflow run and arranges them, one entry per
Knowledge Section, into a single Research Package.

Research Result Assembly NEVER performs research. It NEVER verifies
knowledge. It NEVER approves knowledge. It NEVER writes directly to the
database.

--------------------------------------------------

## 2. Assembly Input

Research Result Assembly receives only Collector Results — the outputs
Research Collectors returned at Research Workflow Stage 4. It does not
fetch, request, or look up anything else.

Each Collector Result, per `RESEARCH_COLLECTORS.md`, contains:

- **Knowledge Section** — which section this result belongs to.
- **Collected Data** — the gathered information itself.
- **Sources** — the source or sources the data came from.
- **Collection Time** — the timestamp the data was gathered.
- **Collector Status** — Success, Partial, or Failed.

The identifying context that labels the finished Research Package —
Research Session, Research Topic, Research Profile, and Research
Category — is not a second input Assembly fetches. It is carried through
from the Research Plan and Research Session already active for this
Research Workflow run (established at Stage 1) and simply attached to the
Package Assembly produces. Assembly does not look this information up
itself.

--------------------------------------------------

## 3. Assembly Output

Research Result Assembly produces exactly one artifact per run: a unified,
Human-readable **Research Package**. It contains:

- **Research Session** — the Research ID of the Research Session this
  Package belongs to, per `RESEARCH_SESSION.md`.
- **Research Topic** — restated from the Research Input that started this
  session.
- **Research Profile** — restated from the Research Input.
- **Research Category** — restated from the Research Input.
- **Knowledge Sections** — one entry for every Knowledge Section the
  Research Plan required, each carrying its status (Section 6) and, where
  available, its Collected Data, Sources, and Collection Time.
- **Collector Summary** — one row per collector triggered this run
  (Section 7).
- **Missing Sections** — the subset of required Knowledge Sections with no
  Collected Data in this Package, whether Failed or Missing (Section 6).
- **Overall Collection Status** — one aggregate value for the whole
  Package:
  - *Complete* — every required Knowledge Section reached Completed.
  - *Partial* — at least one required Knowledge Section reached Completed,
    and at least one did not.
  - *Failed* — no required Knowledge Section reached Completed.
- **Collection Completed Time** — the timestamp Assembly finished
  organizing this Package, distinct from any individual collector's
  Collection Time.

--------------------------------------------------

## 4. Assembly Responsibilities

Research Result Assembly MUST:

- **Combine Collector Results** — bring every Collector Result returned
  this run together into one Research Package.
- **Preserve every Knowledge Section** — every section the Research Plan
  required gets an entry in the Package, whether or not a Collector Result
  exists for it. Nothing required is ever silently dropped from the
  Package's structure, even when its content is absent.
- **Preserve Sources** — a Collector Result's Sources are carried into the
  Package exactly as returned, never summarized away or dropped.
- **Preserve Metadata** — a Collector Result's Collection Time and
  Collector Status are carried into the Package exactly as returned; if
  Metadata is itself a required Knowledge Section, its Collector Result is
  treated the same as any other section's.
- **Report missing sections** — every Knowledge Section without Collected
  Data is explicitly listed in Missing Sections, never left ambiguous.
- **Produce one unified Research Package** — the single output of this
  stage, structured per Section 3.

--------------------------------------------------

## 5. Assembly Restrictions

Research Result Assembly must NEVER:

- Perform research.
- Verify knowledge.
- Approve knowledge.
- Modify collected knowledge.
- Generate scripts.
- Generate videos.
- Write to the database.
- Call APIs.

Assembly touches nothing about a Collector Result's content. It does not
correct, complete, or judge Collected Data — it only decides where each
Collector Result sits within the Package. Everything about whether that
content is trustworthy belongs to `KNOWLEDGE_VERIFICATION.md`, applied at
the next stage.

--------------------------------------------------

## 6. Missing Section Handling

Every Knowledge Section the Research Plan required gets exactly one status
in the Research Package, and the four statuses below are never conflated:

- **Completed** — A collector was triggered for this section and returned
  a Collector Result with Collector Status Success or Partial. Its
  Collected Data, Sources, and Collection Time appear in the Package.
- **Failed** — A collector was triggered for this section but its
  Collector Status was Failed, per the Failure Handling rule in
  `RESEARCH_WORKFLOW.md`: no Collector Result was returned, so nothing is
  fabricated in its place. The section appears in Missing Sections.
- **Missing** — No collector could be identified for this section at all
  at Research Workflow Stage 2 (Identify Required Collectors) — for
  example, the Research Plan required a section with no corresponding
  entry in `RESEARCH_COLLECTORS.md`'s Knowledge Section table — so no
  collector was ever triggered. The section appears in Missing Sections.
- **Skipped** — This Assembly run was not responsible for gathering this
  section at all. This applies specifically during a Revision Loop pass
  (`RESEARCH_WORKFLOW.md` Section 9): only the flagged Knowledge Section's
  collector is re-triggered, so every other required section keeps
  whatever entry — Completed, Failed, or Missing — it already carried in
  the Research Session's existing Research Package from an earlier pass,
  unchanged. A Skipped section is not treated as absent; its prior entry
  is what stands.

Completed is the only status with Collected Data attached. Failed,
Missing, and Skipped never carry fabricated or placeholder content —
Assembly reports the absence itself, precisely categorized, rather than
guessing at what a missing section might have contained.

--------------------------------------------------

## 7. Collector Summary

Alongside the Knowledge Sections list, the Research Package includes one
Collector Summary entry for every collector triggered during this
Assembly run:

- **Collector Name** — the collector's name, per `RESEARCH_COLLECTORS.md`
  Section 6 (for example, "Financial Information Collector").
- **Execution Status** — the Collector Status it returned: Success,
  Partial, or Failed.
- **Completion Time** — the timestamp the collector reached that status.

The Collector Summary is a log of what ran; the Knowledge Sections list
(Section 3) is the resulting content view. A section marked Skipped in the
Knowledge Sections list has no corresponding row here, since no collector
ran for it during this Assembly run.

--------------------------------------------------

## 8. Workflow Ownership

Research Result Assembly belongs to the Research Workflow. It is Stage 5
of `RESEARCH_WORKFLOW.md`, not an independent workflow, not a separate
architectural layer, and not a component with its own lifecycle apart from
the Research Workflow run it executes within.

It executes after all required collectors for this run have finished —
meaning every collector triggered at Stage 3 has reached a final Collector
Status of Success, Partial, or Failed, not that every collector has
succeeded. A slow or failed collector does not block Assembly indefinitely;
it simply means that collector's section reaches Assembly as Failed rather
than Completed, per Section 6.

--------------------------------------------------

## 9. Research Package Example

**Research Plan:** Sample Manufacturing Ltd (SMFG, NSE) — Stock Analysis,
twelve required Knowledge Sections (per the `RESEARCH_WORKFLOW.md` Workflow
Example).

```
Research Package

Research Session: RS-2026-0709-001
Research Topic: Full analysis ahead of quarterly results next week.
Research Profile: Sample Manufacturing Ltd (SMFG, NSE)
Research Category: Stock Analysis

Knowledge Sections:
- Company Information — Completed
- Business Overview — Completed
- Financial Information — Completed
- Products & Services — Completed
- Shareholding — Completed
- Management — Completed
- Risks — Completed
- Market Data — Completed
- Historical Price (OHLC) — Completed
- Technical Analysis — Failed
- Sources — Completed
- Metadata — Completed

Collector Summary:
| Collector Name                        | Execution Status | Completion Time    |
|----------------------------------------|-------------------|---------------------|
| Company Information Collector          | Success           | 2026-07-09 09:05    |
| Business Overview Collector            | Success           | 2026-07-09 09:05    |
| Financial Information Collector        | Success           | 2026-07-09 09:06    |
| Products & Services Collector          | Success           | 2026-07-09 09:05    |
| Shareholding Collector                 | Success           | 2026-07-09 09:07    |
| Management Collector                   | Success           | 2026-07-09 09:06    |
| Risks Collector                        | Success           | 2026-07-09 09:08    |
| Market Data Collector                  | Success           | 2026-07-09 09:04    |
| Historical Price Collector             | Success           | 2026-07-09 09:06    |
| Technical Analysis Collector           | Failed            | 2026-07-09 09:09    |
| Sources Collector                      | Success           | 2026-07-09 09:05    |
| Metadata Collector                     | Success           | 2026-07-09 09:04    |

Missing Sections:
- Technical Analysis — Failed (no historical price window was available
  to compute indicators from)

Overall Collection Status: Partial
Collection Completed Time: 2026-07-09 09:10
```

Eleven sections reached Completed; Technical Analysis reached Failed and
is called out in Missing Sections rather than left unexplained. This
Research Package, exactly as assembled here, is what Research Workflow
Stage 6 (Verification) receives next — Assembly's responsibility ends the
moment this Package is produced.

--------------------------------------------------

## Notes

- See `RESEARCH_WORKFLOW.md` for how Assembly (Stage 5) fits between
  Collect Results (Stage 4) and Verification (Stage 6), and for the
  Ownership table confirming this document's boundaries.
- See `RESEARCH_COLLECTORS.md` for the Collector Result fields Assembly
  consumes and the Knowledge Section-to-collector mapping.
- See `RESEARCH_PLANNER.md` for how Required Knowledge Sections are
  determined in the first place.
- See `RESEARCH_SESSION.md` for how a Research Package persists and is
  updated, unchanged in its Skipped sections, across a Revision Loop pass.
- See `KNOWLEDGE_MODEL.md` for the definition of every Knowledge Section
  referenced in this document.
- This document defines assembly responsibility only. Verification,
  storage, and approval are each owned by their own layer — see
  `ROADMAP.md`.
