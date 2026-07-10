"""Unit tests for research_database.repositories.api_logs_repository,
per project_documentation/API_MANAGER_ARCHITECTURE.md Section 10.3.
Uses an isolated, temp-file-backed database -- never the real project
database file.
"""

import os
import tempfile
import unittest

from research_database.api_manager_schema import ApiManagerDatabaseInitializer
from research_database.database_manager import DatabaseManager
from research_database.repositories.api_logs_repository import ApiLogsRepository
from research_database.repositories.api_provider_repository import ApiProviderRepository
from research_database.schema.api_logs import ApiLog
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


class TestApiLogsRepository(unittest.TestCase):
    def setUp(self):
        self.manager = make_isolated_database_manager()
        ApiManagerDatabaseInitializer(self.manager).initialize()
        self.provider_repo = ApiProviderRepository(self.manager)
        self.logs_repo = ApiLogsRepository(self.manager)
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

    def _log(self, **overrides) -> ApiLog:
        defaults = dict(
            id=0,
            timestamp="2026-07-10T00:00:00",
            category="Fundamental Data",
            operation="Company Profile",
            collector_name="",
            provider_id=self.provider.id,
            role_attempted="Primary",
            served_by="Primary",
            outcome="SUCCESS",
            health_status="ONLINE",
            response_time_ms=10.0,
        )
        defaults.update(overrides)
        return ApiLog(**defaults)

    def test_create_assigns_an_id_and_round_trips_every_field(self):
        created = self.logs_repo.create(self._log())
        self.assertIsInstance(created.id, int)
        fetched = self.logs_repo.get_by_id(created.id)
        self.assertEqual(fetched.operation, "Company Profile")
        self.assertEqual(fetched.outcome, "SUCCESS")
        self.assertEqual(fetched.served_by, "Primary")

    def test_logs_are_append_only_no_update_or_delete_methods_exist(self):
        self.assertFalse(hasattr(self.logs_repo, "update"))
        self.assertFalse(hasattr(self.logs_repo, "delete"))

    def test_list_by_provider_returns_every_attempt_oldest_first(self):
        self.logs_repo.create(self._log(timestamp="t1", outcome="FAILURE", served_by=""))
        self.logs_repo.create(self._log(timestamp="t2", outcome="SUCCESS"))
        rows = self.logs_repo.list_by_provider(self.provider.id)
        self.assertEqual([row.timestamp for row in rows], ["t1", "t2"])

    def test_list_by_category_filters_correctly(self):
        self.logs_repo.create(self._log(category="Fundamental Data"))
        self.logs_repo.create(self._log(category="News"))
        rows = self.logs_repo.list_by_category("Fundamental Data")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].category, "Fundamental Data")

    def test_usage_and_success_counts(self):
        self.logs_repo.create(self._log(outcome="SUCCESS", served_by="Primary"))
        self.logs_repo.create(self._log(outcome="FAILURE", served_by=""))
        self.logs_repo.create(self._log(outcome="FAILURE", served_by=""))

        self.assertEqual(self.logs_repo.usage_count(self.provider.id), 3)
        self.assertEqual(self.logs_repo.success_count(self.provider.id), 1)

    def test_counts_are_zero_for_a_provider_with_no_attempts(self):
        other = self.provider_repo.create(
            ApiProvider(
                id=0,
                provider_name="Finnhub",
                category="Fundamental Data",
                role="Backup",
                key_env_var="FINNHUB_API_KEY",
                active=True,
            )
        )
        self.assertEqual(self.logs_repo.usage_count(other.id), 0)
        self.assertEqual(self.logs_repo.success_count(other.id), 0)


if __name__ == "__main__":
    unittest.main()
