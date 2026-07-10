"""Unit tests for research_database.repositories.api_provider_repository,
per project_documentation/API_MANAGER_ARCHITECTURE.md Section 10.1.
Uses an isolated, temp-file-backed database -- never the real project
database file.
"""

import os
import tempfile
import unittest

from research_database.api_manager_schema import ApiManagerDatabaseInitializer
from research_database.database_manager import DatabaseManager
from research_database.repositories.api_provider_repository import ApiProviderRepository
from research_database.schema.api_provider import ApiProvider


def make_isolated_database_manager() -> DatabaseManager:
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    os.remove(db_path)
    manager = DatabaseManager(db_path)
    manager.audit_db_path = db_path  # type: ignore[attr-defined]
    return manager


def close_isolated_database_manager(manager: DatabaseManager) -> None:
    manager.close()
    db_path = getattr(manager, "audit_db_path", None)
    if db_path and os.path.exists(db_path):
        os.remove(db_path)


def _sample_provider(**overrides) -> ApiProvider:
    defaults = dict(
        id=0,
        provider_name="Financial Modeling Prep (FMP)",
        category="Fundamental Data",
        role="Primary",
        key_env_var="FMP_API_KEY",
        active=True,
    )
    defaults.update(overrides)
    return ApiProvider(**defaults)


class RepositoryTestCase(unittest.TestCase):
    def setUp(self):
        self.manager = make_isolated_database_manager()
        ApiManagerDatabaseInitializer(self.manager).initialize()
        self.repository = ApiProviderRepository(self.manager)

    def tearDown(self):
        close_isolated_database_manager(self.manager)


class TestCreateAndGet(RepositoryTestCase):
    def test_create_assigns_an_id_and_round_trips_every_field(self):
        created = self.repository.create(_sample_provider())
        self.assertIsInstance(created.id, int)
        self.assertGreater(created.id, 0)

        fetched = self.repository.get_by_id(created.id)
        self.assertEqual(fetched.provider_name, "Financial Modeling Prep (FMP)")
        self.assertEqual(fetched.category, "Fundamental Data")
        self.assertEqual(fetched.role, "Primary")
        self.assertEqual(fetched.key_env_var, "FMP_API_KEY")
        self.assertTrue(fetched.active)

    def test_get_by_id_returns_none_when_missing(self):
        self.assertIsNone(self.repository.get_by_id(999))

    def test_active_flag_round_trips_as_a_real_bool(self):
        created = self.repository.create(_sample_provider(active=False))
        fetched = self.repository.get_by_id(created.id)
        self.assertIs(fetched.active, False)


class TestGetByCategoryRole(RepositoryTestCase):
    def test_finds_the_matching_row(self):
        self.repository.create(_sample_provider())
        found = self.repository.get_by_category_role("Fundamental Data", "Primary")
        self.assertIsNotNone(found)
        self.assertEqual(found.provider_name, "Financial Modeling Prep (FMP)")

    def test_returns_none_when_no_match(self):
        self.assertIsNone(self.repository.get_by_category_role("News", "Primary"))


class TestUpdate(RepositoryTestCase):
    def test_update_persists_changes(self):
        created = self.repository.create(_sample_provider())
        created.active = False
        created.role = "Backup"
        updated = self.repository.update(created)
        self.assertFalse(updated.active)
        self.assertEqual(updated.role, "Backup")

    def test_update_of_missing_id_returns_none(self):
        missing = _sample_provider(id=999)
        result = self.repository.update(missing)
        self.assertIsNone(result)


class TestDelete(RepositoryTestCase):
    def test_delete_removes_the_row(self):
        created = self.repository.create(_sample_provider())
        self.assertTrue(self.repository.delete(created.id))
        self.assertIsNone(self.repository.get_by_id(created.id))

    def test_delete_of_missing_id_returns_false(self):
        self.assertFalse(self.repository.delete(999))


class TestSeedingAllSixDefaultRows(RepositoryTestCase):
    def test_seed_and_round_trip_the_finalized_six_row_mapping(self):
        from research_engine.api_manager.api_provider import DEFAULT_PROVIDER_REGISTRATIONS

        for provider in DEFAULT_PROVIDER_REGISTRATIONS:
            self.repository.create(
                _sample_provider(
                    provider_name=provider.provider_name.value,
                    category=provider.category.value,
                    role=provider.role.value,
                    key_env_var=provider.key_env_var,
                    active=provider.active,
                )
            )

        all_rows = self.repository.list_all()
        self.assertEqual(len(all_rows), 6)

        finnhub_rows = [row for row in all_rows if row.provider_name == "Finnhub"]
        self.assertEqual(len(finnhub_rows), 2)
        self.assertEqual({row.category for row in finnhub_rows}, {"Fundamental Data", "News"})
        self.assertTrue(all(row.role == "Backup" for row in finnhub_rows))


if __name__ == "__main__":
    unittest.main()
