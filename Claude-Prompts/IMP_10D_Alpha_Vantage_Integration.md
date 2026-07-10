# Research Engine
# IMP-10D - Alpha Vantage Integration
# Version 1.0

Read and execute this document completely.

Work ONLY inside the current repository.

Use the existing API Manager architecture.

Do NOT redesign any existing architecture.

--------------------------------------------------

OBJECTIVE

Integrate Alpha Vantage as the Primary Provider for the Market & Technical Data category.

Only Alpha Vantage is implemented in this phase.

Twelve Data remains the configured Backup Provider but stays as a placeholder.

--------------------------------------------------

SOURCE OF TRUTH

- project_documentation/API_MANAGER_ARCHITECTURE.md
- Existing API Manager implementation
- Existing Technical Analysis Collector
- Existing Historical Price Collector

--------------------------------------------------

API CATEGORY

Market & Technical

Primary Provider

Alpha Vantage

Backup Provider

Twelve Data (placeholder only)

--------------------------------------------------

READ API KEY FROM

.env

ALPHA_VANTAGE_API_KEY

Never hardcode API keys.

--------------------------------------------------

IMPLEMENT

Implement Alpha Vantage provider support for:

- Real-time Price
- Daily OHLC
- Weekly OHLC
- Monthly OHLC
- Intraday OHLC
- RSI
- MACD
- SMA
- EMA
- Volume
- Chart Dataset

--------------------------------------------------

CHART DATASET

Generate a structured chart dataset.

Do NOT generate:

- PNG
- SVG
- HTML
- JavaScript
- Images

Return only structured chart data suitable for:

- Dashboard
- Phase-2 Video Engine
- Future Web UI

--------------------------------------------------

COLLECTORS

Update ONLY:

- Historical Price Collector
- Technical Analysis Collector

Collectors must never call Alpha Vantage directly.

Collectors must always use the API Manager.

--------------------------------------------------

DATABASE

For every successful response:

- Parse the response.
- Map to existing Research Engine models.
- Persist using the existing SQLite Database Manager.
- Do NOT redesign the database.
- Do NOT create a new database.
- Do NOT modify the schema.

Verify stored data can be read back correctly.

--------------------------------------------------

FAILURE HANDLING

Handle:

- Invalid API Key
- Timeout
- HTTP 5xx
- Rate Limit
- Unknown Error

Update Provider Status accordingly.

--------------------------------------------------

BACKUP PROVIDER

Verify the API Manager correctly identifies Twelve Data as the configured Backup Provider.

Do NOT implement Twelve Data.

--------------------------------------------------

LIVE VALIDATION

Validate using:

- BEL
- TCS
- RELIANCE
- INFY

If Indian symbols require exchange-specific formatting, determine the correct format, retry, and report the working symbol.

Do NOT hardcode symbol conversion.

--------------------------------------------------

VERIFY

For each symbol verify:

- API key loaded
- Authentication succeeded
- Price retrieved
- Historical OHLC retrieved
- RSI retrieved
- MACD retrieved
- SMA retrieved
- EMA retrieved
- Chart Dataset generated
- API Manager routing correct
- SQLite persistence successful
- SQLite read-back successful
- Provider ONLINE
- No API key exposed

--------------------------------------------------

TESTING

Run:

- Alpha Vantage Provider unit tests
- Alpha Vantage integration tests
- SQLite persistence validation
- Full repository compilation

Fix only genuine defects.

--------------------------------------------------

OUTPUT

Print:

1. Live Validation Report
2. Chart Dataset Report
3. Provider Selection Report
4. SQLite Persistence Report
5. Verification Report

Do not commit.