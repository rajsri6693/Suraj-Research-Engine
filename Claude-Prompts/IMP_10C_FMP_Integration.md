# Research Engine
# IMP-10C - Financial Modeling Prep (FMP) Integration
# Version 1.0

Read and execute this document completely.

Work ONLY inside the current repository.

Use the existing API Manager architecture implemented in IMP-10B.

Do NOT redesign the architecture.

--------------------------------------------------

OBJECTIVE

Integrate Financial Modeling Prep (FMP) as the Primary Provider for the Fundamental Data category.

Only FMP is implemented in this phase.

Finnhub remains a registered placeholder provider.

--------------------------------------------------

SOURCE OF TRUTH

project_documentation/API_MANAGER_ARCHITECTURE.md

Use the existing API Manager.

Use the existing Collector architecture.

Do NOT redesign anything.

--------------------------------------------------

API CATEGORY

Fundamental Data

Primary

Financial Modeling Prep (FMP)

Backup

Finnhub (placeholder only)

--------------------------------------------------

DO NOT IMPLEMENT

Alpha Vantage

Twelve Data

NewsAPI

Finnhub live implementation

--------------------------------------------------

READ API KEY FROM

.env

FMP_API_KEY

Never hardcode any API key.

--------------------------------------------------

IMPLEMENT

FMP Provider

API Authentication

Connection Validation

HTTP Client

Request Builder

Response Parser

Error Handling

Rate Limit Handling

Timeout Handling

Retry Logic

Logging

--------------------------------------------------

SUPPORTED DATA

Implement ONLY the endpoints required for

- Company Profile
- Financial Statements
- Financial Ratios
- Earnings
- Dividend
- Stock Split
- Management
- Shareholding
- Competitors
- Products & Services
- Corporate Actions
- Orders & Contracts

--------------------------------------------------

COLLECTORS

Update ONLY the collectors belonging to the Fundamental Data category.

Collectors must request data only through API Manager.

Collectors must never call FMP directly.

--------------------------------------------------

FAILURE HANDLING

If

Invalid API Key

↓

Return INVALID_KEY

----------------

Timeout

↓

Return TIMEOUT

----------------

Rate Limit

↓

Return RATE_LIMITED

----------------

Server Error

↓

Return DOWN

----------------

Unknown

↓

Return UNKNOWN

--------------------------------------------------

BACKUP

Do NOT call Finnhub.

Only verify that the API Manager correctly identifies Finnhub as the configured Backup Provider.

--------------------------------------------------

TESTING

Create

Unit Tests

Integration Tests

Mock all HTTP responses.

No live internet calls during tests.

--------------------------------------------------

VERIFY

1. API Manager unchanged.
2. Architecture unchanged.
3. Only Fundamental category updated.
4. No Technical category modified.
5. No News category modified.
6. No SQLite schema modified.
7. .env used correctly.
8. No API key hardcoded.
9. All tests pass.
10. Full compilation passes.

Print complete implementation report.

Print verification report.

Do not commit.