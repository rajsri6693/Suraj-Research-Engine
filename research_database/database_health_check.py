"""
Database Health Check

Verifies database connectivity, schema presence, and file size.
"""

import os

from research_database.database_initializer import DatabaseInitializer
from research_database.database_manager import DatabaseManager


class DatabaseHealthCheck:
    """Verifies database integrity and health."""

    def __init__(self, manager: DatabaseManager) -> None:
        self.manager = manager

    def run_check(self) -> dict:
        """Run integrity checks and return a health report."""
        connected = False
        schema_loaded = False

        try:
            self.manager.connect()
            connected = True

            rows = self.manager.fetch_all(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
            existing_tables = {row["name"] for row in rows}
            required_tables = set(DatabaseInitializer(self.manager).tables())
            schema_loaded = required_tables.issubset(existing_tables)
        except Exception:
            connected = False

        db_path = self.manager.connection.db_path
        file_size_bytes = os.path.getsize(db_path) if os.path.exists(db_path) else 0

        return {
            "connected": connected,
            "schema_loaded": schema_loaded,
            "file_size_bytes": file_size_bytes,
        }
