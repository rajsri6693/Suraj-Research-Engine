# Phase 01F - Database Relationships & Keys

Read and execute this document completely.

Work ONLY inside the current repository.

Do NOT modify anything outside this repository.

--------------------------------------------------

OBJECTIVE

Finalize the logical relationships of the Verified Knowledge Database.

This phase defines how every entity is connected.

This is DESIGN ONLY.

NOT implementation.

NOT SQLite.

NOT CRUD.

--------------------------------------------------

SOURCE OF TRUTH

Use ONLY:

project_documentation/KNOWLEDGE_MODEL.md

project_documentation/DATABASE_ARCHITECTURE.md

--------------------------------------------------

TASK

Create ONLY this document:

project_documentation/DATABASE_RELATIONSHIPS.md

--------------------------------------------------

The document must define:

# 1. Primary Entity

Identify the root entity of the database.

Explain why it is the root.

--------------------------------------------------

# 2. Primary Key

Define the primary key of every entity.

Examples:

Company

Sector

Market News

Financial Information

Products & Services

Technical Analysis

Market Data

Price History

Corporate Actions

Sources

Metadata

etc.

--------------------------------------------------

# 3. Relationships

Define:

One-to-One

One-to-Many

Many-to-One

Explain every relationship.

Do NOT use Many-to-Many unless absolutely required.

--------------------------------------------------

# 4. Reference Fields

For every relationship define the logical reference fields.

Examples:

company_id

sector_id

news_id

source_id

metadata_id

etc.

Documentation only.

--------------------------------------------------

# 5. Unique Constraints

Identify fields that should always be unique.

Examples:

Company Symbol

ISIN

Exchange Symbol

News ID

etc.

--------------------------------------------------

# 6. Recommended Indexes

Recommend indexes for faster searching.

Examples:

Company Name

Ticker

Sector

Country

Industry

Published Date

Record Date

etc.

Documentation only.

--------------------------------------------------

# 7. Entity Dependency Order

Define the correct creation order.

Example:

Sector

↓

Company

↓

Products

↓

Financial Information

↓

Market Data

↓

Price History

↓

Technical Analysis

↓

Corporate Actions

↓

Sources

↓

Metadata

--------------------------------------------------

# 8. Future Scalability

Explain how new entities can be added without breaking existing relationships.

--------------------------------------------------

RULES

Documentation only.

Do NOT create Python code.

Do NOT modify schema.

Do NOT modify SQLite.

Do NOT modify viewer.

Do NOT modify manager.

Do NOT modify implementation.

--------------------------------------------------

VERIFY

Confirm:

1. Only DATABASE_RELATIONSHIPS.md created.

2. No Python modified.

3. No schema modified.

4. No database implementation added.

5. No SQLite code.

6. Only current repository modified.

Print the final report.