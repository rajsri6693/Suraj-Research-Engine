"""
Sample Data Seeder

Inserts realistic sample company records so the Knowledge Viewer can be
tested against real data. For testing purposes only — not a research
ingestion path.
"""

from datetime import datetime, timezone

from research_database.database_connection import DatabaseConnection

SAMPLE_COMPANIES = [
    {
        "name": "BEL",
        "sector": "Defense & Aerospace",
        "industry": "Defense Electronics",
        "market_cap": "INR 2,10,000 Cr",
        "country": "India",
        "exchange": "NSE, BSE",
    },
    {
        "name": "HAL",
        "sector": "Defense & Aerospace",
        "industry": "Aircraft & Defense Equipment",
        "market_cap": "INR 3,00,000 Cr",
        "country": "India",
        "exchange": "NSE, BSE",
    },
    {
        "name": "Infosys",
        "sector": "Information Technology",
        "industry": "IT Services & Consulting",
        "market_cap": "INR 6,20,000 Cr",
        "country": "India",
        "exchange": "NSE, BSE",
    },
]


class SampleDataSeeder:
    """Seeds the companies table with sample records for viewer testing."""

    def __init__(self, connection: DatabaseConnection) -> None:
        self.connection = connection

    def seed(self) -> None:
        """Insert sample companies if the companies table is empty."""
        db = self.connection.open()
        count = db.execute(
            "SELECT COUNT(*) AS count FROM companies"
        ).fetchone()["count"]

        if count > 0:
            return

        last_updated = datetime.now(timezone.utc).isoformat()

        for company in SAMPLE_COMPANIES:
            db.execute(
                "INSERT OR IGNORE INTO companies "
                "(name, sector, industry, market_cap, country, exchange, last_updated) "
                "VALUES (:name, :sector, :industry, :market_cap, :country, :exchange, :last_updated)",
                {**company, "last_updated": last_updated},
            )

        db.commit()
