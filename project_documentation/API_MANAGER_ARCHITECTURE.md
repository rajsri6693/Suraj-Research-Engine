# API Manager Architecture

This document defines the API Provider Management architecture for the
Research Engine — the single gateway through which every Research
Collector accesses external APIs. It describes responsibility, selection
logic, failover logic, health tracking, dashboard requirements, and
database design only. No Python, no SQL, no implementation.

--------------------------------------------------

## 1. Purpose

Today, per `RESEARCH_COLLECTORS.md`, every collector returns placeholder
data and never calls an API directly. This document defines the
architecture collectors will call into once live collection is built: the
**API Manager** — one gateway that owns provider selection, failover, key
resolution, health tracking, and logging for every external API call in
the Research Engine.

No Research Collector will ever call Financial Modeling Prep, Finnhub,
Alpha Vantage, Twelve Data, or NewsAPI directly. Every collector calls the
API Manager; the API Manager decides which provider answers the call.
This mirrors the existing separation of concerns in the Research Engine —
a collector gathers one Knowledge Section and nothing about *how* the
data is fetched, exactly as `RESEARCH_COLLECTORS.md` already scopes a
collector to gathering, never to source implementation details, per
`COLLECTOR_SOURCE_STRATEGY.md`.

This document does NOT redesign any existing Collector, the Research
Workflow, the Research Planner, or any other existing Research Engine
architecture. It defines a new layer that existing collectors will sit in
front of, unchanged in their own responsibilities. The provider list,
category mapping, architecture rules, failover rules, and dashboard
requirements below are final and are documented as given, not redesigned.

--------------------------------------------------

## 2. Total APIs

Exactly five external providers exist in this architecture:

- Financial Modeling Prep (FMP)
- Finnhub
- Alpha Vantage
- Twelve Data
- NewsAPI

There are five API keys, one .env file, and five Provider Interface
adapters — never more. **Finnhub is a single provider with a single key**
that serves two roles across two categories (Section 3): Backup for
Fundamental Data, and Backup for News, using its news endpoint. "Finnhub
News" is not a sixth provider or a second key — it is Finnhub's role
label within the News category, resolved through the same Finnhub adapter
and the same `FINNHUB_API_KEY`. This is the only provider that carries
more than one Category role; every other provider has exactly one.

--------------------------------------------------

## 3. API Categories

The API Manager organizes every request into exactly three categories.
Each category has one Primary Provider and one Backup Provider — never
more, never fewer.

| Category | Primary | Backup | Provides |
|---|---|---|---|
| Category 1 — Fundamental Data | FMP | Finnhub | Company Profile, Financial Statements, Ratios, Earnings, Dividend, Stock Split, Management, Shareholding, Competitors, Products & Services, Corporate Actions, Orders & Contracts |
| Category 2 — Market & Technical | Alpha Vantage | Twelve Data | Real-time Price, Historical OHLC, Intraday, Technical Indicators, Chart Dataset |
| Category 3 — News | NewsAPI | Finnhub (News role) | Company News, Market News, Sector News, Breaking News |

A category is the unit the API Manager reasons about — a Collector (or,
in a future live-collection phase, a Collector's data-fetch step) asks
the API Manager for a category and an operation, never for a named
provider. Which named provider actually answers is entirely the API
Manager's decision, per Section 6.

--------------------------------------------------

## 4. Architecture Diagram

```
Research Collector (RESEARCH_COLLECTORS.md)
   - Company, Financial, Historical Price, Technical Analysis,
     Market News, Management, Shareholding, Competitors,
     Products & Services, Corporate Actions, etc.
        │
        │  request(Category, Operation, Parameters)
        ▼
┌──────────────────────────────────────────────────────────┐
│                        API Manager                        │
│  Single gateway. Every Collector calls only this layer.   │
│                                                            │
│   ┌───────────────┐   ┌───────────────┐   ┌─────────────┐│
│   │  API Registry  │   │  API Settings  │   │  API Health ││
│   │  category →    │   │  timeouts,     │   │  ONLINE /   ││
│   │  primary/backup│   │  retry counts, │   │  DOWN /     ││
│   │  provider map  │   │  env var names │   │  RATE_LTD / ││
│   │                │   │                │   │  ...        ││
│   └───────────────┘   └───────────────┘   └─────────────┘│
│              │                 │                 │        │
│              └────────────┬────┴─────────────────┘        │
│                            ▼                               │
│                 Provider Selection Logic (Section 6)       │
│                            │                                │
│                            ▼                                │
│                    API Logging (every attempt)              │
└──────────────────────────┬──────────────────────────────┘
                            │  calls through
                            ▼
                   Provider Interface (Section 5.8)
     ┌──────────────┬──────────────┬──────────────┬──────────────┐
     ▼              ▼              ▼              ▼              │
  FMP Adapter   Finnhub Adapter  Alpha Vantage  Twelve Data       │
  (Cat.1        (Cat.1 Backup +  Adapter        Adapter           │
   Primary)      Cat.3 Backup,   (Cat.2         (Cat.2 Backup)    │
                 same key,       Primary)                          │
                 two roles)                                        │
                                                                     ▼
                                                            NewsAPI Adapter
                                                            (Cat.3 Primary)
                            │
                            ▼
      External Provider APIs (FMP, Finnhub, Alpha Vantage,
      Twelve Data, NewsAPI) — keys resolved from the single
      .env file only, never hardcoded (Section 7).
```

The API Manager is a single logical layer sitting strictly between every
Research Collector and every external provider. A Collector never sees a
provider name, a provider's request format, or a provider's API key — it
only sees Category, Operation, Parameters going in, and normalized data
(or an explicit failure) coming back.

--------------------------------------------------

## 5. Class Responsibilities

### 5.1 API Manager

The single gateway and orchestrator. Owns the end-to-end handling of one
request from a Collector:

- Accepts a request identifying a Category and an Operation (for example,
  Fundamental Data / Company Profile).
- Consults the API Registry to find the current Primary and Backup
  Provider for that Category.
- Consults API Health to check whether the Primary Provider is usable
  before calling it.
- Delegates the actual call to the Provider Interface implementation for
  whichever provider it selects.
- Applies the Failover Rules (Section 7) when the Primary Provider fails.
- Records every attempt through API Logging and updates API Health with
  the outcome, including which provider actually served the request.
- Returns normalized data, or an explicit failure, to the calling
  Collector. It never fabricates data when every provider in a Category
  fails — an explicit failure is returned, consistent with the Failure
  Handling rule already established in `RESEARCH_WORKFLOW.md` and
  `COLLECTOR_SOURCE_STRATEGY.md`'s Missing Source Rules.

The API Manager never implements a provider's specific request or
response format itself — that belongs to the Provider Interface
implementation for that provider (Section 5.8).

### 5.2 API Registry

The configuration record of *who* currently answers for each Category.

- Holds the Category → Primary Provider → Backup Provider mapping defined
  in Section 3.
- Is the one place this mapping is recorded — the API Manager consults
  the Registry rather than hardcoding which provider is primary anywhere
  in its own logic.
- Holds Finnhub's two Category roles (Category 1 Backup, Category 3
  Backup) as two distinct mapping entries, both resolving to the same
  underlying Finnhub key and adapter (Section 2).
- Is what a Future Dashboard edits to change provider selection (Section
  9) — editing the Registry's mapping changes behavior with no code
  change, satisfying the "configurable provider selection" rule.

### 5.3 API Provider

The logical representation of one Category role — for example, "FMP as
Primary for Fundamental Data" or "Finnhub as Backup for News."

- Identity: provider name and the Category this row applies to.
- Role: Primary or Backup, per this Category. Because Finnhub holds two
  roles across two categories, Finnhub is represented by two API Provider
  rows, not one — each row scoped to exactly one Category, so role is
  never ambiguous.
- Key Reference: the name of the .env variable holding this provider's
  API key — never the key value itself (Section 7). Both of Finnhub's
  rows reference the same key name.
- Does not hold live status — that is API Health's responsibility, kept
  separate so identity (rarely changes) and status (changes constantly)
  are not conflated.

### 5.4 API Settings

Owns the tunable behavior that controls how the API Manager operates,
distinct from provider identity:

- Timeout threshold per call.
- Retry count before a provider is considered failed for this attempt.
- Rate-limit thresholds and cool-down duration before a RATE_LIMITED
  provider is retried.
- The env var name mapping used to resolve each provider's key (working
  together with API Provider's Key Reference), all sourced from the one
  .env file (Section 7).
- Whether provider selection changes take effect immediately or require a
  restart — a Settings-level toggle, so this behavior itself is
  configurable rather than fixed.

Settings answer "how should a call behave"; the Registry answers "which
provider should be called." Keeping them separate lets a Future Dashboard
change either independently.

### 5.5 API Health

The live operating status of every API Provider row, tracked
continuously:

- Holds the current Health status (Section 8) for each API Provider row
  (so Finnhub-as-Fundamental-Backup and Finnhub-as-News-Backup can carry
  independent status, since a Finnhub outage affecting one endpoint does
  not necessarily affect the other).
- Is updated after every call attempt the API Manager makes through a
  Provider Interface — never asserted independently of an actual call.
- Also carries: Last Health Check timestamp and Response Time for the
  most recent attempt, both required by Dashboard Requirements (Section
  9).
- Is what Provider Selection Logic (Section 6) checks before choosing a
  provider, and what Failover Rules (Section 7) update the moment a
  Primary Provider fails.
- Is a live signal, not a log — API Health always reflects only the most
  recent known status per API Provider row. History of every attempt
  belongs to API Logging, not API Health.

### 5.6 API Logging

The historical record of every call attempt the API Manager makes:

- One entry per attempt: which Collector/Category triggered it, which
  Provider role was attempted, the outcome, response time, and which
  provider actually served the request (Primary or Backup) — the fifth
  Failover Rule (Section 7) requires this be logged explicitly.
- Never summarized or overwritten — each attempt is its own entry, so a
  Future Dashboard or an operator can reconstruct exactly what happened
  and when, including every failover, every Usage Count, and every
  Success Rate (Section 9).
- Feeds the `api_logs` table defined in Section 10.

### 5.7 API Status

The aggregated, read-only view combining API Provider, API Health, and
API Registry for a Category — what gets displayed, not a separate store
of new data.

- Answers "for Fundamental Data, who is Primary, who is Backup, which one
  actually served the last request, and what is each one's current
  Health status" in a single lookup.
- Computes derived values the Dashboard needs — API Usage Count and
  Success Rate — from `api_logs`, rather than storing them redundantly
  (Section 9, Section 10).
- Is what a Future Dashboard reads to render a status board (Section 9).
  API Status computes this view from the other components; it does not
  duplicate their data.

### 5.8 Provider Interface

The contract every concrete provider adapter (FMP adapter, Finnhub
adapter, Alpha Vantage adapter, Twelve Data adapter, NewsAPI adapter)
must satisfy, so the API Manager can call any provider uniformly:

- Accepts an Operation and Parameters (for example, Operation: Company
  Profile, Parameters: ticker symbol).
- Returns normalized data in a category-consistent shape, or raises a
  typed failure the API Manager can map onto a Health status (Section 8).
- Hides every vendor-specific detail — authentication scheme, endpoint
  paths, request/response format, pagination — behind this single
  contract, so the API Manager's selection and failover logic never
  changes when a provider's own API changes shape. Only that provider's
  own adapter changes.
- Is a one-adapter-per-provider contract, not one-per-Category-role: the
  single Finnhub adapter is invoked whether the API Manager is filling
  Finnhub's Fundamental-Backup role or its News-Backup role — the
  Operation passed in is what differs, not the adapter.
- Is what makes Future API Expansion (Section 11) additive: a new
  provider is a new adapter satisfying this same contract, not a change
  to the API Manager.

--------------------------------------------------

## 6. Provider Selection Logic

For every request, the API Manager selects a provider in a fixed order:

```
Request arrives: Category + Operation + Parameters
        ↓
Look up Category in API Registry → Primary Provider, Backup Provider
        ↓
Check API Health for the Primary Provider's row
        ↓
   ┌─────────────────────┬─────────────────────────────┐
   │ Primary is ONLINE    │ Primary is DOWN /            │
   │ (or UNKNOWN — not    │ RATE_LIMITED / INVALID_KEY / │
   │ yet checked)          │ TIMEOUT                      │
   ▼                       ▼                              │
Call Primary Provider   Skip Primary, go directly to      │
via its Provider         Backup Provider (Section 7)      │
Interface                                                  │
   │                       │                              │
   └───────────┬───────────┘                              │
               ▼                                           │
     Log the attempt (API Logging) and update              │
     API Health with the outcome and Response Time         │
               │                                           │
               ▼                                           │
     Return normalized data to the Collector,               │
     or — if both Primary and Backup have been tried and    │
     failed — return an explicit failure                    │
     (never fabricated data)                                │
```

Selection rules:

- The Primary Provider is always attempted first, unless API Health
  already marks it unusable (DOWN, RATE_LIMITED, or INVALID_KEY) from a
  prior attempt within its cool-down window (Section 8).
- The Backup Provider is only attempted after the Primary Provider has
  actually failed this request, or was already known unusable — the
  Backup is never called speculatively alongside the Primary.
- If both Primary and Backup fail, the API Manager returns an explicit
  failure for that request. It never falls back to a provider outside
  the Category's defined Registry mapping (there are only two candidates
  per Category — see Section 3), and never substitutes placeholder data.
- Which provider is Primary and which is Backup for a Category is read
  from the API Registry at request time, not fixed in the API Manager's
  own code — this is what makes provider selection configurable, and
  what a Future Dashboard's Manual Provider Switch changes (Section 9).

--------------------------------------------------

## 7. Failover Rules

If the Primary Provider fails, the API Manager performs exactly these
five steps, in order:

```
1. Record the failure          → written to API Logging (api_logs)
        ↓
2. Mark the provider DOWN      → written to API Health (api_health)
        ↓
3. Call the Backup Provider    → via that provider's Provider Interface
        ↓
4. Return the Backup response  → normalized data handed back to
                                  the Collector exactly as Primary's
                                  response would have been
        ↓
5. Log which provider actually served the request
                                → api_logs records "served by: Backup"
                                  (or "served by: Primary" on the
                                  non-failover path), so every request's
                                  actual origin is always traceable
```

Failover is entirely internal to the API Manager. A Collector that calls
the API Manager for Fundamental Data / Company Profile receives either
data or an explicit failure — it never knows or needs to know whether
that data came from FMP or from Finnhub, and it requires no code change
when a failover happens. This preserves the existing Collector contract
in `RESEARCH_COLLECTORS.md`: a Collector's only concern is its own
Knowledge Section, never the mechanics of data retrieval.

If the Backup Provider also fails, that failure is recorded and marked
the same way (Steps 1–2 repeated for the Backup), and the API Manager
returns an explicit failure to the Collector — it does not search for a
third provider, since each Category defines exactly one Primary and one
Backup (Section 3). A failure returned to a Collector after both are
exhausted is handled exactly like any other missing data at the Collector
level — it becomes a Failed or Partial Collector Status, per
`RESEARCH_COLLECTORS.md` Section 5, and flows downstream as an absent
section per `RESEARCH_WORKFLOW.md`'s Failure Handling rule.

--------------------------------------------------

## 8. Health Check Logic

Every API Provider row's status is always exactly one of six values:

| Status | Meaning |
|---|---|
| ONLINE | The provider answered the most recent call successfully. |
| DOWN | The provider's most recent call failed for a reason other than rate limiting or an invalid key (connection error, server error, unexpected response). |
| RATE_LIMITED | The provider rejected the most recent call because its request quota was exceeded. |
| INVALID_KEY | The provider rejected the most recent call because the configured API key was missing, malformed, or revoked. |
| TIMEOUT | The provider did not respond within the timeout threshold defined in API Settings. |
| UNKNOWN | No call has been attempted against this provider row yet, or its last known status has expired past a freshness window — the default status before any attempt, never used to mean "assumed working." |

Health check rules:

- Status is only ever set as a direct result of an actual call attempt
  made through a Provider Interface, or an explicit manual Health Check
  (Section 9's Health Check button) — never asserted speculatively.
- Status, Last Health Check timestamp, and Response Time are tracked per
  API Provider row, not per raw provider — Finnhub's Fundamental-Backup
  role and News-Backup role can independently be ONLINE and DOWN at the
  same time, since a failure calling one Finnhub endpoint does not imply
  the other endpoint is also failing.
- A DOWN, RATE_LIMITED, or TIMEOUT status is not permanent: the API
  Manager re-attempts that provider row on a subsequent request once its
  cool-down window (an API Settings value) has elapsed, rather than
  avoiding it indefinitely. This allows a Primary Provider that recovers
  to become Primary again automatically, with no manual reset.
- INVALID_KEY is treated as longer-lived than DOWN/RATE_LIMITED/TIMEOUT —
  a bad key does not self-correct with time, so the API Manager does not
  retry an INVALID_KEY provider row on the same short cool-down; it
  remains skipped until the underlying key is corrected in the single
  `.env` file and the provider is next attempted.
- Every status transition is written to API Health (the current-state
  view) and, separately, to API Logging (the permanent record of the
  attempt that caused the transition) — the same event always updates
  both, never one without the other.

--------------------------------------------------

## 9. Dashboard Requirements

The Future Dashboard is the human-facing surface over the API Manager's
configuration and status, satisfying the rule that Primary and Backup
provider selection must be changeable "without code changes." It must
display, per Category:

| Field | Source |
|---|---|
| Primary Provider | API Registry (Section 5.2) |
| Backup Provider | API Registry (Section 5.2) |
| Current Provider in use | API Status (Section 5.7), derived from the most recent `api_logs` entry's "served by" value for this Category |
| Provider Status | API Health (Section 5.5) — one of the six values in Section 8, per API Provider row |
| Last Health Check | API Health — timestamp of the most recent call attempt or manual check |
| Response Time | API Health — response time of the most recent attempt |
| Last Error | API Health / API Logging — the failure reason (mapped to a Health status) from the most recent failed attempt, if any |
| API Usage Count | Computed from `api_logs` — count of attempts against this provider row |
| Success Rate | Computed from `api_logs` — successful attempts ÷ total attempts for this provider row |

And it must expose two actions:

- **Manual Provider Switch** — writes directly to the API Registry
  (Section 5.2), overriding which provider currently holds the Primary or
  Backup role for a Category. Takes effect on the next request, per
  Section 6's rule that Registry is read at request time — no
  deployment, no restart (unless API Settings' restart-required toggle,
  Section 5.4, is enabled).
- **Health Check button** — triggers an on-demand call through the
  selected provider's Provider Interface outside the normal Collector
  request flow, purely to refresh API Health's Status, Last Health Check,
  and Response Time for that provider row. This is the one path,
  alongside a real Collector-triggered request, allowed to update Health
  status (Section 8).

Reads and writes stay separated exactly as before: the Dashboard reads
API Status, API Health, and computed `api_logs` aggregates; its only
writes are to the API Registry (Manual Provider Switch) and to triggering
a fresh Provider Interface call (Health Check button) — it never writes
`api_health` or `api_logs` rows directly, since those only change as the
recorded outcome of an actual call.

The Dashboard's own UI, layout, and implementation are out of scope for
this document — this section only defines the fields and actions it must
expose against the API Manager's data.

--------------------------------------------------

## 10. Database Design

Three tables support the API Manager. This section describes their
responsibility and the information each row carries — no SQL, no column
types, no implementation.

### 10.1 `api_provider`

One row per Category role, mirroring API Provider (Section 5.3) and API
Registry (Section 5.2). Five providers produce **six** rows, because
Finnhub holds two roles:

- Provider name (FMP, Finnhub, Alpha Vantage, Twelve Data, NewsAPI).
- Category this row applies to (Fundamental Data, Market & Technical, or
  News).
- Role within that Category (Primary or Backup).
- Reference to the single `.env` file's variable name holding this
  provider's API key — never the key value itself. Finnhub's two rows
  share the same key reference.
- Whether this row is currently active or disabled (a Dashboard toggle
  adjacent to Manual Provider Switch, Section 9).

### 10.2 `api_health`

One row per `api_provider` row, reflecting its current, live status,
mirroring API Health (Section 5.5):

- Reference to the `api_provider` row.
- Current status — one of the six values defined in Section 8.
- Last Health Check timestamp (from a real request or a manual Health
  Check button trigger).
- Response Time of the most recent attempt.
- Last Error — the failure detail from the most recent failed attempt, if
  the current status is not ONLINE.
- Consecutive failure count since the last ONLINE status, used to judge
  cool-down and escalation.

### 10.3 `api_logs`

One row per call attempt ever made through the API Manager, mirroring API
Logging (Section 5.6):

- Timestamp of the attempt.
- Requesting Category and Operation (and, where available, which
  Collector triggered it).
- `api_provider` row attempted.
- Whether this attempt was against the Primary or Backup role, and — for
  a request that failed over — which provider ultimately served it (the
  fifth Failover Rule, Section 7).
- Outcome (success or failure) and, if failed, which of the six Health
  statuses the failure mapped to.
- Response time for the attempt.

API Usage Count and Success Rate (Section 9) are always computed by
aggregating `api_logs` rows for a given `api_provider` row — they are
never stored as separately maintained counters, so they can never drift
out of sync with the underlying attempt history.

### 10.4 Relationships

- **`api_provider` → `api_health`: One-to-One.** Each Category-role row
  has exactly one current-status row, kept as the live signal described
  in Section 5.5 — historical status changes are not accumulated here.
- **`api_provider` → `api_logs`: One-to-Many.** Each Category-role row
  accumulates one log row per attempt ever made against it, preserving
  full history even though `api_health` only reflects the latest state.
- **Category is not its own table.** Category (Fundamental Data, Market &
  Technical, News) is a fixed attribute recorded on `api_provider`, not a
  separate entity — there are exactly three categories, defined in
  Section 3, and they do not need independent rows of their own.
- **Finnhub is not duplicated as a distinct provider identity.** Its two
  `api_provider` rows both reference the same key name and the same
  Provider Interface adapter (Section 5.3, Section 5.8) — the
  one-to-many relationships above apply per row, not per raw provider
  name, which is what lets Finnhub's two roles carry independent health
  and log history without treating Finnhub as two different APIs.

--------------------------------------------------

## 11. Future API Expansion

Adding a new provider, or a new Category, is additive and never requires
changing the API Manager's own selection or failover logic:

- **New provider within an existing Category** (for example, a second
  backup for Fundamental Data) — add a new `api_provider` row and a new
  Provider Interface adapter satisfying the existing contract (Section
  5.8). The Registry mapping, Settings, and API Manager logic are
  unchanged. (Note: each Category is currently fixed at exactly one
  Primary and one Backup per Section 3 — adding a third candidate would
  itself be a scope change to that rule, not merely an additive step.)
- **New Category** (for example, a future Macroeconomic Data category) —
  define its Primary and Backup Provider in the Registry the same way
  Section 3's three categories are defined, add the corresponding
  `api_provider` rows, and implement adapters for any new providers
  involved. A provider can pick up a second role in a new Category
  exactly as Finnhub already does for Category 1 and Category 3 — no
  change to the Provider Interface contract is required. Provider
  Selection Logic (Section 6), Failover Rules (Section 7), and Health
  Check Logic (Section 8) all apply unchanged, since none of them are
  written against a specific Category or provider name.
- **Replacing a provider entirely** (for example, dropping Twelve Data
  for a different backup) — change the Registry mapping and retire the
  old adapter; no Collector, Workflow, or Planner code is touched, since
  none of them ever reference a provider name directly.

This mirrors the same additive principle `DATABASE_ARCHITECTURE.md`
already establishes for the Verified Knowledge Database (Section 5 of
that document): growth extends the model without altering what already
exists.

--------------------------------------------------

## 12. Rules Enforced by This Architecture

Restated from the source instructions, with how this architecture
enforces each one:

- **One .env file only.** Enforced by Section 2 and API Settings (Section
  5.4) — every provider's key, including both of Finnhub's Category
  roles, resolves through variable names in the single existing `.env`
  file; this architecture introduces no second configuration file.
- **API keys are never hardcoded.** Enforced by API Provider's Key
  Reference (Section 5.3) and `api_provider`'s key-name column (Section
  10.1), which store only the name of an environment variable, never a
  key value, in any table or in-memory record.
- **Collectors never call providers directly; Collectors only communicate
  with the API Manager.** Enforced structurally — the Provider Interface
  and every concrete adapter sit behind the API Manager (Section 4); no
  other component in the Research Engine is defined to hold a reference
  to a provider adapter.
- **The API Manager selects the provider.** Enforced by Provider
  Selection Logic (Section 6) — the caller supplies only Category,
  Operation, and Parameters, never a provider name.
- **Provider selection must be configurable; a Future Dashboard must be
  able to change Primary and Backup providers without code changes.**
  Enforced by the API Registry (Section 5.2) being the single, editable
  source of Category → Provider mapping that the API Manager reads at
  request time, and by the Dashboard's Manual Provider Switch (Section
  9).
- **API status must be tracked.** Enforced by API Health (Section 5.5)
  and the `api_health` table (Section 10.2), updated on every real
  request and on every manual Health Check button trigger.
- **Failover must not require Collector changes.** Enforced by the
  Failover Rules (Section 7) being entirely internal to the API Manager —
  a Collector's request and response shape are identical whether the
  Primary or Backup Provider ultimately answered.

--------------------------------------------------

## Notes

- See `RESEARCH_COLLECTORS.md` for the Collector contract this
  architecture sits behind — unchanged by this document.
- See `COLLECTOR_SOURCE_STRATEGY.md` for the trusted Source Categories a
  Collector's data must trace back to; the API Manager's Providers are the
  concrete implementations behind categories such as Official Financial
  Statements, Market Data Providers, and Financial News Sources defined
  there.
- See `RESEARCH_WORKFLOW.md` for the Failure Handling rule this
  architecture's failover exhaustion feeds into — a Collector that gets
  an explicit failure from the API Manager reports it exactly as any
  other missing data, per that document's Section 5.
- See `DATABASE_ARCHITECTURE.md` for the layering and relationship
  conventions (`One-to-One`, `One-to-Many`) this document's Database
  Design (Section 10) follows for consistency across the whole project.
- This document defines architecture only. Building the API Manager,
  its five adapters, the Dashboard, and the `api_provider` / `api_health`
  / `api_logs` tables is future implementation work, tracked in
  `ROADMAP.md`, and is not performed by this document.
