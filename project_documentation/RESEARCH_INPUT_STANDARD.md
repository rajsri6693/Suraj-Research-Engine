# Research Input Standard

This document defines the standard structure of Research Input — the
information that must be supplied before the Research Planner can produce a
Research Plan. It describes structure and responsibility only — no schema,
no SQL, no code.

Research Input is the starting point of the Research Engine pipeline. It
carries no facts and no research results of its own; it only states what
should be researched, about what, and at what angle.

--------------------------------------------------

## Purpose

To give every component downstream of intake (starting with the Research
Planner) one consistent, predictable shape for "what has been asked for,"
so that planning logic never has to guess the meaning of its input.

--------------------------------------------------

## Research Input Structure

Research Input has exactly three components:

1. Research Profile
2. Research Category
3. Research Topic

All three are required. Research Input is incomplete, and must not be
accepted by the Research Planner, if any component is missing.

--------------------------------------------------

## Research Profile

**Purpose:** Identify which company or companies the research is about.

**What belongs here:** One or more company identifiers (legal name, common
name, or ticker symbol) and, where relevant, the exchange each identifier
trades on. This mirrors the identity fields owned by the Company Information
section of `KNOWLEDGE_MODEL.md` — the Research Profile is a pointer to that
identity, not a duplicate of it.

**Why it exists:** No research request is meaningful without knowing which
company (or companies) it concerns. Separating the profile from the category
and topic keeps "who" distinct from "what kind of research" and "what
specifically."

**Cardinality:**
- Single-company categories (Market News, Stock Update, Stock Analysis)
  require exactly one company identifier.
- Sector Analysis requires either a sector identifier or a representative
  set of companies within that sector.
- Comparison requires two or more company identifiers.

--------------------------------------------------

## Research Category

**Purpose:** Classify the kind of research being requested.

**What belongs here:** Exactly one value from a fixed set of categories.
This document does not define new categories — it uses the same category
list the Research Planner selects Knowledge Sections against:

- Market News
- Stock Update
- Stock Analysis
- Sector Analysis
- Comparison

**Why it exists:** The category is what allows the Research Planner to
decide which Knowledge Sections, what research depth, and what
priority apply — without it, a topic alone is ambiguous.

--------------------------------------------------

## Research Topic

**Purpose:** State, in plain language, the specific angle or question the
research should address.

**What belongs here:** A short, human-written description of the specific
information need — for example "latest quarterly results," "impact of the
new import duty on margins," or "compare debt levels over the last three
years." The topic narrows the category to something concrete.

**Why it exists:** The category identifies the kind of research; the topic
identifies the specific instance of it. The Research Planner reads the
topic's wording (for urgency, breadth, or specificity) to refine research
depth and priority within the bounds set by the category.

--------------------------------------------------

## Validity Rules

Research Input is valid only if:

- A Research Profile is present and satisfies the cardinality rule for the
  chosen Research Category.
- A Research Category is present and matches one of the fixed category
  values.
- A Research Topic is present and is not empty.

This document defines what makes Research Input well-formed. It does not
define how the Research Planner interprets a well-formed input — that
responsibility belongs to `RESEARCH_PLANNER.md`.

--------------------------------------------------

## Example Research Input

- Research Profile: Sample Manufacturing Ltd (Ticker: SMFG, Exchange: NSE)
- Research Category: Stock Analysis
- Research Topic: "Full analysis ahead of quarterly results next week."

--------------------------------------------------

## Restrictions

Research Input:

- Does NOT contain research results or facts.
- Does NOT contain Knowledge Model data.
- Does NOT determine research depth or priority — those are Research
  Planner decisions.
- Does NOT call APIs.
- Does NOT access the database.

--------------------------------------------------

## Notes

- See `KNOWLEDGE_MODEL.md` for the definition of the knowledge sections a
  Research Profile ultimately points to.
- See `RESEARCH_PLANNER.md` for how Research Input is converted into a
  Human-readable Research Plan.
