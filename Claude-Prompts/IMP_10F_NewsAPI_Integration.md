# Research Engine
# IMP-10F - NewsAPI Integration
# Version 1.0

Read and execute this document completely.

Work ONLY inside the current repository.

Use the existing API Manager architecture.

Do NOT redesign any existing architecture.

--------------------------------------------------

OBJECTIVE

Integrate NewsAPI as the Primary Provider for the News category.

NewsAPI becomes the live provider.

Finnhub remains the configured Backup Provider but stays as a placeholder.

--------------------------------------------------

SOURCE OF TRUTH

- project_documentation/API_MANAGER_ARCHITECTURE.md
- Existing API Manager
- Existing Market News Collector

--------------------------------------------------

API CATEGORY

News

Primary Provider

NewsAPI

Backup Provider

Finnhub

--------------------------------------------------

READ API KEY FROM

.env

NEWS_API_KEY

Never hardcode API keys.

--------------------------------------------------

IMPLEMENT

Implement NewsAPI Provider support for:

- Company News
- Market News
- Sector News
- Breaking News

Use only officially documented NewsAPI endpoints.

--------------------------------------------------

COLLECTORS

Update ONLY:

- Market News Collector

Collectors must never call NewsAPI directly.

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

NEWS FILTERING

Verify support for:

- Company-specific news
- Sector-specific news
- General market news

Remove duplicate articles returned within the same request.

Keep original publication timestamps.

Do not fabricate summaries.

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

Verify the API Manager correctly identifies Finnhub as the configured Backup Provider.

Do NOT implement Finnhub in this phase.

--------------------------------------------------

LIVE VALIDATION

Validate using:

- BEL
- TCS
- RELIANCE
- INFY
- NIFTY 50

If NewsAPI search requires different query formatting, determine the correct format and report it.

Do NOT hardcode query conversion.

--------------------------------------------------

VERIFY

For each validation verify:

- API key loaded correctly.
- Authentication succeeded.
- News articles retrieved.
- Company news mapped correctly.
- Market news mapped correctly.
- Publication timestamps preserved.
- Duplicate removal working.
- API Manager routing correct.
- SQLite persistence successful.
- SQLite read-back successful.
- Provider ONLINE.
- No API key exposed.

--------------------------------------------------

TESTING

Run:

- NewsAPI Provider unit tests
- NewsAPI integration tests
- SQLite persistence validation
- Full repository test suite
- Full repository compilation

Fix only genuine defects.

--------------------------------------------------

OUTPUT

Print:

1. Live Validation Report
2. News Retrieval Report
3. Provider Selection Report
4. SQLite Persistence Report
5. Duplicate Removal Report
6. Verification Report

Do not commit.