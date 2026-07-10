"""Unit tests for research_database.repositories.api_health_repository,
per project_documentation/API_MANAGER_ARCHITECTURE.md Section 10.2.
Uses an isolated, temp-file-backed database -- never the real project
database file.
"""

import os
import tempfile
import unittest

from research_database.api_manager_schema import ApiManagerDatabaseInitializer
from research_database.database_manager import DatabaseManager
from research_database.repositories.api_health_repository import ApiHealthRepository
from research_database.repositories.api_provider_repository import ApiProviderRepository
from research_database.schema.api_health import ApiHealth
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


class TestApiHealthRepository(unittest.TestCase):
    def setUp(self):
        self.manager = make_isolated_database_manager()
        ApiManagerDatabaseInitializer(self.manager).initialize()
        self.provider_repo = ApiProviderRepository(self.manager)
        self.health_repo = ApiHealthRepository(self.manager)
        self.provider = self.provider_repo.create(
            ApiProvider(
                id=0,
                provider_name="Financial Modeling Prep (FMP)",
                category="Fundamental Data",
                role="Primary",
                key_env_var="FMP_API_KEY",
                active=True,
            )
        )

    def tearDown(self):
        close_isolated_database_manager(self.manager)

    def _health(self, **overrides) -> ApiHealth:
        defaults = dict(
            id=0,
            provider_id=self.provider.id,
            status="UNKNOWN",
            last_health_check="",
            response_time_ms=0.0,
            last_error="",
            consecutive_failures=0,
        )
        defaults.update(overrides)
        return ApiHealth(**defaults)

    def test_upsert_inserts_when_no_row_exists(self):
        result = self.health_repo.upsert(self._health(status="ONLINE", response_time_ms=12.5))
        self.assertEqual(result.status, "ONLINE")
        self.assertEqual(result.response_time_ms, 12.5)
        self.assertEqual(len(self.health_repo.list_all()), 1)

    def test_upsert_updates_the_existing_row_one_to_one(self):
        self.health_repo.upsert(self._health(status="UNKNOWN"))
        self.health_repo.upsert(self._health(status="DOWN", last_error="boom"))
        self.health_repo.upsert(self._health(status="ONLINE", last_error=""))

        all_rows = self.health_repo.list_all()
        self.assertEqual(len(all_rows), 1, "api_provider -> api_health must stay One-to-One")
        self.assertEqual(all_rows[0].status, "ONLINE")

    def test_get_by_provider_id_returns_none_before_any_check(self):
        self.assertIsNone(self.health_repo.get_by_provider_id(self.provider.id))

    def test_get_by_provider_id_returns_the_latest_state(self):
        self.health_repo.upsert(self._health(status="RATE_LIMITED", consecutive_failures=3))
        found = self.health_repo.get_by_provider_id(self.provider.id)
        self.assertEqual(found.status, "RATE_LIMITED")
        self.assertEqual(found.consecutive_failures, 3)

    def test_two_different_providers_get_two_independent_rows(self):
        second_provider = self.provider_repo.create(
            ApiProvider(
                id=0,
                provider_name="Finnhub",
                category="Fundamental Data",
                role="Backup",
                key_env_var="FINNHUB_API_KEY",
                active=True,
            )
        )
        self.health_repo.upsert(self._health(status="ONLINE"))
        self.health_repo.upsert(self._health(provider_id=second_provider.id, status="DOWN"))

        self.assertEqual(len(self.health_repo.list_all()), 2)
        self.assertEqual(self.health_repo.get_by_provider_id(self.provider.id).status, "ONLINE")
        self.assertEqual(
            self.health_repo.get_by_provider_id(second_provider.id).status, "DOWN"
        )


if __name__ == "__main__":
    unittest.main()
