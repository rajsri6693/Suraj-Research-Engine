"""
Database Manager

The single gateway between the application and SQLite. Owns the
connection lifecycle, transaction handling, and the generic execute and
query primitives that higher-level modules are built on. Contains no
entity-specific logic — CRUD for individual entities (Company, Sector,
Market News, etc.) belongs to future modules built on top of this one.
"""

import sqlite3

from research_database.database_connection import DatabaseConnection


class DatabaseError(Exception):
    """Raised when a database operation fails."""


class DatabaseManager:
    """Sole gateway to SQLite: connection lifecycle, transactions, and
    generic execute/query helpers."""

    def __init__(self, db_path: str | None = None) -> None:
        self.connection = (
            DatabaseConnection(db_path) if db_path else DatabaseConnection()
        )

    def connect(self) -> None:
        """Open the database connection."""
        self.connection.open()

    def close(self) -> None:
        """Close the database connection."""
        self.connection.close()

    def execute(self, sql: str, params: tuple | dict = ()) -> sqlite3.Cursor:
        """Run a single statement (DDL, insert, update, delete, or
        select) and return its cursor."""
        db = self.connection.open()
        try:
            return db.execute(sql, params)
        except sqlite3.Error as error:
            raise DatabaseError(str(error)) from error

    def execute_many(self, sql: str, params_list) -> sqlite3.Cursor:
        """Run the same statement against a sequence of parameter sets."""
        db = self.connection.open()
        try:
            return db.executemany(sql, params_list)
        except sqlite3.Error as error:
            raise DatabaseError(str(error)) from error

    def fetch_one(self, sql: str, params: tuple | dict = ()) -> dict | None:
        """Run a query and return the first row as a plain dict, or None."""
        cursor = self.execute(sql, params)
        row = cursor.fetchone()
        return dict(row) if row is not None else None

    def fetch_all(self, sql: str, params: tuple | dict = ()) -> list[dict]:
        """Run a query and return every row as a list of plain dicts."""
        cursor = self.execute(sql, params)
        return [dict(row) for row in cursor.fetchall()]

    def commit(self) -> None:
        """Commit the current transaction."""
        try:
            self.connection.connection.commit()
        except sqlite3.Error as error:
            raise DatabaseError(str(error)) from error

    def rollback(self) -> None:
        """Roll back the current transaction."""
        try:
            self.connection.connection.rollback()
        except sqlite3.Error as error:
            raise DatabaseError(str(error)) from error

    def transaction(self) -> "_Transaction":
        """Return a context manager that commits on success and rolls
        back if an exception is raised inside it."""
        return _Transaction(self)


class _Transaction:
    """Context manager implementing commit-on-success, rollback-on-error."""

    def __init__(self, manager: DatabaseManager) -> None:
        self.manager = manager

    def __enter__(self) -> DatabaseManager:
        self.manager.connect()
        return self.manager

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        if exc_type is None:
            self.manager.commit()
        else:
            self.manager.rollback()
        return False
