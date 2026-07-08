# Database Architecture

This document defines the architecture of the Verified Knowledge Database.
It describes layers, entities, relationships, and scalability
considerations only — no schema, no SQL, no ER diagrams, no implementation.

`KNOWLEDGE_MODEL.md` is the source of truth for the qualitative knowledge
sections in this system (Layers 1 through 5 below), and every entity in
those layers maps directly onto a section defined there. Layer 6 is a
directed extension covering quantitative market and technical data —
Market Data, Historical Price (OHLC), Technical Analysis, and Corporate
Actions — which does not yet have corresponding sections in
`KNOWLEDGE_MODEL.md`. It follows the same layering and relationship rules
as every other layer so the model remains internally consistent.

--------------------------------------------------

## 1. Database Layers

The Verified Knowledge Database is organized into six layers. Layers group
entities by how central, how stable, and how shared across companies their
data is — not by table structure.

### Layer 1 — Identity

The anchor layer. Holds the single entity that every other layer attaches
to: the identity and description of the company itself.

Maps to: Company Information, Business Overview.

### Layer 2 — Company Knowledge

Holds knowledge that belongs to one company and describes what it does,
what it offers, and who runs and owns it.

Maps to: Products & Services, Management, Shareholding.

### Layer 3 — Financial & Contractual Knowledge

Holds knowledge with financial weight: figures, deals, and obligations.
Kept distinct from Layer 2 because it carries stricter verification
requirements and a stronger emphasis on reporting period and time.

Maps to: Financial Information, Orders & Contracts.

### Layer 4 — Market & Context Knowledge

Holds knowledge that situates a company against the outside world: peers,
sector, policy environment, ongoing risks, and news. Much of this layer's
data is shared across many companies rather than owned by a single one.

Maps to: Competitors, Risks, Market News, Sector Information, Government
Policies.

### Layer 5 — Verification & Metadata

Holds the knowledge that makes every other layer trustworthy and
trackable: where facts came from, and how fresh and complete each record
is. This layer is cross-cutting — every entity in every other layer
depends on it, rather than depending on any single layer above.

Maps to: Sources, Metadata.

### Layer 6 — Market & Technical Data

Holds quantitative trading data and the technical indicators derived from
it. Kept distinct from Layer 4 because it is numeric, price-driven, and
sourced from market data feeds rather than research and reporting — its
verification, refresh cadence, and volume characteristics are different in
kind from qualitative market context.

Maps to: Market Data, Historical Price (OHLC), Technical Analysis,
Corporate Actions.

--------------------------------------------------

## 2. Entities

Each entity below corresponds to one or more sections in
`KNOWLEDGE_MODEL.md`. An entity is a logical grouping of facts, not a
table — how it is eventually stored is an implementation concern outside
this document's scope.

### Company

**Layer:** 1 — Identity.

**What belongs inside:** Legal and common name, registration details,
incorporation country, headquarters, founding date, website, exchange and
ticker listings, business description, mission, industry/sector
classification, business model summary, geographic footprint, and customer
segments.

**Role:** The root entity. Every other entity exists in relation to a
Company (directly or, for shared entities such as Sector, indirectly).

### Products & Services

**Layer:** 2 — Company Knowledge.

**What belongs inside:** Individual product lines and service offerings,
associated brand names, the revenue segment each offering maps to, and its
target market.

### Management

**Layer:** 2 — Company Knowledge.

**What belongs inside:** Individual board members and executives, their
roles, tenure, background, and dated leadership changes.

### Shareholding

**Layer:** 2 — Company Knowledge.

**What belongs inside:** Individual ownership records — promoter/founder
holding, institutional ownership, public float, named major shareholders,
pledge information, each tied to the date the holding pattern was
observed.

### Financial Information

**Layer:** 3 — Financial & Contractual Knowledge.

**What belongs inside:** Individual verified financial figures — revenue,
profit, margins, balance sheet items, cash flow items, ratios — each tied
to a reporting period and currency.

### Orders & Contracts

**Layer:** 3 — Financial & Contractual Knowledge.

**What belongs inside:** Individual order or contract records —
counterparty, value, date, duration, and status.

### Competitors

**Layer:** 4 — Market & Context Knowledge.

**What belongs inside:** Individual comparison records, each naming a
competitor, the basis of comparison, relative market position, and
comparative strengths or weaknesses. A comparison record references a
company being described and the competing company being compared against.

### Risks

**Layer:** 4 — Market & Context Knowledge.

**What belongs inside:** Individual risk factors — business, financial,
regulatory, litigation, operational — each stated distinctly rather than
as a bundled narrative.

### Market News

**Layer:** 4 — Market & Context Knowledge.

**What belongs inside:** Individual dated news items, an event summary,
and the verified facts extracted from that event.

### Sector

**Layer:** 4 — Market & Context Knowledge.

**What belongs inside:** Sector name, sector size, growth trends,
sector-wide dynamics, and comparative benchmarks. This entity is shared —
it is described once and referenced by every Company that belongs to it,
rather than duplicated per company.

### Government Policies

**Layer:** 4 — Market & Context Knowledge.

**What belongs inside:** Individual policy or regulatory records — the
law or action, its effective date, and whether it targets a sector broadly
or a specific company.

### Sources

**Layer:** 5 — Verification & Metadata.

**What belongs inside:** Source name, URL or reference, source type
(filing, news outlet, official statement, etc.), and retrieval date. Every
Source record exists to support one or more facts recorded in any other
entity.

### Metadata

**Layer:** 5 — Verification & Metadata.

**What belongs inside:** Creation date, last verified date, last updated
date, verification status, revision markers, and per-section completeness
indicators for a Company's knowledge record.

### Market Data

**Layer:** 6 — Market & Technical Data.

**What belongs inside:** Point-in-time market snapshots for a Company —
current price, day range, 52-week range, traded volume, market
capitalization, and the timestamp the snapshot was taken.

### Historical Price (OHLC)

**Layer:** 6 — Market & Technical Data.

**What belongs inside:** One record per trading period per Company — open,
high, low, close, volume, and the date (or interval) the record covers.
This entity is the time-series backbone that Technical Analysis is
computed from.

### Technical Analysis

**Layer:** 6 — Market & Technical Data.

**What belongs inside:** Individual computed indicator records — moving
averages, RSI, MACD, trend signals, support/resistance levels — each tied
to the Company, the date it was computed for, and the Historical Price
(OHLC) window it was derived from.

### Corporate Actions

**Layer:** 6 — Market & Technical Data.

**What belongs inside:** Individual corporate action records — dividends,
stock splits, bonus issues, buybacks, mergers — each with an action type,
announcement date, effective date, and terms. Corporate Actions are
recorded here because they are the events that require adjustments to
Historical Price and Market Data, not because they are themselves price
data.

--------------------------------------------------

## 3. Relationships Between Entities

Only three relationship kinds are used, applied consistently across the
whole model.

**Company → Metadata: One-to-One.**
Each Company has exactly one Metadata record describing the freshness and
completeness of its knowledge. A Metadata record describes exactly one
Company.

**Company → Products & Services, Management, Shareholding, Financial
Information, Orders & Contracts, Risks, Market News: One-to-Many.**
A single Company can have many records in each of these entities (many
products, many executives, many financial periods, many risks, many news
items). Each such record belongs to exactly one Company, which from that
record's side is a **Many-to-One** relationship back to Company.

**Company → Sector: Many-to-One.**
Many Companies belong to a single Sector. From the Sector's side, this is
a One-to-Many relationship (one Sector has many Companies). Sector is
recorded once and referenced by every Company it applies to, rather than
duplicated.

**Sector → Government Policies: One-to-Many.**
A Sector can have many associated policy records. Where a policy targets
one Company directly rather than a whole sector, the same relationship
applies at the Company level instead: **Company → Government Policies:
One-to-Many**, with each policy record belonging to exactly one Company
(Many-to-One back to Company).

**Company → Competitors: One-to-Many, with a Many-to-One reference back to
Company for the competitor being named.**
Each comparison record belongs to exactly one Company (the subject) and
separately references exactly one other Company (the competitor). Both
sides of that reference are Many-to-One relationships onto the Company
entity; no direct many-to-many construct is used.

**Any entity record → Sources: One-to-Many.**
Any single fact-bearing record, in any entity, can be backed by many
Source records. Each Source record supports one originating fact record,
a Many-to-One relationship back to whichever entity it verifies. A source
that legitimately supports multiple independent facts is recorded once per
supported fact rather than as a shared reference, keeping every
verification link traceable to exactly one fact.

**Company → Market Data, Historical Price (OHLC), Corporate Actions:
One-to-Many.**
A single Company can have many market data snapshots, many OHLC records
(one per trading period), and many corporate action records over its
history. Each such record belongs to exactly one Company — a Many-to-One
relationship back to Company, following the same pattern as Layer 2 and
Layer 3 entities.

**Historical Price (OHLC) → Technical Analysis: One-to-Many.**
A given span of Historical Price records can back many computed Technical
Analysis records (different indicators, different lookback windows, all
computed from the same underlying prices). Each Technical Analysis record
is derived from exactly one Historical Price window, a Many-to-One
relationship back to Historical Price (OHLC); it also carries a
Many-to-One reference back to Company directly, consistent with every
other entity in this document.

**Corporate Actions → Historical Price (OHLC): One-to-Many (adjustment
relationship).**
A single Corporate Action (for example, a stock split) can require
adjustment of many prior Historical Price records. This does not change
the ownership relationship of those records to their Company — it is a
secondary reference used to explain why a historical figure was restated,
not a replacement for the Company → Historical Price relationship above.

--------------------------------------------------

## 4. What Belongs Inside Each Entity

Covered above under each entity's "What belongs inside" description in
Section 2. As a general rule across all entities:

- Only verified facts belong inside an entity. Unverified or unconfirmed
  data does not enter the Verified Knowledge Database at all.
- Every fact-bearing entity record must be traceable to at least one
  Sources record, per the mandatory status of Sources in
  `KNOWLEDGE_MODEL.md`.
- Time-sensitive entities (Financial Information, Shareholding, Market
  News, Government Policies, Market Data, Historical Price (OHLC),
  Technical Analysis, Corporate Actions) always carry the date or period
  the fact applies to, so that history is preserved rather than
  overwritten.
- Shared entities (Sector) hold only information that is true regardless
  of which company is looking at it; company-specific commentary about a
  sector belongs in that Company's own knowledge, not in the Sector
  entity.
- Derived entities (Technical Analysis) never store facts that could
  instead be recomputed from an underlying entity (Historical Price);
  they store the computed result plus a reference to what it was computed
  from, so the source data remains the single point of truth.

--------------------------------------------------

## 5. Future Scalability

The layered, entity-based structure is designed so that growth is additive
— new data extends the model without altering what already exists.

**New exchanges and new countries.** Exchange and country are attributes
of the Company entity, not structural elements of the database. Adding a
company on a new exchange or in a new country requires only a new Company
record (and, if useful later, a new lookup value) — no change to Layer 1
or to any relationship.

**New sectors.** Sector is already its own shared entity, decoupled from
Company. A new sector is simply a new Sector record that new or existing
Companies can reference via the existing Many-to-One relationship. No
existing Company or Sector record needs to change.

**New indicators.** The Technical Analysis entity already stores each
computed indicator as an individual record rather than as a fixed set of
fields. A new indicator (a new moving average variant, a new oscillator,
etc.) is simply a new Technical Analysis record type referencing the same
Historical Price (OHLC) data — no change to Layer 6's structure or to any
other layer.

**New categories of fact in general.** Because each knowledge category is
its own entity attached to Company through one of the established
relationship kinds, a new category becomes a new entity in the
appropriate layer (Layer 6 for further market/technical data, Layer 3 or 4
for further qualitative knowledge) rather than a modification of an
existing entity. Existing entities, and the facts already stored in them,
are unaffected. Layer 6 itself is an example of this principle already
applied once.

**New languages.** Language is a property of the content within an entity
(for example, a Source's original language, or a translated field on a
News or Policy record), not a structural feature. Supporting a new
language means recording that attribute on new or existing records; it
does not require restructuring any entity or relationship.

**General principle.** Every extension path above adds a new record, a new
attribute value, or — at most — a new entity following the existing
relationship rules. None of them require redefining Layer 1 (Identity) or
Layer 5 (Verification & Metadata), which is what keeps the rest of the
database stable as the system grows.
