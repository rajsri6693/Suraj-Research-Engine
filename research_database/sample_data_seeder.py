"""
Sample Data Seeder

Inserts realistic sample company records so the Knowledge Viewer can be
tested against real data. For testing purposes only — not a research
ingestion path.
"""

import json
from datetime import datetime, timezone

from research_database.database_connection import DatabaseConnection

SAMPLE_SECTORS = [
    "Defense & Aerospace",
    "Information Technology",
]

SAMPLE_COMPANIES = [
    {
        "legal_name": "Bharat Electronics Limited",
        "common_name": "BEL",
        "incorporation_country": "India",
        "headquarters_location": "Bengaluru, India",
        "industry": "Defense Electronics",
        "sector_name": "Defense & Aerospace",
        "stock_exchanges": ["NSE", "BSE"],
        "ticker_symbols": ["BEL"],
    },
    {
        "legal_name": "Hindustan Aeronautics Limited",
        "common_name": "HAL",
        "incorporation_country": "India",
        "headquarters_location": "Bengaluru, India",
        "industry": "Aircraft & Defense Equipment",
        "sector_name": "Defense & Aerospace",
        "stock_exchanges": ["NSE", "BSE"],
        "ticker_symbols": ["HAL"],
    },
    {
        "legal_name": "Infosys Limited",
        "common_name": "Infosys",
        "incorporation_country": "India",
        "headquarters_location": "Bengaluru, India",
        "industry": "IT Services & Consulting",
        "sector_name": "Information Technology",
        "stock_exchanges": ["NSE", "BSE"],
        "ticker_symbols": ["INFY"],
    },
]


class SampleDataSeeder:
    """Seeds the company table (and its required Sector/Metadata records)
    with sample records for viewer testing."""

    def __init__(self, connection: DatabaseConnection) -> None:
        self.connection = connection

    def seed(self) -> None:
        """Insert sample sector, company, and metadata records if the
        company table is empty."""
        db = self.connection.open()
        count = db.execute("SELECT COUNT(*) AS count FROM company").fetchone()["count"]

        if count > 0:
            return

        sector_ids = self._seed_sectors(db)
        self._seed_companies(db, sector_ids)

        db.commit()

    def _seed_sectors(self, db) -> dict:
        sector_ids = {}
        for sector_name in SAMPLE_SECTORS:
            cursor = db.execute(
                "INSERT INTO sector "
                "(name, size, growth_trend, dynamics_summary, regulatory_environment, "
                "benchmark_summary) VALUES (?, '', '', '', '', '')",
                (sector_name,),
            )
            sector_ids[sector_name] = cursor.lastrowid
        return sector_ids

    def _seed_companies(self, db, sector_ids: dict) -> None:
        now = datetime.now(timezone.utc).isoformat()

        for company in SAMPLE_COMPANIES:
            cursor = db.execute(
                "INSERT INTO company ("
                "legal_name, common_name, registration_details, incorporation_country, "
                "headquarters_location, founding_date, website, stock_exchanges, "
                "ticker_symbols, business_description, mission, industry, sector_id, "
                "business_model_summary, geographic_footprint, customer_segments"
                ") VALUES (?, ?, '', ?, ?, '', '', ?, ?, '', '', ?, ?, '', '[]', '[]')",
                (
                    company["legal_name"],
                    company["common_name"],
                    company["incorporation_country"],
                    company["headquarters_location"],
                    json.dumps(company["stock_exchanges"]),
                    json.dumps(company["ticker_symbols"]),
                    company["industry"],
                    sector_ids[company["sector_name"]],
                ),
            )
            company_id = cursor.lastrowid

            db.execute(
                "INSERT INTO metadata ("
                "company_id, created_at, last_verified_at, last_updated_at, "
                "verification_status, revision_number, section_completeness"
                ") VALUES (?, ?, ?, ?, ?, ?, ?)",
                (company_id, now, now, now, "verified", 1, json.dumps({})),
            )
