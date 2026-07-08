# Knowledge Model

This document defines every knowledge section that can exist inside the
Verified Knowledge Database. It describes responsibilities only — no schema,
no SQL, no code.

Each section below is a logical grouping of verified facts about a company
(or, where noted, about its surrounding context). A section becomes part of
a company's knowledge record once at least one fact belonging to it has
passed the Fact Validation Layer.

For each section this document states its purpose, what data belongs there,
why it exists, and whether it is mandatory or optional for a company record
to be considered usable.

--------------------------------------------------

## Company Information

**Purpose:** Identify the company itself, unambiguously.

**What belongs here:** Legal name, common/brand name, registration details,
country of incorporation, headquarters location, founding date, website,
stock exchange(s) and ticker symbol(s).

**Why it exists:** Every other section is meaningless without a stable
anchor identifying which company the facts describe. This section is the
root of the knowledge record.

**Mandatory or Optional:** Mandatory. No knowledge record can exist without it.

## Business Overview

**Purpose:** Explain what the company does in plain terms.

**What belongs here:** Business description, mission, industry and sector
classification, business model summary, geographic footprint, core
customer segments.

**Why it exists:** Provides the narrative context needed to interpret every
other section — financials, products, and risks only make sense once the
underlying business is understood.

**Mandatory or Optional:** Mandatory.

## Products & Services

**Purpose:** Catalog what the company sells or offers.

**What belongs here:** Product lines, service offerings, brands, revenue
segments tied to each offering, target markets per offering.

**Why it exists:** Downstream analysis and content generation need to know
what the company actually produces, not just what industry it belongs to.

**Mandatory or Optional:** Optional. Present when the company's offerings
have been researched and verified; absent for companies not yet covered at
that depth.

## Financial Information

**Purpose:** Hold verified financial facts about the company.

**What belongs here:** Revenue, profit, margins, balance sheet figures,
cash flow figures, key financial ratios, historical financial trends,
reporting period and currency for each figure.

**Why it exists:** Financial standing is one of the most frequently
requested and most fact-sensitive categories of research; it must be kept
distinct so it can carry stricter verification requirements.

**Mandatory or Optional:** Optional at the record level, but any individual
financial fact that is stored must be verified — partial or estimated
figures are not permitted in this section.

## Orders & Contracts

**Purpose:** Track material orders, contracts, and agreements the company
has entered into.

**What belongs here:** Contract counterparties, contract value, contract
date and duration, order book status, significant one-off deals.

**Why it exists:** Orders and contracts are leading indicators of future
business performance and are often the basis for market-moving news.

**Mandatory or Optional:** Optional.

## Shareholding

**Purpose:** Record who owns the company.

**What belongs here:** Promoter/founder holding percentage, institutional
ownership, public float, major shareholders, recent changes in
shareholding pattern, pledge information.

**Why it exists:** Ownership structure affects governance, control, and
investor sentiment, and is commonly requested alongside financial data.

**Mandatory or Optional:** Optional.

## Management

**Purpose:** Identify who runs the company.

**What belongs here:** Board of directors, key executives, their roles,
tenure, and relevant background, recent leadership changes.

**Why it exists:** Leadership quality and stability are recurring factors
in company analysis and are frequently referenced in research narratives.

**Mandatory or Optional:** Optional.

## Competitors

**Purpose:** Place the company within its competitive landscape.

**What belongs here:** Named direct competitors, relative market position,
comparative strengths and weaknesses, competitive advantages or moats.

**Why it exists:** A company's facts are more meaningful in relation to its
peers; this section enables comparative analysis.

**Mandatory or Optional:** Optional.

## Risks

**Purpose:** Capture verified risk factors facing the company.

**What belongs here:** Business risks, financial risks, regulatory risks,
litigation, operational risks, and their sources.

**Why it exists:** Balanced research requires documenting downside factors,
not only positive developments; this section prevents one-sided records.

**Mandatory or Optional:** Optional.

## Market News

**Purpose:** Hold time-bound, verified news events relevant to the company.

**What belongs here:** Dated news items, event summaries, and the verified
facts extracted from them (announcements, deals, results, incidents).

**Why it exists:** Research must stay current; this section separates
perishable, event-driven facts from the company's more stable attributes.

**Mandatory or Optional:** Optional.

## Sector Information

**Purpose:** Describe the broader sector or industry the company operates
in, independent of the company itself.

**What belongs here:** Sector size, growth trends, sector-wide dynamics,
regulatory environment specific to the sector, comparative sector
benchmarks.

**Why it exists:** Company-level facts are easier to interpret against
sector-level context, and this context is often shared across many
companies in the same knowledge database.

**Mandatory or Optional:** Optional.

## Government Policies

**Purpose:** Track policies, regulations, and government actions relevant
to the company or its sector.

**What belongs here:** Relevant laws, regulatory changes, subsidies, duties
or tariffs, policy announcements, and their effective dates.

**Why it exists:** Policy shifts can materially affect a company's
prospects and are a distinct category of fact from company-reported news.

**Mandatory or Optional:** Optional.

## Sources

**Purpose:** Record where every fact came from.

**What belongs here:** Source name, source URL or reference, source type
(filing, news outlet, official statement, etc.), retrieval date, and a
link back to the specific fact(s) each source supports.

**Why it exists:** This is what makes the database "verified" rather than
merely "collected." No fact is trustworthy without a traceable source, and
this section is what the Fact Validation Layer depends on.

**Mandatory or Optional:** Mandatory. Every verified fact in every other
section must be attributable to at least one entry in this section.

## Metadata

**Purpose:** Describe the knowledge record itself, not the company.

**What belongs here:** Record creation date, last verified date, last
updated date, verification status, version/revision markers, completeness
indicators per section.

**Why it exists:** The system needs to know how fresh and how complete a
company's knowledge record is, independent of the content of that record.

**Mandatory or Optional:** Mandatory.

--------------------------------------------------

## Section Summary

| Section              | Mandatory or Optional |
|-----------------------|------------------------|
| Company Information   | Mandatory              |
| Business Overview     | Mandatory              |
| Products & Services   | Optional               |
| Financial Information | Optional (strict verification when present) |
| Orders & Contracts    | Optional               |
| Shareholding          | Optional               |
| Management            | Optional               |
| Competitors           | Optional               |
| Risks                 | Optional               |
| Market News           | Optional               |
| Sector Information    | Optional               |
| Government Policies   | Optional               |
| Sources               | Mandatory              |
| Metadata              | Mandatory              |

--------------------------------------------------

## Notes

- This document defines the logical knowledge model only. It does not
  define database schema, table structure, or storage format — see
  `DATABASE.md` for storage responsibilities.
- New sections may be added in future phases as research scope expands.
  Any new section must follow the same structure: Purpose, What data
  belongs there, Why it exists, Mandatory or Optional.
