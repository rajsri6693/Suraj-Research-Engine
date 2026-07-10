"""Unit tests for
research_database.repositories.financial_information_repository. Uses
an isolated, temp-file-backed database via the existing, unmodified
DatabaseInitializer -- never the real project database file.

Schema initialization (~7s for the existing DatabaseInitializer's 17
tables) happens once per class, matching
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
from research_database.repositories.financial_information_repository import (
    FinancialInformationRepository,
)
from research_database.repositories.sector_repository import SectorRepository
from research_database.schema.company import Company
from research_database.schema.financial_information import FinancialRecord
from research_database.schema.sector import Sector


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


class TestFinancialInformationRepository(unittest.TestCase):
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
                headquarters_location="Bangalore, Karnataka, IN",
                founding_date="",
                website="https://www.infosys.com",
                stock_exchanges=["NSE"],
                ticker_symbols=["INFY.NS"],
                business_description="",
                mission="",
                industry="IT Services",
                sector_id=sector.id,
                business_model_summary="",
                geographic_footprint=["IN"],
                customer_segments=[],
            )
        )

    @classmethod
    def tearDownClass(cls):
        close_isolated_database_manager(cls.manager)

    def setUp(self):
        self.repository = FinancialInformationRepository(self.manager)

    def tearDown(self):
        self.manager.execute("DELETE FROM financial_information")
        self.manager.execute("DELETE FROM company WHERE legal_name = 'Other Corp'")
        self.manager.commit()

    def _record(self, **overrides) -> FinancialRecord:
        defaults = dict(
            id=0,
            company_id=self.company.id,
            reporting_period="FY2025",
            currency="INR",
            revenue=1_000_000.0,
            profit=200_000.0,
            gross_margin=0.5,
            operating_margin=0.3,
            net_margin=0.2,
            balance_sheet_summary="",
            cash_flow_summary="",
            key_ratios={"peRatio": 21.6, "currentRatio": 0.89},
        )
        defaults.update(overrides)
        return FinancialRecord(**defaults)

    def test_create_assigns_an_id_and_round_trips_every_field(self):
        created = self.repository.create(self._record())
        fetched = self.repository.get_by_id(created.id)
        self.assertEqual(fetched.company_id, self.company.id)
        self.assertEqual(fetched.reporting_period, "FY2025")
        self.assertEqual(fetched.revenue, 1_000_000.0)
        self.assertEqual(fetched.profit, 200_000.0)

    def test_key_ratios_dict_round_trips_through_json(self):
        created = self.repository.create(self._record())
        fetched = self.repository.get_by_id(created.id)
        self.assertEqual(fetched.key_ratios, {"peRatio": 21.6, "currentRatio": 0.89})

    def test_empty_key_ratios_round_trips_as_empty_dict(self):
        created = self.repository.create(self._record(key_ratios={}))
        fetched = self.repository.get_by_id(created.id)
        self.assertEqual(fetched.key_ratios, {})

    def test_get_by_id_returns_none_when_missing(self):
        self.assertIsNone(self.repository.get_by_id(999))

    def test_list_by_company_returns_only_that_company_s_records(self):
        self.repository.create(self._record(reporting_period="FY2024"))
        self.repository.create(self._record(reporting_period="FY2025"))
        records = self.repository.list_by_company(self.company.id)
        self.assertEqual(len(records), 2)
        self.assertEqual(
            {record.reporting_period for record in records}, {"FY2024", "FY2025"}
        )

    def test_list_by_company_excludes_other_companies(self):
        other_company = CompanyRepository(self.manager).create(
            Company(
                id=0,
                legal_name="Other Corp",
                common_name="Other Corp",
                registration_details="",
                incorporation_country="US",
                headquarters_location="",
                founding_date="",
                website="",
                stock_exchanges=[],
                ticker_symbols=[],
                business_description="",
                mission="",
                industry="",
                sector_id=self.company.sector_id,
                business_model_summary="",
                geographic_footprint=[],
                customer_segments=[],
            )
        )
        self.repository.create(self._record(company_id=self.company.id))
        self.repository.create(self._record(company_id=other_company.id))
        self.assertEqual(len(self.repository.list_by_company(self.company.id)), 1)


if __name__ == "__main__":
    unittest.main()
