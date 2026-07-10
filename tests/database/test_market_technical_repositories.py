"""Unit tests for research_database.repositories.market_data_repository,
price_history_repository, and technical_analysis_repository. Uses an
isolated, temp-file-backed database via the existing, unmodified
DatabaseInitializer -- never the real project database file.

Schema initialization (~7s for the existing DatabaseInitializer's 17
tables) happens once for the whole module, matching
tests/database/test_database_audit.py's own established pattern for
this exact reason; each test cleans up the rows it created afterward
so tests stay independent without re-paying that cost per test.
"""

import os
import tempfile
import unittest

from research_database.database_initializer import DatabaseInitializer
from research_database.database_manager import DatabaseManager
from research_database.repositories.company_repository import CompanyRepository
from research_database.repositories.market_data_repository import MarketDataRepository
from research_database.repositories.price_history_repository import PriceHistoryRepository
from research_database.repositories.sector_repository import SectorRepository
from research_database.repositories.technical_analysis_repository import (
    TechnicalAnalysisRepository,
)
from research_database.schema.company import Company
from research_database.schema.market_data import MarketDataSnapshot
from research_database.schema.price_history import HistoricalPrice
from research_database.schema.sector import Sector
from research_database.schema.technical_analysis import TechnicalIndicator


def make_isolated_database_manager() -> DatabaseManager:
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    os.remove(db_path)
    manager = DatabaseManager(db_path)
    manager.audit_db_path = db_path  # type: ignore[attr-defined]
    DatabaseInitializer(manager).initialize()
    return manager


def close_isolated_database_manager(manager: DatabaseManager) -> None:
    manager.close()
    db_path = getattr(manager, "audit_db_path", None)
    if db_path and os.path.exists(db_path):
        os.remove(db_path)


class _SharedCompanyFixture(unittest.TestCase):
    """Base class providing one shared isolated DB + Company row per
    test class, matching test_financial_information_repository.py's
    established pattern."""

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


class TestMarketDataRepository(_SharedCompanyFixture):
    def setUp(self):
        self.repository = MarketDataRepository(self.manager)

    def tearDown(self):
        self.manager.execute("DELETE FROM market_data")
        self.manager.commit()

    def _snapshot(self, **overrides) -> MarketDataSnapshot:
        defaults = dict(
            id=0,
            company_id=self.company.id,
            snapshot_timestamp="2026-07-09T10:00:00",
            current_price=1510.0,
            day_low=1490.0,
            day_high=1520.0,
            week_52_low=1200.0,
            week_52_high=1600.0,
            traded_volume=100_000,
            market_capitalization=6_000_000_000.0,
            currency="INR",
        )
        defaults.update(overrides)
        return MarketDataSnapshot(**defaults)

    def test_create_and_get_by_id_round_trips(self):
        created = self.repository.create(self._snapshot())
        fetched = self.repository.get_by_id(created.id)
        self.assertEqual(fetched.current_price, 1510.0)
        self.assertEqual(fetched.currency, "INR")

    def test_get_by_id_returns_none_when_missing(self):
        self.assertIsNone(self.repository.get_by_id(999))

    def test_list_by_company_returns_only_that_company_s_snapshots(self):
        self.repository.create(self._snapshot(snapshot_timestamp="t1"))
        self.repository.create(self._snapshot(snapshot_timestamp="t2"))
        snapshots = self.repository.list_by_company(self.company.id)
        self.assertEqual(len(snapshots), 2)


class TestPriceHistoryRepository(_SharedCompanyFixture):
    def setUp(self):
        self.repository = PriceHistoryRepository(self.manager)

    def tearDown(self):
        self.manager.execute("DELETE FROM price_history")
        self.manager.commit()

    def _record(self, **overrides) -> HistoricalPrice:
        defaults = dict(
            id=0,
            company_id=self.company.id,
            period_date="2026-07-09",
            open_price=1500.0,
            high_price=1520.0,
            low_price=1490.0,
            close_price=1510.0,
            volume=100_000,
        )
        defaults.update(overrides)
        return HistoricalPrice(**defaults)

    def test_create_and_get_by_id_round_trips(self):
        created = self.repository.create(self._record())
        fetched = self.repository.get_by_id(created.id)
        self.assertEqual(fetched.close_price, 1510.0)
        self.assertEqual(fetched.volume, 100_000)

    def test_create_many_inserts_a_whole_series(self):
        records = [
            self._record(period_date="2026-07-07"),
            self._record(period_date="2026-07-08"),
            self._record(period_date="2026-07-09"),
        ]
        created = self.repository.create_many(records)
        self.assertEqual(len(created), 3)
        self.assertEqual(len(self.repository.list_by_company(self.company.id)), 3)

    def test_list_by_company_ordered_by_period_date(self):
        self.repository.create(self._record(period_date="2026-07-09"))
        self.repository.create(self._record(period_date="2026-07-07"))
        self.repository.create(self._record(period_date="2026-07-08"))
        dates = [record.period_date for record in self.repository.list_by_company(self.company.id)]
        self.assertEqual(dates, ["2026-07-07", "2026-07-08", "2026-07-09"])

    def test_get_by_id_returns_none_when_missing(self):
        self.assertIsNone(self.repository.get_by_id(999))


class TestTechnicalAnalysisRepository(_SharedCompanyFixture):
    def setUp(self):
        self.price_repository = PriceHistoryRepository(self.manager)
        self.repository = TechnicalAnalysisRepository(self.manager)
        self.price_record = self.price_repository.create(
            HistoricalPrice(
                id=0,
                company_id=self.company.id,
                period_date="2026-07-09",
                open_price=1500.0,
                high_price=1520.0,
                low_price=1490.0,
                close_price=1510.0,
                volume=100_000,
            )
        )

    def tearDown(self):
        self.manager.execute("DELETE FROM technical_analysis")
        self.manager.execute("DELETE FROM price_history")
        self.manager.commit()

    def _indicator(self, **overrides) -> TechnicalIndicator:
        defaults = dict(
            id=0,
            company_id=self.company.id,
            price_history_id=self.price_record.id,
            indicator_name="RSI",
            indicator_value=63.86,
            computed_date="2026-07-09",
            lookback_period="14",
        )
        defaults.update(overrides)
        return TechnicalIndicator(**defaults)

    def test_create_and_get_by_id_round_trips(self):
        created = self.repository.create(self._indicator())
        fetched = self.repository.get_by_id(created.id)
        self.assertEqual(fetched.indicator_name, "RSI")
        self.assertEqual(fetched.indicator_value, 63.86)
        self.assertEqual(fetched.price_history_id, self.price_record.id)

    def test_get_by_id_returns_none_when_missing(self):
        self.assertIsNone(self.repository.get_by_id(999))

    def test_list_by_company_returns_only_that_company_s_indicators(self):
        self.repository.create(self._indicator(indicator_name="RSI"))
        self.repository.create(self._indicator(indicator_name="SMA-20"))
        indicators = self.repository.list_by_company(self.company.id)
        self.assertEqual(len(indicators), 2)
        self.assertEqual(
            {indicator.indicator_name for indicator in indicators}, {"RSI", "SMA-20"}
        )


if __name__ == "__main__":
    unittest.main()
