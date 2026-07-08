"""
Database Manager

Single entry point for all database operations used by the Knowledge Viewer.
"""

import json

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
        """Search for a company by (case-insensitive, partial) legal or
        common name."""
        db = self.connection.open()
        cursor = db.execute(
            "SELECT company.legal_name, company.common_name, company.industry, "
            "company.incorporation_country, company.headquarters_location, "
            "company.stock_exchanges, company.ticker_symbols, "
            "sector.name AS sector_name, metadata.last_updated_at AS last_updated "
            "FROM company "
            "LEFT JOIN sector ON sector.id = company.sector_id "
            "LEFT JOIN metadata ON metadata.company_id = company.id "
            "WHERE company.legal_name LIKE ? OR company.common_name LIKE ? "
            "ORDER BY company.common_name LIMIT 1",
            (f"%{name}%", f"%{name}%"),
        )
        row = cursor.fetchone()
        if row is None:
            return None

        result = dict(row)
        result["stock_exchanges"] = ", ".join(json.loads(result["stock_exchanges"] or "[]"))
        result["ticker_symbols"] = ", ".join(json.loads(result["ticker_symbols"] or "[]"))
        return result

    def get_statistics(self) -> dict:
        """Return database statistics for the viewer's Statistics screen."""
        db = self.connection.open()

        total_companies = db.execute(
            "SELECT COUNT(*) AS count FROM company"
        ).fetchone()["count"]

        total_sectors = db.execute(
            "SELECT COUNT(*) AS count FROM sector"
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
