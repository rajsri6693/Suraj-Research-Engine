# Research Engine
# IMP-10E - Twelve Data Integration
# Version 1.0

Read and execute this document completely.

Work ONLY inside the current repository.

Use the existing API Manager architecture.

Do NOT redesign any existing architecture.

--------------------------------------------------

OBJECTIVE

Integrate Twelve Data as the Backup Provider for the Market & Technical category.

Alpha Vantage remains the Primary Provider.

This phase implements the live Twelve Data Provider and validates automatic failover.

--------------------------------------------------

SOURCE OF TRUTH

- project_documentation/API_MANAGER_ARCHITECTURE.md
- Existing API Manager
- Existing Historical Price Collector
- Existing Technical Analysis Collector

--------------------------------------------------

API CATEGORY

Market & Technical

Primary Provider

Alpha Vantage

Backup Provider

Twelve Data

--------------------------------------------------

READ API KEY FROM

.env

TWELVE_DATA_API_KEY

Never hardcode API keys.

--------------------------------------------------

IMPLEMENT

Implement Twelve Data Provider support for:

- Live Price
- Daily OHLC
- Weekly OHLC
- Monthly OHLC
- Intraday OHLC
- RSI (if supported)
- SMA (if supported)
- EMA (if supported)
- Volume
- Chart Dataset

Use only officially supported Twelve Data endpoints.

--------------------------------------------------

COLLECTORS

Update ONLY:

- Historical Price Collector
- Technical Analysis Collector

Collectors must never call Twelve Data directly.

Collectors must always use the API Manager.

--------------------------------------------------

DATABASE

For every successful response:

- Parse the response.
- Map to the existing Research Engine models.
- Persist using the existing SQLite Database Manager.
- Do NOT redesign the database.
- Do NOT create a new database.
- Do NOT modify the schema.

Verify stored data can be read back correctly.

--------------------------------------------------

FAILOVER

Validate automatic failover.

Scenario 1

Alpha Vantage ONLINE

↓

API Manager

↓

Alpha Vantage used

--------------------------------------------------

Scenario 2

Alpha Vantage DOWN

↓

API Manager

↓

Automatically switch

↓

Twelve Data

↓

Persist returned data

↓

Log provider selection

--------------------------------------------------

Do not modify Collectors to support failover.

Failover must happen only inside API Manager.

--------------------------------------------------

PROVIDER HEALTH

Verify:

ONLINE

DOWN

TIMEOUT

RATE_LIMITED

UNKNOWN

Provider status must update correctly.

--------------------------------------------------

LIVE VALIDATION

Validate using:

- BEL
- TCS
- RELIANCE
- INFY

If exchange-specific symbols are required:

Detect

Retry

Report working format

Do NOT hardcode symbol conversion.

--------------------------------------------------

VERIFY

For each symbol verify:

- API key loaded
- Authentication succeeded
- Live Price retrieved
- Historical OHLC retrieved
- Technical data retrieved (if supported)
- Chart Dataset generated
- API Manager routing correct
- SQLite persistence successful
- SQLite read-back successful
- Provider ONLINE
- No API key exposed

--------------------------------------------------

TESTING

Run:

- Twelve Data Provider unit tests
- Twelve Data integration tests
- Failover tests
- SQLite persistence validation
- Full repository test suite
- Full repository compilation

Fix only genuine defects.

--------------------------------------------------

OUTPUT

Print:

1. Live Validation Report
2. Failover Validation Report
3. Provider Selection Report
4. SQLite Persistence Report
5. Technical Data Report
6. Verification Report

Do not commit.