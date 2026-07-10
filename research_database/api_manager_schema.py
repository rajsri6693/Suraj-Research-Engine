"""
API Manager Database Initializer

Creates the API Manager's own SQLite configuration layer -- api_provider,
api_health, api_logs -- per
project_documentation/API_MANAGER_ARCHITECTURE.md Section 10. Kept
entirely separate from database_initializer.py's Verified Knowledge
Database: that module owns a fixed set of 17 knowledge-entity tables
(DATABASE_ARCHITECTURE.md) plus its own schema_version table, and
tests/database/test_database_audit.py asserts that count directly. The
API Manager's tables are operational gateway configuration, not
verified company knowledge, so this module never touches
database_initializer.py's SCHEMA_MODULES, never writes to its
schema_version table, and by default uses its own database file
(data/api_manager.db) rather than verified_knowledge.db.
"""

import dataclasses
import os
from typing import get_origin

from research_database.database_manager import DatabaseManager
from research_database.schema import api_health, api_logs, api_provider

DEFAULT_API_MANAGER_DB_PATH = os.path.join(os.path.dirname(__file__), "data", "api_manager.db")

SCHEMA_MODULES = (api_provider, api_health, api_logs)

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


class ApiManagerDatabaseInitializer:
    """Initializes the API Manager's own SQLite file and its three
    tables -- never touches the Verified Knowledge Database file or
    its schema_version table."""

    def __init__(self, manager: DatabaseManager) -> None:
        self.manager = manager

    def initialize(self) -> None:
        """Create every API Manager table if it does not already exist."""
        for schema_module in SCHEMA_MODULES:
            self.manager.execute(_create_table_sql(schema_module))
        self.manager.commit()

    def tables(self) -> list[str]:
        """Return the list of table names this initializer is responsible for."""
        return [_table_name(module) for module in SCHEMA_MODULES]


def initialize_api_manager_database(db_path: str | None = None) -> DatabaseManager:
    """Open the API Manager's database connection and ensure its
    database file and three tables exist. Safe to call on every
    startup, since table creation is idempotent."""
    manager = DatabaseManager(db_path or DEFAULT_API_MANAGER_DB_PATH)
    ApiManagerDatabaseInitializer(manager).initialize()
    return manager
