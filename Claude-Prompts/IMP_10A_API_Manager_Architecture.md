# Research Engine
# IMP-10A - API Manager Architecture
# Version 1.0

Read and execute this document completely.

Work ONLY inside the current repository.

Do NOT modify any existing implementation.

This task is DOCUMENTATION ONLY.

--------------------------------------------------

OBJECTIVE

Design the complete API Provider Management architecture for the Research Engine.

This architecture will become the single gateway through which every Collector accesses external APIs.

No Collector will ever directly call any API.

--------------------------------------------------

SOURCE OF TRUTH

Use ONLY the existing Research Engine architecture and implementation.

Do NOT redesign existing collectors.

Do NOT redesign Workflow.

Do NOT redesign Planner.

--------------------------------------------------

AVAILABLE API PROVIDERS

Fundamental Data

- Financial Modeling Prep (FMP)
- Finnhub

Market & Technical

- Alpha Vantage
- Twelve Data

News

- NewsAPI
- Finnhub News

--------------------------------------------------

FINAL API CATEGORIES

Category 1

Fundamental Data

Primary Provider

FMP

Backup Provider

Finnhub

Provides

- Company Profile
- Financial Statements
- Financial Ratios
- Earnings
- Dividend
- Stock Split
- Management
- Shareholding
- Competitors
- Products & Services
- Corporate Actions
- Orders & Contracts

--------------------------------------------------

Category 2

Market & Technical

Primary Provider

Alpha Vantage

Backup Provider

Twelve Data

Provides

- Real-time Price
- Historical OHLC
- Intraday
- Technical Indicators
- Chart Dataset

--------------------------------------------------

Category 3

News

Primary Provider

NewsAPI

Backup Provider

Finnhub News

Provides

- Company News
- Market News
- Sector News
- Breaking News

--------------------------------------------------

DESIGN

Define

API Manager

API Registry

API Provider

API Settings

API Health

API Logging

API Status

Provider Interface

--------------------------------------------------

RULES

Collectors NEVER call providers directly.

Collectors ONLY call API Manager.

API Manager chooses provider.

API keys are NEVER hardcoded.

All keys come from .env.

Provider selection must be configurable.

Future Dashboard must be able to change providers without changing code.

--------------------------------------------------

FAILOVER

If Primary Provider fails

↓

Log failure

↓

Mark Provider DOWN

↓

Call Backup Provider

↓

Return data

Do NOT require Collector changes.

--------------------------------------------------

HEALTH CHECK

Define

ONLINE

DOWN

RATE_LIMITED

INVALID_KEY

TIMEOUT

UNKNOWN

--------------------------------------------------

DATABASE

Design the SQLite tables required for

api_provider

api_health

api_logs

Do NOT implement.

--------------------------------------------------

OUTPUT

Create

project_documentation/API_MANAGER_ARCHITECTURE.md

Include

Architecture Diagram

Class Responsibilities

Sequence Diagram

Database Design

Provider Selection Logic

Health Check Logic

Future Dashboard Integration

Future API Expansion

No Python.

No SQL.

Documentation only.

--------------------------------------------------

VERIFY

Confirm

1. Only API_MANAGER_ARCHITECTURE.md created.

2. No Python modified.

3. No Database modified.

4. No SQLite modified.

5. Documentation only.

Print final verification report.