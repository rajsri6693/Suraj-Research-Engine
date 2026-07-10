"""Unit tests for research_database.repositories.sector_repository.
Uses an isolated, temp-file-backed database via the existing, unmodified
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
from research_database.repositories.sector_repository import SectorRepository
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


def _sector(**overrides) -> Sector:
    defaults = dict(
        id=0,
        name="Technology",
        size="Large",
        growth_trend="Growing",
        dynamics_summary="",
        regulatory_environment="",
        benchmark_summary="",
    )
    defaults.update(overrides)
    return Sector(**defaults)


class TestSectorRepository(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manager = make_isolated_database_manager()

    @classmethod
    def tearDownClass(cls):
        close_isolated_database_manager(cls.manager)

    def setUp(self):
        self.repository = SectorRepository(self.manager)

    def tearDown(self):
        self.manager.execute("DELETE FROM sector")
        self.manager.commit()

    def test_create_and_get_by_id_round_trips(self):
        created = self.repository.create(_sector())
        fetched = self.repository.get_by_id(created.id)
        self.assertEqual(fetched.name, "Technology")
        self.assertEqual(fetched.size, "Large")

    def test_get_by_id_returns_none_when_missing(self):
        self.assertIsNone(self.repository.get_by_id(999))

    def test_get_by_name_is_case_insensitive(self):
        self.repository.create(_sector(name="Technology"))
        found = self.repository.get_by_name("technology")
        self.assertIsNotNone(found)
        self.assertEqual(found.name, "Technology")

    def test_get_or_create_returns_existing_row_without_duplicating(self):
        first = self.repository.get_or_create(_sector(name="Financials"))
        second = self.repository.get_or_create(_sector(name="Financials"))
        self.assertEqual(first.id, second.id)
        self.assertEqual(len(self.repository.list_all()), 1)

    def test_get_or_create_creates_when_absent(self):
        self.assertIsNone(self.repository.get_by_name("Energy"))
        created = self.repository.get_or_create(_sector(name="Energy"))
        self.assertIsNotNone(created.id)
        self.assertEqual(self.repository.get_by_name("Energy").id, created.id)

    def test_list_all_returns_every_sector(self):
        self.repository.create(_sector(name="Technology"))
        self.repository.create(_sector(name="Healthcare"))
        names = {sector.name for sector in self.repository.list_all()}
        self.assertEqual(names, {"Technology", "Healthcare"})


if __name__ == "__main__":
    unittest.main()
