"""
API Provider Schema

Logical schema for the API Provider entity, per
project_documentation/API_MANAGER_ARCHITECTURE.md Section 5.3 and
Section 10.1. One row per Category role -- five providers produce six
rows, since Finnhub holds two roles (Backup for Fundamental Data,
Backup for News), per Section 2.

This is the API Manager's own configuration table, kept separate from
the Verified Knowledge Database's entity tables (DATABASE_ARCHITECTURE.md)
-- see research_database/api_manager_schema.py, which initializes this
table in its own database file rather than registering it alongside
database_initializer.py's 17 knowledge entities.
"""

from dataclasses import dataclass


@dataclass
class ApiProvider:
    """Represents one Category-role registration -- a provider name,
    the Category it applies to, its Role (Primary/Backup) within that
    Category, and the name of the .env variable holding its key.

    Purpose: the persisted form of the API Registry's Category ->
    Primary Provider -> Backup Provider mapping, per Section 5.2. Never
    holds live status -- that belongs to ApiHealth.
    """

    id: int  # Unique identifier for this Category-role row.
    provider_name: str  # One of the five providers (FMP, Finnhub, Alpha Vantage, Twelve Data, NewsAPI).
    category: str  # One of the three Categories (Fundamental Data, Market & Technical, News).
    role: str  # Primary or Backup within this Category.
    key_env_var: str  # Name of the .env variable holding this provider's API key -- never the key value itself.
    active: bool  # Whether this Category-role row is currently enabled.
