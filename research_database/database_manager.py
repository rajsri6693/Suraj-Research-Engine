"""
Database Manager

Single entry point for all database operations used by the Knowledge Viewer.
"""

from research_database.database_connection import DatabaseConnection
from research_database.database_health_check import DatabaseHealthCheck
from research_database.database_initializer import DatabaseInitializer
from research_database.sample_data_seeder import SampleDataSeeder


class DatabaseManager:
    """Coordinates connection, initialization, and queries for the database."""

    def __init__(self, db_path: str | None = None) -> None:
        self.connection = (
            DatabaseConnection(db_path) if db_path else DatabaseConnection()
        )
        self.initializer = DatabaseInitializer(self.connection)
        self.health_checker = DatabaseHealthCheck(self.connection)
        self.seeder = SampleDataSeeder(self.connection)

    def connect(self) -> None:
        """Establish the database connection."""
        self.connection.open()

    def initialize(self) -> None:
        """Initialize database structures (create tables if missing) and seed sample data."""
        self.initializer.initialize()
        self.seeder.seed()

    def close(self) -> None:
        """Close the database connection."""
        self.connection.close()

    def search_company(self, name: str) -> dict | None:
        """Search for a company by (case-insensitive, partial) name."""
        db = self.connection.open()
        cursor = db.execute(
            "SELECT id, name, sector, industry, market_cap, country, exchange, "
            "last_updated FROM companies WHERE name LIKE ? ORDER BY name LIMIT 1",
            (f"%{name}%",),
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_statistics(self) -> dict:
        """Return database statistics for the viewer's Statistics screen."""
        db = self.connection.open()

        total_companies = db.execute(
            "SELECT COUNT(*) AS count FROM companies"
        ).fetchone()["count"]

        total_sectors = db.execute(
            "SELECT COUNT(DISTINCT sector) AS count FROM companies "
            "WHERE sector IS NOT NULL AND sector != ''"
        ).fetchone()["count"]

        version_row = db.execute(
            "SELECT version FROM schema_version WHERE id = 1"
        ).fetchone()
        database_version = version_row["version"] if version_row else "unknown"

        return {
            "total_companies": total_companies,
            "total_sectors": total_sectors,
            "database_version": database_version,
        }

    def health_check(self) -> dict:
        """Run and return the database health report."""
        return self.health_checker.run_check()
