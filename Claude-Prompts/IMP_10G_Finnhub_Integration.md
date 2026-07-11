Read and execute the instructions from:

Claude-Prompts/IMP_10G_Finnhub_Integration.md

Implement Finnhub as the Backup Provider for:

- Fundamental Data
- News

Use the existing API Manager architecture.

Do not redesign any existing architecture.

Run live validation.

Verify automatic failover from:

- FMP → Finnhub
- NewsAPI → Finnhub

Verify automatic failback when the Primary Provider becomes available again.

Persist all successful responses using the existing SQLite Database Manager.

Run:

- Finnhub Provider unit tests
- Finnhub integration tests
- Failover tests
- Failback tests
- SQLite persistence validation
- Full repository test suite
- Full repository compilation

Fix only genuine defects.

Print:

1. Live Validation Report
2. Fundamental Failover Report
3. News Failover Report
4. Failback Report
5. Provider Selection Report
6. SQLite Persistence Report
7. Verification Report

Do not commit.