"""Unit tests for research_database.repositories.market_news_repository.
Uses an isolated, temp-file-backed database via the existing,
unmodified DatabaseInitializer -- never the real project database
file, mirroring tests/database/test_market_technical_repositories.py's
established pattern exactly.
"""

import os
import tempfile
import unittest

from research_database.database_manager import DatabaseManager
from research_database.repositories.company_repository import CompanyRepository
from research_database.repositories.market_news_repository import MarketNewsRepository
from research_database.repositories.sector_repository import SectorRepository
from research_database.schema.company import Company
from research_database.schema.market_news import MarketNewsItem
from research_database.schema.sector import Sector
from tests.database.test_market_technical_repositories import (
    close_isolated_database_manager,
    make_isolated_database_manager,
)


class TestMarketNewsRepository(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manager = make_isolated_database_manager()
        sector = SectorRepository(cls.manager).get_or_create(
            Sector(
                id=0,
                name="Technology",
                size="",
                growth_trend="",
                dynamics_summary="",
                regulatory_environment="",
                benchmark_summary="",
            )
        )
        cls.company = CompanyRepository(cls.manager).create(
            Company(
                id=0,
                legal_name="Infosys Limited",
                common_name="Infosys Limited",
                registration_details="",
                incorporation_country="IN",
                headquarters_location="",
                founding_date="",
                website="",
                stock_exchanges=["NSE"],
                ticker_symbols=["INFY.NS"],
                business_description="",
                mission="",
                industry="",
                sector_id=sector.id,
                business_model_summary="",
                geographic_footprint=[],
                customer_segments=[],
            )
        )

    @classmethod
    def tearDownClass(cls):
        close_isolated_database_manager(cls.manager)

    def setUp(self):
        self.repository = MarketNewsRepository(self.manager)

    def tearDown(self):
        self.manager.execute("DELETE FROM market_news")
        self.manager.commit()

    def _item(self, **overrides) -> MarketNewsItem:
        defaults = dict(
            id=0,
            company_id=self.company.id,
            headline="Infosys wins large multi-year deal",
            event_date="2026-07-10T09:00:00+00:00",
            summary="Infosys announced a new multi-year outsourcing deal.",
            extracted_facts=["NewsAPI (Primary)", "Economic Times"],
            url="https://example.com/infosys-deal",
        )
        defaults.update(overrides)
        return MarketNewsItem(**defaults)

    def test_create_and_get_by_id_round_trips(self):
        created = self.repository.create(self._item())
        fetched = self.repository.get_by_id(created.id)

        self.assertEqual(fetched.headline, "Infosys wins large multi-year deal")
        self.assertEqual(fetched.event_date, "2026-07-10T09:00:00+00:00")
        self.assertEqual(
            fetched.summary, "Infosys announced a new multi-year outsourcing deal."
        )
        self.assertEqual(fetched.extracted_facts, ["NewsAPI (Primary)", "Economic Times"])
        self.assertEqual(fetched.url, "https://example.com/infosys-deal")

    def test_get_by_id_returns_none_when_missing(self):
        self.assertIsNone(self.repository.get_by_id(999))

    def test_list_by_company_returns_only_that_company_s_news(self):
        self.repository.create(self._item(headline="First article"))
        self.repository.create(self._item(headline="Second article"))
        items = self.repository.list_by_company(self.company.id)
        self.assertEqual(len(items), 2)
        self.assertEqual({item.headline for item in items}, {"First article", "Second article"})

    def test_extracted_facts_defaults_to_empty_list_when_blank(self):
        created = self.repository.create(self._item(extracted_facts=[]))
        fetched = self.repository.get_by_id(created.id)
        self.assertEqual(fetched.extracted_facts, [])

    def test_url_defaults_to_empty_string_when_blank(self):
        created = self.repository.create(self._item(url=""))
        fetched = self.repository.get_by_id(created.id)
        self.assertEqual(fetched.url, "")

    def test_url_with_query_string_and_unicode_round_trips_byte_for_byte(self):
        exact_url = "https://example.com/a?id=123&ref=abc%20def&tag=%E2%9C%93#section-2"
        created = self.repository.create(self._item(url=exact_url))
        fetched = self.repository.get_by_id(created.id)
        self.assertEqual(fetched.url, exact_url)


class TestMarketNewsRepositoryMigratesALegacyTable(unittest.TestCase):
    """Proves the exact real-world scenario this change must handle:
    the project's own market_news table already existed (created before
    IMP-10F's url column) with no `url` column at all -- confirmed live
    via `PRAGMA table_info(market_news)` against the real project
    database during this phase. This test recreates that condition from
    scratch (a bare database with only a pre-url-column market_news
    table, never run through DatabaseInitializer -- which would create
    every table, including market_news, with the current, already-
    migrated column set) and proves MarketNewsRepository still reads
    and writes correctly, migrating the column itself on first use."""

    def setUp(self):
        fd, self._db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        os.remove(self._db_path)
        self.manager = DatabaseManager(self._db_path)
        self.manager.execute(
            "CREATE TABLE market_news ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, company_id INTEGER, "
            "headline TEXT, event_date TEXT, summary TEXT, extracted_facts TEXT)"
        )
        self.manager.commit()

    def tearDown(self):
        self.manager.close()
        if os.path.exists(self._db_path):
            os.remove(self._db_path)

    def test_pragma_confirms_url_column_is_missing_before_first_use(self):
        columns = {row["name"] for row in self.manager.fetch_all("PRAGMA table_info(market_news)")}
        self.assertNotIn("url", columns)

    def test_create_and_read_back_succeed_against_the_legacy_table(self):
        repository = MarketNewsRepository(self.manager)
        created = repository.create(
            MarketNewsItem(
                id=0,
                company_id=1,
                headline="Legacy-table migration check",
                event_date="2026-07-11T00:00:00+00:00",
                summary="Proves the url column is added on first use.",
                extracted_facts=[],
                url="https://example.com/legacy-migration-check",
            )
        )
        fetched = repository.get_by_id(created.id)

        self.assertEqual(fetched.url, "https://example.com/legacy-migration-check")

        columns = {row["name"] for row in self.manager.fetch_all("PRAGMA table_info(market_news)")}
        self.assertIn("url", columns)


if __name__ == "__main__":
    unittest.main()
