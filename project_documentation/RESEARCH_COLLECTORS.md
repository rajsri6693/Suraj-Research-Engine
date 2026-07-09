# Research Collectors

This document defines the Research Collectors architecture — the
components of the Research Engine responsible for collecting knowledge. It
describes responsibility and output structure only — no schema, no SQL, no
API implementation.

--------------------------------------------------

## 1. Purpose

A Research Collector gathers knowledge for exactly one Knowledge Section,
as instructed by a Research Plan. Collectors are what Research
Workflow Stage 3 (Run Collectors in Parallel) triggers and what Stage 4
(Collect Results) receives output from, per `RESEARCH_WORKFLOW.md`.

Research Collectors are responsible ONLY for collecting knowledge. They
NEVER verify knowledge — that is `KNOWLEDGE_VERIFICATION.md`'s
responsibility, applied at Research Workflow Stage 6. They NEVER approve
knowledge — that is Human Review's responsibility. They NEVER write
directly to the database — that is the Knowledge Storage step at Research
Workflow Stage 7. A collector's job ends the moment it returns its
Collector Result.

--------------------------------------------------

## 2. Collector Responsibilities

Each collector is scoped to exactly one Knowledge Section, matching
the one-collector-per-section rule established in `RESEARCH_PLANNER.md`
Section 7 (Parallel Collectors). A collector's only responsibility is to
gather the information belonging to that section for the Research Profile
named in the Research Plan.

- **No verification.** A collector does not judge whether what it found is
  accurate, complete, or trustworthy — it reports what it found.
- **No approval.** A collector never marks anything as accepted, final, or
  release-ready.
- **No database writing.** A collector never stores anything itself; it
  only returns collected knowledge for the Research Workflow to carry
  forward.

--------------------------------------------------

## 3. Collector Selection Rules

The Research Planner decides which collectors are required. This decision
is made once, in the Required Knowledge Sections list of the
Research Plan, per the Knowledge Selection Rules in `RESEARCH_PLANNER.md`
Section 5. Research Workflow Stage 2 (Identify Required Collectors) reads
that list and maps each required section to its collector.

Collectors never decide themselves. A collector does not choose whether it
should run, does not choose which section it covers, and does not decide
whether any other collector should also run. Those decisions belong
entirely upstream, to the Research Planner and the Research Workflow — a
collector only executes once it has been identified as required.

--------------------------------------------------

## 4. Collector Execution

- **Collectors run independently.** Each collector operates only on its
  own assigned Knowledge Section. No collector reads another
  collector's output as an input, and no collector's behavior depends on
  another collector's presence, timing, or result.
- **Collectors may run in parallel.** Per the Research Mode defined in
  `RESEARCH_PLANNER.md` and Stage 3 of `RESEARCH_WORKFLOW.md`, collectors
  for a single Research Plan are triggered concurrently, since the sections
  they gather have no dependency on one another.
- **Failure of one collector must not stop the others.** If a collector
  fails, it simply produces no result for its own section. It never
  blocks, delays, or otherwise affects the execution of any other
  collector — this mirrors the Failure Handling rule in
  `RESEARCH_WORKFLOW.md`, which treats a missing collector result as an
  absent section, never as a reason to halt the run.

--------------------------------------------------

## 5. Collector Output

Each collector returns exactly one **Collector Result** for its section, in
Human-readable form. Every Collector Result must include:

- **Knowledge Section** — which of the sections defined in
  `KNOWLEDGE_MODEL.md` this item belongs to.
- **Collected Data** — the gathered information itself, stated in plain
  language.
- **Sources** — the source or sources the data came from, matching the
  fields defined by the Sources section of `KNOWLEDGE_MODEL.md` (source
  name or reference, source type, retrieval date).
- **Collection Time** — the timestamp at which this item was gathered.
- **Collector Status** — one of:
  - *Success* — the collector completed and returned data for its section.
  - *Partial* — the collector returned some data for its section but could
    not complete the full collection.
  - *Failed* — the collector could not return any data for its section.

Collector Status describes only whether the collection attempt itself
completed — it is not a judgment about accuracy or trustworthiness. That
judgment belongs to `KNOWLEDGE_VERIFICATION.md`, applied later and
separately.

--------------------------------------------------

## 6. Knowledge Sections

Each Knowledge Section defined in `KNOWLEDGE_MODEL.md` has exactly
one corresponding collector:

| Knowledge Section | Responsible Collector |
|---|---|
| Company Information | Company Information Collector |
| Business Overview | Business Overview Collector |
| Products & Services | Products & Services Collector |
| Management | Management Collector |
| Shareholding | Shareholding Collector |
| Financial Information | Financial Information Collector |
| Orders & Contracts | Orders & Contracts Collector |
| Competitors | Competitors Collector |
| Risks | Risks Collector |
| Market News | Market News Collector |
| Sector Information | Sector Information Collector |
| Government Policies | Government Policies Collector |
| Market Data | Market Data Collector |
| Historical Price (OHLC) | Historical Price Collector |
| Technical Analysis | Technical Analysis Collector |
| Corporate Actions | Corporate Actions Collector |
| Sources | Sources Collector |
| Metadata | Metadata Collector |

A collector never gathers data belonging to a section other than the one
it is assigned. This one-to-one mapping is what makes the sections
independent and safe to collect in parallel, per Section 4 above.

--------------------------------------------------

## 7. Collector Restrictions

Collectors must NEVER:

- Verify information.
- Approve information.
- Generate scripts.
- Generate videos.
- Write directly into the database.
- Modify user input.

A collector's contract is narrow by design: receive a section assignment
from the Research Plan, gather what it can find for that section, and
return it. Every responsibility outside that contract belongs to a
different layer of the Research Engine.

--------------------------------------------------

## 8. Collector Example

**Collector:** Financial Information Collector
**Research Profile:** Sample Manufacturing Ltd (SMFG, NSE)

```
Knowledge Section: Financial Information
Collected Data: Q4 FY2026 quarterly filing reports revenue of ₹412
  crore and net profit of ₹28 crore for the period ending 2026-06-30.
Sources: Sample Manufacturing Ltd Q4 FY2026 quarterly filing,
  retrieved 2026-07-09.
Collection Time: 2026-07-09 09:14
Collector Status: Success
```

This is the complete, unverified Collector Result the Financial
Information Collector hands to Research Workflow Stage 4. It is not
assembled, stored, verified, or approved by the collector itself — those
steps belong to Research Workflow's Research Result Assembly,
`KNOWLEDGE_VERIFICATION.md`, and Human Review, which act on this Collector
Result afterward.

--------------------------------------------------

## Notes

- See `RESEARCH_WORKFLOW.md` for how collectors fit between Stage 2
  (Identify Required Collectors) and Stage 4 (Collect Results), and for how
  Research Result Assembly (Stage 5) and Verification (Stage 6) act on
  Collector Results afterward.
- See `RESEARCH_PLANNER.md` for how the Research Plan determines which
  collectors are required and why they run in parallel.
- See `KNOWLEDGE_MODEL.md` for the definition of every section a collector
  is scoped to.
- See `RESEARCH_WORKFLOW.md` for the complete Ownership table confirming
  this document's boundaries.
- This document defines collection responsibility only. Verification,
  approval, and storage are each owned by their own layer — see
  `ROADMAP.md`.
