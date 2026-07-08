# Database Relationships & Keys

This document finalizes the logical relationships of the Verified
Knowledge Database. It is design only — no schema, no SQL, no CRUD, no
implementation. Its source of truth is `KNOWLEDGE_MODEL.md` (what
knowledge exists) and `DATABASE_ARCHITECTURE.md` (the layers and entities
built from that knowledge).

--------------------------------------------------

## 1. Primary Entity

**Company** is the root entity of the database.

Every other entity either belongs directly to a Company (Products &
Services, Management, Shareholding, Financial Information, Orders &
Contracts, Risks, Market News, Market Data, Historical Price (OHLC),
Technical Analysis, Corporate Actions, Metadata) or belongs to it
indirectly through a shared entity that a Company references (Sector,
and Government Policies via Sector). Sources, the one entity that does
not belong to a Company directly, exists only to verify facts that
ultimately trace back to a Company.

Company is the root because it is the only entity every knowledge section
in `KNOWLEDGE_MODEL.md` is ultimately describing. Remove Company and no
other entity has anything left to attach to; remove any other entity and
Company still stands as a complete, identifiable record.

--------------------------------------------------

## 2. Primary Key

Every entity has exactly one primary key: a single `id` field, unique
within that entity. Other entities refer to it using the naming
convention `<entity>_id`.

| Entity | Primary Key |
|---|---|
| Company | `id` (referenced as `company_id`) |
| Sector | `id` (referenced as `sector_id`) |
| Products & Services | `id` (referenced as `product_service_id`) |
| Management | `id` (referenced as `management_id`) |
| Shareholding | `id` (referenced as `shareholding_id`) |
| Financial Information | `id` (referenced as `financial_information_id`) |
| Orders & Contracts | `id` (referenced as `order_contract_id`) |
| Competitors | `id` (referenced as `competitor_id`) |
| Risks | `id` (referenced as `risk_id`) |
| Market News | `id` (referenced as `news_id`) |
| Government Policies | `id` (referenced as `policy_id`) |
| Market Data | `id` (referenced as `market_data_id`) |
| Historical Price (OHLC) | `id` (referenced as `price_history_id`) |
| Technical Analysis | `id` (referenced as `technical_analysis_id`) |
| Corporate Actions | `id` (referenced as `corporate_action_id`) |
| Sources | `id` (referenced as `source_id`) |
| Metadata | `id` (referenced as `metadata_id`) |

No entity uses a composite key. Every entity is identifiable on its own,
even before any relationship to it is considered.

--------------------------------------------------

## 3. Relationships

Only three relationship kinds are used across the entire model:
One-to-One, One-to-Many, and Many-to-One. No Many-to-Many relationship is
used anywhere — the one case that could naturally be modeled as
Many-to-Many (a company having many competitors, each of which is itself
a company) is instead modeled as two Many-to-One references, explained
below.

**Company ↔ Metadata — One-to-One.**
Each Company has exactly one Metadata record, and each Metadata record
describes exactly one Company. This is the only One-to-One relationship
in the model, because Metadata is a 1:1 summary of a single record's
freshness and completeness — there is never a reason for a Company to
have more than one.

**Sector → Company — One-to-Many** (equivalently, **Company → Sector —
Many-to-One**).
One Sector is referenced by many Companies. Sector is described once and
shared, so it sits on the "one" side; every Company that belongs to it
sits on the "many" side.

**Company → {Products & Services, Management, Shareholding, Financial
Information, Orders & Contracts, Risks, Market News, Market Data,
Historical Price (OHLC), Corporate Actions} — One-to-Many** (equivalently,
each of those entities → Company — Many-to-One).
A Company can have many records in each of these entities (many products,
many executives, many financial periods, many risks, many news items,
many price bars, many corporate actions). Each individual record in these
entities belongs to exactly one Company.

**Sector → Government Policies — One-to-Many**, with **Company →
Government Policies — One-to-Many** used instead when a policy targets one
Company directly rather than an entire sector.
A policy record carries exactly one of the two references, never both,
depending on whether it is sector-wide or company-specific.

**Company → Competitors — One-to-Many, with a second Many-to-One reference
from Competitors back to Company for the named competitor.**
Each Competitors record belongs to exactly one subject Company and
separately names exactly one competitor Company. Modeling it as two
Many-to-One references (subject and competitor) rather than a direct
Many-to-Many between companies keeps every relationship in the model to
the three permitted kinds, and keeps each comparison individually
traceable and attributable.

**Historical Price (OHLC) → Technical Analysis — One-to-Many.**
A span of Historical Price records can back many Technical Analysis
records (different indicators, different lookback windows, computed from
the same price window). Each Technical Analysis record is derived from
exactly one Historical Price reference window.

**Corporate Actions → Historical Price (OHLC) — One-to-Many (adjustment
reference).**
A single Corporate Action (e.g. a stock split) can necessitate adjustment
of many prior Historical Price records. This is a secondary explanatory
reference, not a replacement for the primary Company → Historical Price
(OHLC) ownership relationship — an adjusted price record still belongs to
its Company first and foremost.

**Any fact-bearing entity record → Sources — One-to-Many.**
Any single record, in any entity, can be backed by many Source records.
Each Source record supports exactly one originating fact record. A source
document that legitimately supports multiple independent facts is
recorded once per fact it supports, so every verification link remains
traceable to exactly one fact rather than shared ambiguously across many.

--------------------------------------------------

## 4. Reference Fields

Reference fields follow the `<entity>_id` naming convention established
in Section 2. This is the complete list of reference fields required by
the relationships in Section 3.

| Entity | Reference Field(s) | Points To |
|---|---|---|
| Company | `sector_id` | Sector |
| Products & Services | `company_id` | Company |
| Management | `company_id` | Company |
| Shareholding | `company_id` | Company |
| Financial Information | `company_id` | Company |
| Orders & Contracts | `company_id` | Company |
| Competitors | `company_id`, `competitor_company_id` | Company (subject), Company (competitor) |
| Risks | `company_id` | Company |
| Market News | `company_id` | Company |
| Government Policies | `sector_id` (when sector-wide), `company_id` (when company-specific) | Sector, Company |
| Market Data | `company_id` | Company |
| Historical Price (OHLC) | `company_id` | Company |
| Technical Analysis | `company_id`, `price_history_id` | Company, Historical Price (OHLC) |
| Corporate Actions | `company_id` | Company |
| Sources | `entity_name`, `record_id` | Whichever entity/record the source verifies |
| Metadata | `company_id` | Company |
| Sector | *(none — Sector has no outgoing reference field)* | — |

`Sources` is the one entity whose reference is generic rather than fixed:
`entity_name` names which entity the fact belongs to, and `record_id`
holds that entity's primary key value, so any current or future entity
can be verified without adding a new reference field to Sources itself.

--------------------------------------------------

## 5. Unique Constraints

- **Company.legal_name** — must be unique; no two Company records may
  share the same registered legal name.
- **Company (stock exchange, ticker symbol) pair** — must be unique; the
  same ticker on the same exchange can only identify one Company.
- **Sector.name** — must be unique; a sector is described once and shared,
  so duplicate sector names would fragment that shared context.
- **Metadata.company_id** — must be unique, enforcing the One-to-One
  relationship between Company and Metadata (no Company may have more
  than one Metadata record).
- **Company ISIN** (International Securities Identification Number) — not
  currently a modeled field, but recommended as a unique constraint if
  and when it is added, since it is the standard globally unique
  identifier for a listed security.

--------------------------------------------------

## 6. Recommended Indexes

Indexes recommended for fields that will be searched or filtered on
frequently:

- Company: `legal_name`, `common_name`, ticker symbols, `incorporation_country`, `industry`
- Sector: `name`
- Market News: `event_date`
- Government Policies: `effective_date`
- Financial Information: `reporting_period`
- Shareholding: `observed_date`
- Historical Price (OHLC): `period_date`
- Market Data: `snapshot_timestamp`
- Technical Analysis: `computed_date`
- Corporate Actions: `effective_date`
- Every child entity's `company_id` — the single most frequent lookup in
  this model is "every record for this Company," so every entity that
  carries a `company_id` reference field should have it indexed.

--------------------------------------------------

## 7. Entity Dependency Order

The order below reflects logical creation dependency: an entity cannot be
meaningfully created until every entity it references already exists.

```
Sector
   ↓
Company
   ↓
Products & Services, Management, Shareholding
   ↓
Financial Information
   ↓
Orders & Contracts
   ↓
Competitors
   ↓
Risks
   ↓
Market News
   ↓
Government Policies
   ↓
Market Data
   ↓
Historical Price (OHLC)
   ↓
Technical Analysis
   ↓
Corporate Actions
   ↓
Sources
   ↓
Metadata
```

Sector comes first because it has no outgoing reference field and nothing
else in the model depends on referencing anything above it. Company comes
second because every other entity either references it directly or
references something (Sector, Government Policies) that only matters in
relation to it. Sources comes second-to-last because it can reference a
record in any other entity and therefore has the widest set of
dependencies. Metadata comes last because it summarizes the completeness
of a Company's record as a whole, which is only meaningful once the rest
of that record exists.

--------------------------------------------------

## 8. Future Scalability

The relationship model is additive by design: every relationship in this
document is built from the same three kinds (One-to-One, One-to-Many,
Many-to-One) and the same reference-field convention (`<entity>_id`). A
new entity extends the model without breaking any existing relationship
because:

- It attaches to Company (or to Sector, if it is a shared entity like
  Sector) through a new `company_id` (or `sector_id`) field, following
  the same Many-to-One pattern every existing entity already uses. No
  existing entity's fields or relationships need to change.
- It automatically gains verification and freshness tracking for free,
  because Sources references records generically via `entity_name` +
  `record_id`, and Metadata already summarizes completeness per section
  rather than per fixed entity list.
- It does not require a Many-to-Many relationship to be introduced,
  because the one case that could have required one (Competitors) was
  already solved with two Many-to-One references — the same technique
  applies to any future case that looks like a many-to-many at first
  glance.
- It does not change the Entity Dependency Order for anything that
  already exists — a new entity simply inserts itself at the point in
  the order where its own dependencies are satisfied, typically
  immediately after Company or after whichever entity it derives from
  (as Technical Analysis does from Historical Price (OHLC)).
