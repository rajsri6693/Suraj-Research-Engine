# Phase 01FA - Schema Cleanup

Read and execute this document completely.

Work ONLY inside the current repository.

Do NOT modify anything outside this repository.

--------------------------------------------------

OBJECTIVE

Clean the schema directory.

The project has moved to the new Verified Knowledge Database architecture.

Legacy schema files are no longer allowed.

There must be only ONE schema definition for each entity.

--------------------------------------------------

DELETE the following legacy schema files if they exist:

research_database/schema/company_schema.py

research_database/schema/cache_schema.py

research_database/schema/raw_research_schema.py

research_database/schema/research_history_schema.py

research_database/schema/verified_research_schema.py

--------------------------------------------------

KEEP ONLY the new entity schema files.

Expected schema directory:

company.py

products_services.py

management.py

shareholding.py

financial_information.py

orders_contracts.py

competitors.py

risks.py

market_news.py

sector.py

government_policies.py

market_data.py

technical_analysis.py

historical_price.py

corporate_actions.py

sources.py

metadata.py

--------------------------------------------------

RULES

Do NOT modify any dataclass.

Do NOT rename any new schema file.

Do NOT add any new fields.

Do NOT create any new schema.

Do NOT modify database manager.

Do NOT modify viewer.

Do NOT modify documentation.

Cleanup only.

--------------------------------------------------

VERIFY

Confirm:

1. Legacy schema files were removed.

2. Exactly 17 schema files remain.

3. Every schema compiles successfully.

4. No duplicate schema exists.

5. No SQLite code exists.

6. No CRUD exists.

7. Only current repository modified.

Print the final report.