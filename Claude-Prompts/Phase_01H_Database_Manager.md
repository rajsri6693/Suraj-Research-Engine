# Phase 01H - Database Manager

Read and execute this document completely.

Work ONLY inside the current repository.

Do NOT modify anything outside this repository.

--------------------------------------------------

OBJECTIVE

Build the central Database Manager for the Verified Knowledge Database.

The Database Manager will become the ONLY gateway between the application and SQLite.

No other module is allowed to access SQLite directly.

--------------------------------------------------

SOURCE OF TRUTH

Use ONLY:

project_documentation/KNOWLEDGE_MODEL.md

project_documentation/DATABASE_ARCHITECTURE.md

project_documentation/DATABASE_RELATIONSHIPS.md

research_database/schema/

research_database/data/verified_knowledge.db

--------------------------------------------------

TASK

Implement:

research_database/database_manager.py

--------------------------------------------------

RESPONSIBILITIES

The Database Manager must:

• Open database connection

• Close database connection

• Manage transactions

• Provide a reusable execution interface

• Provide reusable query helpers

• Handle commit / rollback

• Handle SQLite exceptions

• Return clean results

--------------------------------------------------

DO NOT IMPLEMENT

Do NOT implement entity CRUD.

Examples:

Company CRUD

Market News CRUD

Technical Analysis CRUD

Price History CRUD

Sector CRUD

etc.

Those belong to future phases.

--------------------------------------------------

DESIGN

Create reusable internal methods that future CRUD modules can use.

The manager should become the database backbone.

--------------------------------------------------

RULES

No Research Engine logic.

No Viewer logic.

No Script Engine logic.

No AI logic.

No API logic.

No business rules.

Only generic database management.

--------------------------------------------------

VERIFY

Confirm:

1. Database Manager created successfully.

2. Connection management works.

3. Transaction management works.

4. Commit/Rollback works.

5. Exception handling works.

6. No entity CRUD implemented.

7. SQLite is accessed ONLY through Database Manager.

8. Only current repository modified.

Print the final report.