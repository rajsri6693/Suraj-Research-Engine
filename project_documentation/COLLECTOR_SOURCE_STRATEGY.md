# Collector Source Strategy

This document defines the Source Strategy every Research Collector
follows: which categories of source are trusted, which category each
Knowledge Section should be gathered from first, and what a collector
does when its sources disagree or none exist. It describes strategy
only — no collector implementation, no API calls, and no named website
or service.

--------------------------------------------------

## 1. Purpose

`RESEARCH_COLLECTORS.md` defines what each collector gathers — one
collector per Knowledge Section, returning a Collector Result. It does
not say where that collector is allowed to look. This document closes
that gap: it defines a fixed set of trusted Source Categories, the
priority order a collector follows among them for each Knowledge
Section, and the rules a collector applies when its sources disagree or
come up empty.

This document does NOT implement collectors. It does NOT call APIs. It
never names a specific website, service, or API — only the category of
source a fact of that kind should come from.

--------------------------------------------------

## 2. Source Categories

Every fact a collector gathers must come from one of the following ten
categories. A source outside this list is not trusted, regardless of how
convenient or plausible it is — an untrusted source is treated the same
as no source at all (see Section 6).

**Official Company Information**
Material a company publishes about its own identity, business, and
operations — legal and registration details, business description,
leadership, and official statements directly attributable to the
company. Trusted because the company is the authoritative source for
facts about itself.

**Official Exchange Information**
Material published by the stock exchange(s) a company is listed on —
listing status, ticker/symbol data, trading status, and
exchange-mandated disclosures. Trusted because the exchange is the
authoritative, regulated record of a security's trading identity and
status.

**Official Regulatory Information**
Material published by the securities or financial regulator(s) with
authority over the company or market — regulatory filings, compliance
notices, enforcement actions, approvals. Trusted because regulators hold
legal authority and independent oversight.

**Government Information**
Material published by government bodies relevant to law, policy, or the
sector a company operates in, distinct from the securities regulator
specifically — legislation, policy announcements, duties or tariffs,
official government statistics and sector reports. Trusted because
government bodies are the authoritative source for law and policy.

**Official Financial Statements**
A company's own reported financial disclosures — balance sheets, income
statements, cash flow statements, and financial ratios as reported.
Trusted because these are the company's own formally reported figures.

**Official Corporate Filings**
Formal documents a company is required or chooses to file with a
regulator or exchange — annual reports, prospectuses, disclosures of
material events, ownership or shareholding filings, corporate action
notices. Trusted because filings carry legal weight and formal
accountability.

**Market Data Providers**
Organizations whose business is aggregating and distributing trading
data — current price, historical OHLC, traded volume, market
capitalization. Trusted for aggregating exchange-sourced data reliably,
though positioned below Official Exchange Information where both are
available, since a provider is one step removed from the exchange
itself.

**Financial News Sources**
Reputable financial journalism and news coverage — reporting on events,
market commentary, interpretation of company or sector developments.
Useful for timely event coverage, but reports facts secondhand rather
than being the original authority, so it is positioned lower in priority
for factual claims and is most appropriate for Market News.

**Sector Information Sources**
Organizations that publish sector- or industry-wide research, statistics,
and benchmarks not specific to one company — sector size, growth trends,
competitive landscape data, industry benchmarks. Trusted for specialized
cross-company aggregation that a single company's own sources would not
cover.

**Technical Market Data Sources**
Sources that compute or publish derived technical indicators from
historical price data — moving averages, RSI, MACD, and other computed
signals. Trusted for specializing in the specific computation this
Knowledge Section requires, downstream of Historical Price (OHLC) data.

--------------------------------------------------

## 3. Priority Rules

Every Knowledge Section is assigned a Preferred Source Category and a
Fallback Category (Section 4). Within that assignment, a collector always
follows the same three-tier priority order:

- **Primary Source** — the Preferred Source Category for this Knowledge
  Section. A collector must attempt its Primary Source first, before
  considering any other category.
- **Secondary Source** — a second trusted category a collector may
  consult once it already has an answer from its Primary Source, either
  because the Primary Source was incomplete or to corroborate the fact
  with an independent source. Consulting a Secondary Source is not
  required when the Primary Source alone is sufficient, but doing so
  strengthens the Source Count a fact carries into Knowledge
  Verification's Confidence assessment.
- **Fallback Source** — the Fallback Category for this Knowledge Section
  (Section 4), consulted only when the Primary Source does not have the
  needed fact at all. A Fallback Source is still one of the ten trusted
  categories, never an untrusted substitute — it is simply lower priority
  than the Primary Source for this particular section.

A collector never skips ahead of a higher-priority category to save
effort, and never invents a value once Primary, Secondary, and Fallback
are all exhausted — see Section 6.

--------------------------------------------------

## 4. Collector Mapping

| Knowledge Section | Preferred Source Category (Primary) | Fallback Category |
|---|---|---|
| Company Information | Official Company Information | Official Corporate Filings |
| Business Overview | Official Company Information | Official Corporate Filings |
| Products & Services | Official Company Information | Official Corporate Filings |
| Management | Official Company Information | Official Corporate Filings |
| Shareholding | Official Corporate Filings | Official Regulatory Information |
| Financial Information | Official Financial Statements | Official Corporate Filings |
| Orders & Contracts | Official Corporate Filings | Financial News Sources |
| Competitors | Sector Information Sources | Financial News Sources |
| Risks | Official Corporate Filings | Official Regulatory Information |
| Market News | Financial News Sources | Official Exchange Information |
| Sector Information | Sector Information Sources | Government Information |
| Government Policies | Government Information | Official Regulatory Information |
| Market Data | Official Exchange Information | Market Data Providers |
| Historical Price (OHLC) | Market Data Providers | Official Exchange Information |
| Technical Analysis | Technical Market Data Sources | Market Data Providers |
| Corporate Actions | Official Corporate Filings | Official Exchange Information |
| Sources | Not applicable — compiled from the sources already used by every other section's collector, not independently sourced from one of the ten categories. | Not applicable |
| Metadata | Not applicable — derived from the collection process itself (collection time, collector status), not an external source category. | Not applicable |

--------------------------------------------------

## 5. Conflict Rules

A collector may consult more than one Source Category for the same fact
— its Primary Source and a Secondary Source, or its Primary and Fallback
Source across separate attempts. When two trusted sources disagree on the
same fact:

- The collector must NEVER silently resolve the disagreement — it never
  picks one value as correct, edits one value to match the other, or
  averages or blends them into a single figure. Deciding which of two
  sourced claims is correct is a verification judgment, not a collection
  task, and collectors must never verify information, per
  `RESEARCH_COLLECTORS.md`.
- The collector reports the disagreement plainly within its Collected
  Data, stating both values and which Source Category each came from,
  rather than presenting only one value as if it were uncontested.
- Both disagreeing sources are included in the collector's Sources list,
  so the conflict remains traceable once it reaches Knowledge
  Verification, which is where it is actually resolved (per
  `KNOWLEDGE_VERIFICATION.md`'s Conflicting Information rule, routing the
  section to Needs Human Review).
- Collector Status is unaffected by the disagreement itself — the
  collector still reports Success, since it successfully completed its
  collection attempt. Collector Status describes whether the attempt
  completed, not whether the content it found agrees with itself.

--------------------------------------------------

## 6. Missing Source Rules

If a collector has attempted its Primary Source, its Secondary Source
where applicable, and its Fallback Source, and none of the ten trusted
Source Categories has the fact this Knowledge Section needs:

- The collector reports Collector Status Failed, per
  `RESEARCH_COLLECTORS.md` — no Collected Data and no Sources are
  produced.
- The collector never substitutes a source outside the ten trusted
  categories to fill the gap, no matter how easily available or
  plausible it is. An untrusted source is treated exactly the same as no
  source at all.
- The collector never fabricates, estimates, or guesses a value to avoid
  reporting Failed. A missing fact is reported as missing.
- This failure is handled downstream exactly as any other collector
  failure: the section is excluded from this run's Research Package and
  reflected as absent rather than silently filled in, per
  `RESEARCH_WORKFLOW.md`'s Failure Handling rule.

--------------------------------------------------

## Notes

- See `RESEARCH_COLLECTORS.md` for what each collector gathers and the
  Collector Result fields (Knowledge Section, Collected Data, Sources,
  Collection Time, Collector Status) this strategy feeds into.
- See `KNOWLEDGE_MODEL.md` for the definition of every Knowledge Section
  referenced in this document.
- This document defines source strategy only. Verifying, resolving
  conflicts with authority, and approving knowledge are each owned by
  their own layer — see `KNOWLEDGE_VERIFICATION.md` and
  `HUMAN_REVIEW.md`.
