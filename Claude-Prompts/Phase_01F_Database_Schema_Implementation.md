# Phase 01F - Database Schema Implementation

Read and execute this document completely.

Work ONLY inside the current repository.

Do NOT modify anything outside this repository.

--------------------------------------------------

OBJECTIVE

Implement the Verified Knowledge Database schema.

Use ONLY these documents as the source of truth:

- project_documentation/KNOWLEDGE_MODEL.md
- project_documentation/DATABASE_ARCHITECTURE.md

--------------------------------------------------

TASK

Implement the Python dataclass schema files.

Each entity defined in DATABASE_ARCHITECTURE.md must have its own schema file.

Examples (adapt names if required):

research_database/schema/

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

technical_analysis.py

market_data.py

price_history.py

sources.py

metadata.py

--------------------------------------------------

RULES

Each file must contain ONLY:

- dataclass
- type hints
- docstrings

No SQLite.

No SQL.

No CRUD.

No database manager.

No viewer.

No business logic.

No methods except dataclass definitions.

No API calls.

--------------------------------------------------

IMPLEMENT

Represent every field defined by the documentation.

Keep the design clean, reusable and extendable.

--------------------------------------------------

VERIFY

Confirm:

1. Every entity has its own schema file.

2. All schema files compile successfully.

3. No SQLite code exists.

4. No CRUD exists.

5. No implementation outside schema.

6. Only current repository modified.

Print the final report.