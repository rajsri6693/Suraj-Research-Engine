# Phase 01G - SQLite Foundation

Read and execute this document completely.

Work ONLY inside the current repository.

Do NOT modify anything outside this repository.

--------------------------------------------------

OBJECTIVE

Build the SQLite database foundation for the Verified Knowledge Database.

This phase creates the physical database.

No CRUD.

No Research Engine.

No Viewer.

No AI.

No API.

--------------------------------------------------

SOURCE OF TRUTH

Use ONLY:

project_documentation/KNOWLEDGE_MODEL.md

project_documentation/DATABASE_ARCHITECTURE.md

project_documentation/DATABASE_RELATIONSHIPS.md

research_database/schema/

--------------------------------------------------

TASK

Implement the SQLite foundation.

--------------------------------------------------

Create:

research_database/database_connection.py

research_database/database_initializer.py

--------------------------------------------------

Create the SQLite database:

research_database/data/verified_knowledge.db

--------------------------------------------------

Implement

1.

Database connection

--------------------------------------------------

2.

Database initialization

--------------------------------------------------

3.

Automatic table creation

using every schema.

--------------------------------------------------

4.

Automatic database creation

if database does not exist.

--------------------------------------------------

5.

Automatic initialization

on first startup.

--------------------------------------------------

6.

Safe database closing.

--------------------------------------------------

RULES

Do NOT implement CRUD.

Do NOT insert sample data.

Do NOT create viewer logic.

Do NOT create search logic.

Do NOT create research logic.

Do NOT create backup.

Do NOT create health check.

Only SQLite foundation.

--------------------------------------------------

VERIFY

Confirm:

1.

Database created successfully.

2.

All tables created.

3.

Connection successful.

4.

Database closes correctly.

5.

No CRUD exists.

6.

No sample data inserted.

7.

Only current repository modified.

Print final report.