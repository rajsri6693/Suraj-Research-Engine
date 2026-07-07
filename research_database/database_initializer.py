"""
Database Initializer

Creates the database file (if needed) and applies every required schema.
"""

from research_database.database_connection import DatabaseConnection
from research_database.schema import (
    cache_schema,
    company_schema,
    raw_research_schema,
    research_history_schema,
    verified_research_schema,
)

SCHEMA_VERSION = "1.0.0"

SCHEMA_MODULES = (
    raw_research_schema,
    verified_research_schema,
    research_history_schema,
    cache_schema,
    company_schema,
)

CREATE_SCHEMA_VERSION_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS schema_version (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    version TEXT NOT NULL
)
"""


class DatabaseInitializer:
    """Initializes database files and structure."""

    def __init__(self, connection: DatabaseConnection) -> None:
        self.connection = connection

    def initialize(self) -> None:
        """Create every required table if it does not already exist."""
        db = self.connection.open()

        for schema_module in SCHEMA_MODULES:
            db.execute(schema_module.CREATE_TABLE_SQL)

        db.execute(CREATE_SCHEMA_VERSION_TABLE_SQL)
        db.execute(
            "INSERT OR IGNORE INTO schema_version (id, version) VALUES (1, ?)",
            (SCHEMA_VERSION,),
        )
        db.commit()

    def tables(self) -> list[str]:
        """Return the list of table names this initializer is responsible for."""
        return [schema_module.TABLE_NAME for schema_module in SCHEMA_MODULES]
