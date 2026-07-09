# Knowledge Verification

This document defines Knowledge Verification — the layer of the Research
Engine responsible for deciding whether collected knowledge is trustworthy
enough to enter the Knowledge Base. It describes responsibility and
decision rules only — no schema, no SQL, no implementation.

Knowledge Verification is what `KNOWLEDGE_MODEL.md` refers to as the Fact
Validation Layer — one component, described in full here.

--------------------------------------------------

## 1. Purpose

Knowledge Verification sits between Research Workflow Stage 5 (Research
Result Assembly) and Stage 7 (Knowledge Storage) — it is the specification
for Stage 6 (Verification) defined in `RESEARCH_WORKFLOW.md`. Its job is
to decide, for each Collector Result inside a Research Session's Research
Package, whether that result is trustworthy enough to be stored.

Knowledge Verification NEVER performs research. It NEVER generates
scripts. It NEVER approves data. Deciding that knowledge is trustworthy
enough to store is not the same as approving it — human approval, reached
at Research Workflow Stage 9 (Ready for Human Review) via Human Review, is
always the final authority. Knowledge Verification narrows what reaches a
human; it never replaces the human's decision.

--------------------------------------------------

## 2. Verification Input

Knowledge Verification receives exactly three things for each Knowledge
Section it evaluates, drawn from the Research Package assembled at
Research Workflow Stage 5:

- **Collector Result** — the raw, unverified result a single collector
  returned at Research Workflow Stage 4, for one Knowledge Section, for one
  Research Profile.
- **Collected Sources** — the source records that accompany that Collector
  Result, matching the fields defined by the Sources section of
  `KNOWLEDGE_MODEL.md`: source name, source URL or reference, source type,
  and retrieval date.
- **Metadata** — the record-level metadata defined by the Metadata section
  of `KNOWLEDGE_MODEL.md` that is relevant to assessing this result, at
  minimum a collection or retrieval timestamp.

Verification always operates at the granularity of one Knowledge Section
for one Research Profile at a time — one Collector Result out of the
Research Package, never the whole Package at once.

--------------------------------------------------

## 3. Verification Output

Knowledge Verification produces exactly one of two outcomes for each
Knowledge Section it evaluates:

- **Verified Knowledge** — proceeds to Research Workflow Stage 7 (Knowledge
  Storage).
- **Rejected Knowledge** — excluded from storage for this run, handled the
  same way as a failed collector under `RESEARCH_WORKFLOW.md`'s failure
  handling: not fabricated, not stored, reflected as missing rather than
  silently dropped.

A section that cannot yet be resolved to either outcome (see Verification
Status, Section 5) does not proceed to storage either — only a section that
reaches Verified is stored. Every evaluated section, regardless of outcome,
produces an entry in the Verification Report (Section 6).

--------------------------------------------------

## 4. Verification Rules

**Source validation**
Every fact in a Collector Result must trace to at least one entry in
Collected Sources with a name or reference, a source type, and a retrieval
date. Knowledge with no source, or with a source missing these fields,
fails verification — this is the same rule stated in `RESEARCH_WORKFLOW.md`:
every knowledge section must have at least one valid source.

**Duplicate detection**
An incoming Collector Result is compared against knowledge already stored
for the same Research Profile and section. If the incoming facts are
identical in substance to what is already verified and stored, they add
nothing new and are not stored again. If the incoming facts update or
refine an existing verified fact, that is not a duplicate — it is a
legitimate update, and the section's Last Updated metadata changes
accordingly.

**Missing information**
Verification can only evaluate a Collector Result that arrived. If a
required Knowledge Section has no Collector Result at all — for example
because its collector failed — there is nothing for Verification to
evaluate, and the section is excluded from storage exactly as described
under Failure Handling in `RESEARCH_WORKFLOW.md`. Within a Collector Result
that did arrive, if fields central to that section's stated purpose in
`KNOWLEDGE_MODEL.md` are absent (for example a Financial Information entry
with no reporting period), the section fails verification for missing
information rather than being verified with gaps.

**Time-sensitive knowledge**
Sections that are inherently perishable — Market News, Market Data, and
other Quick Research categories defined in `RESEARCH_PLANNER.md` — are
checked for freshness. Knowledge whose retrieval date is stale relative to
what the Research Topic asked for (for example a price snapshot several
days old when the topic asked about "today") fails verification even if it
is properly sourced, because trustworthiness includes currency, not only
accuracy.

**Conflicting information**
When an incoming Collector Result disagrees with already-verified stored
knowledge for the same fact, Knowledge Verification does not choose a
winner automatically. Picking between two sourced but conflicting claims is
a judgment call, not an automated trustworthiness check, so conflicting
knowledge is never automatically marked Verified or Rejected — it is
marked Needs Human Review instead, and resolved as described in Section 5.

**Metadata requirements**
Every Collector Result must carry at minimum a collection or retrieval date
and a link to its Collected Sources, per the Metadata section of
`KNOWLEDGE_MODEL.md`. Knowledge missing this metadata cannot be verified —
without it, Verification has no basis for assessing freshness or detecting
duplicates, regardless of how complete the knowledge otherwise appears.

--------------------------------------------------

## 5. Verification Status

- **Pending** — A Collector Result has arrived but has not yet been
  evaluated against the Verification Rules. Every section starts here.
- **Verified** — The knowledge passed every applicable Verification Rule:
  it has valid sources, no unresolved duplicates, no missing required
  information, meets the freshness bar for its section, and has no
  unresolved conflict with existing stored knowledge. Verified is the only
  status that proceeds to Knowledge Storage, and the only status a section
  can carry to become eligible for Human Review (`HUMAN_REVIEW.md`).
- **Rejected** — The knowledge failed one or more Verification Rules for a
  clear, unambiguous reason — for example no source at all, or knowledge
  that is stale beyond its section's freshness bar. Rejected knowledge is
  excluded from storage for this run.
- **Needs Human Review** — The knowledge cannot be automatically resolved
  to Verified or Rejected, most often because of Conflicting Information.
  **Resolving this status is a Knowledge Verification responsibility, not a
  Human Review responsibility.** A human is asked to judge which
  conflicting claim is correct — that decision is recorded here, against
  Verification Status, and results in the section becoming either Verified
  or Rejected. Only after that resolution can the section reach Knowledge
  Storage and, if Verified, become eligible for Human Review's Approval
  Status. A section still at Needs Human Review is never shown as
  actionable on Human Review's Review Screen — see `HUMAN_REVIEW.md`
  Section 5.

--------------------------------------------------

## 6. Verification Report

Knowledge Verification always produces a Human-readable Verification
Report alongside its output. One entry per Knowledge Section evaluated,
containing:

- **Knowledge Section** — which `KNOWLEDGE_MODEL.md` section this entry
  covers.
- **Verification Status** — Pending, Verified, Rejected, or Needs Human
  Review.
- **Reason** — a plain-language statement of why this status was reached.
- **Source Count** — how many Collected Sources support this section's
  knowledge.
- **Confidence** — High, Medium, or Low, reflecting how strongly the
  available sources support the knowledge: High when multiple independent
  sources agree, Medium when a single valid source supports it, Low when
  sourced but thin, aging, or borderline. Confidence is independent of
  Status — even Verified knowledge can carry Medium or Low confidence,
  which is informative to the human reviewer at Research Workflow Stage 9.
- **Last Updated** — the retrieval or collection timestamp for this
  section's knowledge.

--------------------------------------------------

## 7. Restrictions

Knowledge Verification must NEVER:

- Perform research.
- Call APIs.
- Generate scripts.
- Generate videos.
- Approve data.
- Modify collected knowledge.

Knowledge Verification only evaluates what collectors already returned. It
does not gather anything itself, does not alter the facts or sources it is
given, and does not have the authority to approve a record — it only
decides whether knowledge is trustworthy enough to be stored and shown to a
human reviewer. Resolving Needs Human Review (Section 5) is the one place a
human is involved at this layer, and even that resolution only ever
produces a Verification Status, never an Approval Status.

--------------------------------------------------

## 8. Human Review

Human Review is always the final decision. Knowledge Verification's
statuses — Verified and Rejected — are inputs to human judgment at the next
layer, never substitutes for it.

Needs Human Review is resolved here, at Knowledge Verification, not at
Human Review (Section 5). Once a section reaches Verified, it is stored and
becomes visible in the Knowledge Viewer, and still arrives at Research
Workflow Stage 9 (Ready for Human Review), where a human makes the final
call on the record as a whole. Verification only decides what is
trustworthy enough to present for review — it never decides what is
approved.

--------------------------------------------------

## 9. Verification Example

**Subject:** Sample Manufacturing Ltd (SMFG, NSE) — Stock Analysis
**Snapshot taken during Research Workflow Stage 6**

| Knowledge Section | Status | Reason | Source Count | Confidence | Last Updated |
|---|---|---|---|---|---|
| Company Information | Verified | Two independent sources agree on all identity fields. | 2 | High | 2026-07-08 |
| Business Overview | Verified | Single valid source, no conflicts. | 1 | Medium | 2026-07-08 |
| Financial Information | Needs Human Review | Two sources report different net profit figures for the same quarter; awaiting a human decision on which figure is correct. | 2 | Low | 2026-07-09 |
| Products & Services | Verified | Source confirms all listed product lines. | 1 | Medium | 2026-07-08 |
| Shareholding | Verified | Source matches latest filing. | 1 | Medium | 2026-07-07 |
| Management | Rejected | No source reference accompanied the collected data. | 0 | Low | 2026-07-09 |
| Risks | Pending | Collector Result received; evaluation not yet complete. | 1 | — | 2026-07-09 |
| Market Data | Verified | Snapshot timestamp is within the freshness window required for Stock Analysis. | 1 | High | 2026-07-09 |
| Historical Price (OHLC) | Verified | Complete trading history with source citation. | 1 | High | 2026-07-08 |

*Technical Analysis is not included in this report: its collector returned
no result at Research Workflow Stage 4, so no Collector Result ever reached
Verification for that section.*

This report is handed forward as-is. Six sections proceed to Knowledge
Storage and, from there, to Human Review. Financial Information remains
here, at Knowledge Verification, awaiting a human decision between its two
conflicting figures — it does not appear as an actionable item on Human
Review's Review Screen until that conflict is resolved to Verified or
Rejected. Management is excluded this run for lacking a source. Risks
remains Pending until its evaluation completes. None of these outcomes
constitute approval — every section that does reach Human Review still
awaits its own decision there.

--------------------------------------------------

## Notes

- See `RESEARCH_WORKFLOW.md` for how Verification (Stage 6) fits between
  Research Result Assembly (Stage 5) and Knowledge Storage (Stage 7), and
  for the Ownership table confirming this document's boundaries.
- See `RESEARCH_PLANNER.md` for how Research Category determines which
  sections are time-sensitive.
- See `HUMAN_REVIEW.md` for how Verified knowledge is reviewed, and for why
  Needs Human Review sections are never shown there as actionable.
- See `KNOWLEDGE_MODEL.md` for the definition of every section and the
  Sources and Metadata fields referenced in this document, and for the
  origin of the term Fact Validation Layer, which this document implements.
