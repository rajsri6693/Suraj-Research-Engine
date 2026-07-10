"""Schema audit for the API Manager's own SQLite configuration layer
(research_database/api_manager_schema.py), per
project_documentation/API_MANAGER_ARCHITECTURE.md Section 10.

Confirms this initializer is completely isolated from the Phase 01
Verified Knowledge Database's 17-table schema
(research_database/database_initializer.py) -- it creates exactly
api_provider, api_health, api_logs, never touches schema_version, and
uses its own temp-file-backed database, never the real project
database file.
"""

import os
import tempfile
import unittest

from research_database.api_manager_schema import (
    SCHEMA_MODULES,
    ApiManagerDatabaseInitializer,
)
from research_database.database_manager import DatabaseManager


def make_isolated_database_manager() -> DatabaseManager:
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    os.remove(db_path)  # DatabaseManager creates it on first use.
    manager = DatabaseManager(db_path)
    manager.audit_db_path = db_path  # type: ignore[attr-defined]
    return manager


def close_isolated_database_manager(manager: DatabaseManager) -> None:
    manager.close()
    db_path = getattr(manager, "audit_db_path", None)
    if db_path and os.path.exists(db_path):
        os.remove(db_path)


def table_names(manager: DatabaseManager) -> set:
    rows = manager.fetch_all(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
    )
    return {row["name"] for row in rows}


def table_info(manager: DatabaseManager, table: str):
    return manager.fetch_all(f"PRAGMA table_info({table})")


class TestApiManagerSchemaInitialization(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manager = make_isolated_database_manager()
        cls.initializer = ApiManagerDatabaseInitializer(cls.manager)
        cls.initializer.initialize()

    @classmethod
    def tearDownClass(cls):
        close_isolated_database_manager(cls.manager)

    def test_exactly_three_tables_are_reported(self):
        self.assertEqual(
            set(self.initializer.tables()), {"api_provider", "api_health", "api_logs"}
        )

    def test_all_three_tables_actually_exist(self):
        existing = table_names(self.manager)
        for table in ("api_provider", "api_health", "api_logs"):
            self.assertIn(table, existing)

    def test_does_not_create_a_schema_version_table(self):
        """Unlike the Phase 01 Verified Knowledge Database, this
        initializer never writes a schema_version row -- it is a
        separate, self-contained configuration layer."""
        self.assertNotIn("schema_version", table_names(self.manager))

    def test_no_other_stray_tables_are_created(self):
        self.assertEqual(table_names(self.manager), {"api_provider", "api_health", "api_logs"})

    def test_api_provider_columns_match_schema_fields(self):
        columns = {row["name"] for row in table_info(self.manager, "api_provider")}
        self.assertEqual(
            columns, {"id", "provider_name", "category", "role", "key_env_var", "active"}
        )

    def test_api_health_columns_match_schema_fields(self):
        columns = {row["name"] for row in table_info(self.manager, "api_health")}
        self.assertEqual(
            columns,
            {
                "id",
                "provider_id",
                "status",
                "last_health_check",
                "response_time_ms",
                "last_error",
                "consecutive_failures",
            },
        )

    def test_api_logs_columns_match_schema_fields(self):
        columns = {row["name"] for row in table_info(self.manager, "api_logs")}
        self.assertEqual(
            columns,
            {
                "id",
                "timestamp",
                "category",
                "operation",
                "collector_name",
                "provider_id",
                "role_attempted",
                "served_by",
                "outcome",
                "health_status",
                "response_time_ms",
            },
        )

    def test_id_is_the_integer_primary_key_on_every_table(self):
        for table in self.initializer.tables():
            id_column = next(row for row in table_info(self.manager, table) if row["name"] == "id")
            self.assertEqual(id_column["pk"], 1)


class TestInitializationIsIdempotent(unittest.TestCase):
    def test_calling_initialize_twice_does_not_error_or_duplicate_tables(self):
        manager = make_isolated_database_manager()
        try:
            initializer = ApiManagerDatabaseInitializer(manager)
            initializer.initialize()
            initializer.initialize()
            self.assertEqual(
                table_names(manager), {"api_provider", "api_health", "api_logs"}
            )
        finally:
            close_isolated_database_manager(manager)


class TestSchemaModulesTuple(unittest.TestCase):
    def test_exactly_three_schema_modules_registered(self):
        self.assertEqual(len(SCHEMA_MODULES), 3)


if __name__ == "__main__":
    unittest.main()
