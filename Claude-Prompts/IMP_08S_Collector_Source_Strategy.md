# Research Engine
# IMP-08S - Collector Source Strategy
# Version 1.0

Read and execute this document completely.

Work ONLY inside the current repository.

Do NOT modify anything outside this repository.

--------------------------------------------------

OBJECTIVE

Design the Source Strategy used by all Research Collectors.

This document defines trusted source categories and source priority.

It does NOT implement collectors.

It does NOT call APIs.

--------------------------------------------------

SOURCE OF TRUTH

Use ONLY:

project_documentation/KNOWLEDGE_MODEL.md

project_documentation/RESEARCH_COLLECTORS.md

--------------------------------------------------

TASK

Create ONLY:

project_documentation/COLLECTOR_SOURCE_STRATEGY.md

--------------------------------------------------

Define

1.

Purpose

2.

Source Categories

Official Company Information

Official Exchange Information

Official Regulatory Information

Government Information

Official Financial Statements

Official Corporate Filings

Market Data Providers

Financial News Sources

Sector Information Sources

Technical Market Data Sources

--------------------------------------------------

3.

Priority Rules

Primary Source

Secondary Source

Fallback Source

--------------------------------------------------

4.

Collector Mapping

For every Knowledge Section define:

Preferred Source Category

Fallback Category

--------------------------------------------------

5.

Conflict Rules

If two trusted sources disagree:

How should the collector report the conflict?

--------------------------------------------------

6.

Missing Source Rules

What happens if no trusted source exists?

--------------------------------------------------

RULES

Do NOT mention specific websites.

Do NOT mention API names.

Do NOT write code.

Documentation only.

--------------------------------------------------

VERIFY

1. Only COLLECTOR_SOURCE_STRATEGY.md created.

2. No Python modified.

3. No Database modified.

4. No Schema modified.

5. Only current repository modified.

Print the final report.