# Phase 01IA - Knowledge Viewer Migration

Read and execute this document completely.

Work ONLY inside the current repository.

Do NOT modify anything outside this repository.

--------------------------------------------------

OBJECTIVE

Migrate the Knowledge Viewer to the new Repository architecture.

The Knowledge Viewer must NEVER access DatabaseManager directly.

The Knowledge Viewer must use CompanyRepository.

--------------------------------------------------

SOURCE OF TRUTH

Use ONLY:

research_database/repositories/company_repository.py

research_database/database_manager.py

knowledge_viewer/viewer.py

main.py

--------------------------------------------------

TASK

Update:

knowledge_viewer/viewer.py

main.py (only if required)

--------------------------------------------------

REQUIREMENTS

Replace every DatabaseManager call with CompanyRepository.

The Knowledge Viewer must:

• Search Company

• List Companies (if supported)

• Company Statistics

• Database Health

All Company operations must go through CompanyRepository.

--------------------------------------------------

DO NOT

Do NOT modify DatabaseManager.

Do NOT modify CompanyRepository.

Do NOT modify SQLite.

Do NOT modify schema.

Do NOT create new repositories.

--------------------------------------------------

ARCHITECTURE

Knowledge Viewer

↓

Company Repository

↓

Database Manager

↓

SQLite

--------------------------------------------------

VERIFY

Confirm:

1. Knowledge Viewer migrated successfully.

2. No direct DatabaseManager calls remain.

3. No direct SQLite access exists.

4. Search works.

5. Statistics work.

6. Database Health works.

7. python main.py runs successfully.

8. Only current repository modified.

Print the final report.