"""
Database Health Check

Verifies database connectivity, schema presence, and file size.
"""

import os

from research_database.database_connection import DatabaseConnection
from research_database.database_initializer import DatabaseInitializer


class DatabaseHealthCheck:
    """Verifies database integrity and health."""

    def __init__(self, connection: DatabaseConnection) -> None:
        self.connection = connection

    def run_check(self) -> dict:
        """Run integrity checks and return a health report."""
        connected = False
        schema_loaded = False

        try:
            db = self.connection.open()
            connected = True

            cursor = db.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
            existing_tables = {row["name"] for row in cursor.fetchall()}
            required_tables = set(DatabaseInitializer(self.connection).tables())
            schema_loaded = required_tables.issubset(existing_tables)
        except Exception:
            connected = False

        db_path = self.connection.db_path
        file_size_bytes = os.path.getsize(db_path) if os.path.exists(db_path) else 0

        return {
            "connected": connected,
            "schema_loaded": schema_loaded,
            "file_size_bytes": file_size_bytes,
        }
