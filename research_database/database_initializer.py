"""
Database Initializer

Creates the Verified Knowledge Database file (if needed) and applies every
entity schema defined in research_database/schema/, generating each table
automatically from its dataclass fields.
"""

import dataclasses
from typing import get_origin

from research_database.database_connection import DatabaseConnection
from research_database.schema import (
    company,
    competitors,
    corporate_actions,
    financial_information,
    government_policies,
    management,
    market_data,
    market_news,
    metadata,
    orders_contracts,
    price_history,
    products_services,
    risks,
    sector,
    shareholding,
    sources,
    technical_analysis,
)

SCHEMA_VERSION = "1.0.0"

SCHEMA_MODULES = (
    sector,
    company,
    products_services,
    management,
    shareholding,
    financial_information,
    orders_contracts,
    competitors,
    risks,
    market_news,
    government_policies,
    market_data,
    price_history,
    technical_analysis,
    corporate_actions,
    sources,
    metadata,
)

CREATE_SCHEMA_VERSION_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS schema_version (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    version TEXT NOT NULL
)
"""

_SQL_TYPE_BY_PYTHON_TYPE = {
    int: "INTEGER",
    float: "REAL",
    bool: "INTEGER",
    str: "TEXT",
}


def _table_name(module) -> str:
    """Derive a table name from a schema module's own module name."""
    return module.__name__.rsplit(".", 1)[-1]


def _entity_dataclass(module):
    """Find the single dataclass defined in a schema module."""
    for value in vars(module).values():
        if dataclasses.is_dataclass(value) and value.__module__ == module.__name__:
            return value
    raise ValueError(f"No dataclass found in schema module {module.__name__}")


def _column_type(field_type) -> str:
    """Map a dataclass field type to a SQLite column type."""
    if get_origin(field_type) in (list, dict):
        return "TEXT"
    return _SQL_TYPE_BY_PYTHON_TYPE.get(field_type, "TEXT")


def _create_table_sql(module) -> str:
    """Build a CREATE TABLE statement from a schema module's dataclass fields."""
    table_name = _table_name(module)
    entity = _entity_dataclass(module)

    columns = []
    for entity_field in dataclasses.fields(entity):
        if entity_field.name == "id":
            columns.append("id INTEGER PRIMARY KEY AUTOINCREMENT")
        else:
            columns.append(f"{entity_field.name} {_column_type(entity_field.type)}")

    column_definitions = ",\n    ".join(columns)
    return f"CREATE TABLE IF NOT EXISTS {table_name} (\n    {column_definitions}\n)"


class DatabaseInitializer:
    """Initializes the database file and creates every entity table."""

    def __init__(self, connection: DatabaseConnection) -> None:
        self.connection = connection

    def initialize(self) -> None:
        """Create every entity table if it does not already exist."""
        db = self.connection.open()

        for schema_module in SCHEMA_MODULES:
            db.execute(_create_table_sql(schema_module))

        db.execute(CREATE_SCHEMA_VERSION_TABLE_SQL)
        db.execute(
            "INSERT OR IGNORE INTO schema_version (id, version) VALUES (1, ?)",
            (SCHEMA_VERSION,),
        )
        db.commit()

    def tables(self) -> list[str]:
        """Return the list of table names this initializer is responsible for."""
        return [_table_name(module) for module in SCHEMA_MODULES]


def initialize_database(db_path: str | None = None) -> DatabaseConnection:
    """Open the database connection and ensure the database and its
    tables exist. Creates the database file and every entity table on
    first startup; safe to call on every subsequent startup, since table
    creation is idempotent.
    """
    connection = DatabaseConnection(db_path) if db_path else DatabaseConnection()
    DatabaseInitializer(connection).initialize()
    return connection
