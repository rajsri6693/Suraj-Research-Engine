"""
Database Connection

SQLite connection manager. Owns opening, closing, and configuring the
single SQLite connection used by the rest of the database layer.
"""

import os
import sqlite3

DEFAULT_DB_PATH = os.path.join(
    os.path.dirname(__file__), "data", "knowledge.db"
)


class DatabaseConnection:
    """Manages the SQLite connection lifecycle."""

    def __init__(self, db_path: str = DEFAULT_DB_PATH) -> None:
        self.db_path = db_path
        self._connection: sqlite3.Connection | None = None

    def open(self) -> sqlite3.Connection:
        """Open the SQLite connection, creating the parent directory if needed."""
        if self._connection is None:
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            connection = sqlite3.connect(self.db_path)
            connection.row_factory = sqlite3.Row
            connection.execute("PRAGMA foreign_keys = ON")
            self._connection = connection
        return self._connection

    def close(self) -> None:
        """Close the database connection, if one is open."""
        if self._connection is not None:
            self._connection.close()
            self._connection = None

    @property
    def connection(self) -> sqlite3.Connection:
        """Return the open connection, opening it if necessary."""
        return self.open()

    def __enter__(self) -> sqlite3.Connection:
        return self.open()

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()
