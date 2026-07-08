# Phase 01I - Company Repository

Read and execute this document completely.

Work ONLY inside the current repository.

Do NOT modify anything outside this repository.

--------------------------------------------------

OBJECTIVE

Implement the Company Repository.

This repository is responsible ONLY for Company entity operations.

It must use DatabaseManager exclusively.

Direct SQLite access is NOT allowed.

--------------------------------------------------

SOURCE OF TRUTH

Use ONLY:

project_documentation/KNOWLEDGE_MODEL.md

project_documentation/DATABASE_ARCHITECTURE.md

project_documentation/DATABASE_RELATIONSHIPS.md

research_database/schema/company.py

research_database/database_manager.py

--------------------------------------------------

TASK

Create:

research_database/repositories/

research_database/repositories/company_repository.py

--------------------------------------------------

IMPLEMENT

The repository must provide:

1. Create Company

2. Update Company

3. Delete Company

4. Get Company by ID

5. Get Company by Symbol

6. Search Company

7. List Companies

8. Company Statistics

--------------------------------------------------

SEARCH

Search must support:

• Company Name

• Symbol

• Exchange Symbol

Case-insensitive matching.

--------------------------------------------------

STATISTICS

Return:

• Total Companies

• Total Sectors

• Database Version (if available)

--------------------------------------------------

RULES

Do NOT access sqlite3 directly.

Use ONLY DatabaseManager.

Do NOT modify DatabaseManager.

Do NOT modify schema.

Do NOT modify SQLite foundation.

Do NOT modify Viewer.

Do NOT modify Research Engine.

--------------------------------------------------

QUALITY

Repository must:

Return dataclass objects.

Handle exceptions cleanly.

Use transactions where required.

Avoid duplicate code.

Be reusable by every future module.

--------------------------------------------------

VERIFY

Confirm:

1. Repository created successfully.

2. No direct SQLite access.

3. CRUD works correctly.

4. Search works.

5. Statistics work.

6. Returns Company dataclass objects.

7. Uses only DatabaseManager.

8. Only current repository modified.

Print the final report.