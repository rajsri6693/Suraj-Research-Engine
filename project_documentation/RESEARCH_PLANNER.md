# Research Planner

This document defines the Research Planner — the decision-making component
of the Research Engine. It describes responsibility and behavior only — no
schema, no SQL, no code.

--------------------------------------------------

## 1. Purpose

The Research Planner converts Research Input into a Human-readable Research
Plan.

It is the sole decision-making step between "what was asked for" and "what
gets researched." It decides scope, depth, priority, and required Knowledge
Model coverage — it does not act on any of those decisions itself.

The Research Planner does NOT perform research. It does NOT call APIs. It
does NOT access the database. It only reasons over Research Input and
produces a plan for Research Workflow to carry out.

--------------------------------------------------

## 2. Planner Input

The Research Planner accepts exactly one Research Input, as defined in
`RESEARCH_INPUT_STANDARD.md`:

- **Research Profile** — which company or companies the research concerns.
- **Research Category** — the kind of research requested (Market News,
  Stock Update, Stock Analysis, Sector Analysis, or Comparison).
- **Research Topic** — the specific angle or question within that category.

The Planner does not accept partial Research Input. If any component is
missing or invalid under `RESEARCH_INPUT_STANDARD.md`, the Planner cannot
produce a plan.

--------------------------------------------------

## 3. Planner Output

The Research Planner produces exactly one artifact: a **Human-readable
Research Plan**.

The Research Plan is a plain-language document — not code, not a database
record — that states, for a single Research Input:

- What is being researched (Research Profile, Research Category, Research
  Topic, restated).
- The research depth (Quick or Deep) and why it was chosen.
- The assigned priority (High, Medium, or Low) and why it was chosen.
- The Knowledge Sections required to fulfill the request.
- The list of collectors Research Workflow should run, and the fact that
  they run in parallel.

The plan is handed to Research Workflow. The Planner's responsibility ends
once the plan is produced.

--------------------------------------------------

## 4. Research Depth Rules

The Research Planner assigns exactly one depth to every plan: Quick
Research or Deep Research.

### Quick Research

Applies when the Research Category is time-bound and narrow in scope:

- Market News
- Stock Update

Quick Research also applies when the Research Topic's wording signals a
snapshot rather than an analysis (for example: "latest," "today," "current
price," "what happened").

A Quick Research plan draws on the smallest set of Knowledge Sections
that can answer the topic, favoring the most recent data available.

### Deep Research

Applies when the Research Category requires synthesis across multiple
Knowledge Sections:

- Stock Analysis
- Sector Analysis
- Comparison

Deep Research also applies when the Research Topic's wording signals
breadth or judgment (for example: "full analysis," "compare," "outlook,"
"risks," "should we...").

A Deep Research plan draws on every Knowledge Section relevant to the
Research Category, not just the most recent data.

### Precedence

Research Category sets the default depth. Research Topic wording can
upgrade a category's default depth from Quick to Deep (for example, a Stock
Update topic that asks for underlying causes), but Topic wording never
downgrades Deep Research categories to Quick — Stock Analysis, Sector
Analysis, and Comparison always remain at least Deep Research.

--------------------------------------------------

## 5. Knowledge Selection Rules

The Research Planner selects which `KNOWLEDGE_MODEL.md` sections a plan
requires, based on Research Category. Company Information, Business
Overview, Sources, and Metadata are the Knowledge Model's own mandatory
sections and are therefore included as a baseline for every category that
is anchored to a company.

| Research Category | Required Knowledge Sections |
|--------------------|-----------------------------------|
| Market News | Company Information, Market News, Sources, Metadata. Government Policies when the news is policy-driven. |
| Stock Update | Company Information, Market Data, Historical Price (OHLC), Sources, Metadata. Corporate Actions when a corporate action is the cause of the update. |
| Stock Analysis | Company Information, Business Overview, Financial Information, Products & Services, Shareholding, Management, Risks, Market Data, Historical Price (OHLC), Technical Analysis, Sources, Metadata. |
| Sector Analysis | Sector Information, Government Policies, Company Information and Business Overview for each company in scope, Competitors, Sources, Metadata. |
| Comparison | Company Information, Business Overview, Financial Information, Competitors, Market Data, Sources, Metadata — gathered once per company being compared. |

If a required section is absent from a company's knowledge record, the
Research Plan still lists it as required — sourcing that gap is a Research
Workflow responsibility, carried out through Research Collectors, not a
Planner responsibility.

--------------------------------------------------

## 6. Research Priority

The Research Planner assigns exactly one priority to every plan: High,
Medium, or Low.

- **High** — Assigned to time-sensitive categories (Market News, Stock
  Update) and to any Research Topic whose wording signals urgency ("today,"
  "breaking," "just announced") or that is tied to an active corporate
  action or event.
- **Medium** — The default priority for Stock Analysis requests, and for
  any Deep Research plan that has no urgency signal in its Research Topic.
- **Low** — Assigned to broad, non-time-sensitive research: Sector Analysis
  and Comparison requests that are exploratory or background in nature,
  with no urgency signal in the Research Topic.

Priority is assigned from the combination of Research Category (which sets
a default) and Research Topic wording (which can raise, but never lower,
the default). A Research Topic can move a plan from Medium to High; it
cannot move a Market News or Stock Update plan below High, because those
categories are time-sensitive by definition.

--------------------------------------------------

## 7. Research Mode: Parallel Collectors

Every Research Plan lists its required Knowledge Sections as independent
collector tasks intended to run in parallel, not in sequence.

**Why collectors work in parallel:** Each Knowledge Section is an
independently verifiable domain of fact — Financial Information does not
depend on Management, Market Data does not depend on Competitors, and so
on. Because the sections have no dependency on one another, gathering them
one after another would only add wall-clock time without adding accuracy.
The Planner therefore expresses the plan as a set of concurrent collector
tasks, one per required section.

The Planner only specifies that collectors run in parallel. It does not
run them, schedule them, manage their execution, or assemble their
results — that belongs entirely to Research Workflow, specifically
Research Result Assembly (`RESEARCH_WORKFLOW.md` Stage 5), which is the
sole owner of combining collector output into a Research Package.

--------------------------------------------------

## 8. Planner Restrictions

The Research Planner must NEVER:

- Perform research.
- Call APIs.
- Save data.
- Verify data.
- Generate scripts.
- Generate videos.
- Modify the database.

The Planner's only output is a Human-readable Research Plan. Every action
beyond producing that plan belongs to a different layer of the Research
Engine.

--------------------------------------------------

## 9. Planner Output Example

**Research Input**

- Research Profile: Sample Manufacturing Ltd (Ticker: SMFG, Exchange: NSE)
- Research Category: Stock Analysis
- Research Topic: "Full analysis ahead of quarterly results next week."

**Research Plan**

```
Research Plan

Subject: Sample Manufacturing Ltd (SMFG, NSE)
Category: Stock Analysis
Topic: Full analysis ahead of quarterly results next week.

Research Depth: Deep Research
Reason: Stock Analysis is always Deep Research. The topic's wording
("full analysis") confirms breadth is expected.

Priority: High
Reason: Stock Analysis defaults to Medium, but the topic ties the
request to an imminent event (quarterly results next week), which
raises it to High.

Required Knowledge Sections:
- Company Information
- Business Overview
- Financial Information
- Products & Services
- Shareholding
- Management
- Risks
- Market Data
- Historical Price (OHLC)
- Technical Analysis
- Sources
- Metadata

Research Mode: Parallel Collectors
Each section above is assigned to its own collector task. All
collector tasks run concurrently; none depends on another's result.

End of Plan.
```

--------------------------------------------------

## Notes

- See `RESEARCH_INPUT_STANDARD.md` for the structure of Research Input.
- See `KNOWLEDGE_MODEL.md` for the definition of every section referenced
  in this document.
- See `RESEARCH_WORKFLOW.md` for the complete Ownership table and how the
  Research Plan is executed, including Research Result Assembly.
- This document defines planning responsibility only. Execution,
  validation, and storage are owned by later layers — see `ROADMAP.md`.
