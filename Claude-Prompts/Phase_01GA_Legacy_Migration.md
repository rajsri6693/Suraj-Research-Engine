# Phase 01GA - Legacy Migration

Read and execute this document completely.

Work ONLY inside the current repository.

Do NOT modify anything outside this repository.

--------------------------------------------------

OBJECTIVE

Migrate the remaining project components from the old schema architecture to the new Verified Knowledge Database architecture.

This is a migration phase.

NOT a compatibility phase.

NOT a rollback.

The old schema system has been permanently removed.

Do NOT recreate it.

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

Update every remaining component that still depends on the removed legacy schema.

Components include (if they exist):

research_database/database_manager.py

research_database/database_health_check.py

research_database/sample_data_seeder.py

knowledge_viewer/viewer.py

main.py

--------------------------------------------------

REQUIREMENTS

Update every import.

Update every table reference.

Update every schema reference.

Update every field reference.

Use ONLY the new entity schema files.

Use ONLY verified_knowledge.db.

Remove every dependency on the deleted legacy schema.

--------------------------------------------------

DO NOT

Do NOT recreate:

company_schema.py

verified_research_schema.py

raw_research_schema.py

research_history_schema.py

cache_schema.py

Do NOT add compatibility layers.

Do NOT duplicate code.

Do NOT create wrapper classes.

Do NOT restore deleted architecture.

--------------------------------------------------

EXPECTED RESULT

python main.py runs successfully.

Knowledge Viewer works.

Database Health Check works.

Sample Data Seeder works.

Database Manager works.

Everything uses the new schema.

--------------------------------------------------

VERIFY

Confirm:

1. All legacy imports removed.

2. All components use the new schema.

3. python main.py runs successfully.

4. Knowledge Viewer works.

5. Database Manager works.

6. Database Health Check works.

7. Sample Data Seeder works.

8. No legacy schema dependency exists.

9. No compatibility layer created.

10. Only current repository modified.

Print the final report.