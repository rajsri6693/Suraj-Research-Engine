# SURAJ RESEARCH ENGINE
# Phase 01B — Database Schema Design

IMPORTANT

Work ONLY inside the current repository.

Do NOT modify any external repository.

Do NOT create another project.

========================================================

OBJECTIVE

Design the database schema.

Do NOT execute SQL.

Do NOT connect to SQLite.

Do NOT create CRUD operations.

Do NOT create API integrations.

Do NOT create AI integrations.

========================================================

Design the following logical schemas.

1. Raw Research

Purpose:
Store data exactly as received from external APIs.

Suggested fields:
- id
- topic
- source_name
- source_type
- raw_payload
- fetched_at
- status

========================================================

2. Verified Research

Purpose:
Store validated research ready for AI.

Suggested fields:
- id
- topic
- company
- sector
- verified_fact
- confidence_score
- source_count
- verified_at

========================================================

3. Research History

Purpose:
Track every completed research request.

Suggested fields:
- id
- topic
- started_at
- completed_at
- duration
- ai_provider
- status

========================================================

4. Cache

Purpose:
Store reusable research.

Suggested fields:
- id
- cache_key
- cache_value
- expires_at
- created_at

========================================================

Rules

Create logical schema definitions only.

No SQL execution.

No CREATE TABLE statements.

No database connections.

Document every field.

Explain the purpose of every schema.

========================================================

VERIFICATION

Verify:

- Every schema exists.
- No SQL statements.
- No SQLite usage.
- No implementation logic.
- Only current repository modified.

========================================================

OUTPUT

List every schema.

Explain why it exists.

Explain every field.

Confirm repository is ready for Phase 01C.