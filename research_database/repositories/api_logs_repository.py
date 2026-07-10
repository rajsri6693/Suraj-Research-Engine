"""
API Logs Repository

Provides Create and lookup operations for the ApiLog entity -- the
API Manager's permanent record of every call attempt, per
project_documentation/API_MANAGER_ARCHITECTURE.md Section 10.3. Logs
are append-only: this repository exposes no update or delete, since
Section 5.6 requires every entry stay "never summarized or
overwritten." This is the only module allowed to compose SQL for the
`api_logs` table.
"""

from research_database.database_manager import DatabaseError, DatabaseManager
from research_database.schema.api_logs import ApiLog

_INSERT_COLUMNS = (
    "timestamp",
    "category",
    "operation",
    "collector_name",
    "provider_id",
    "role_attempted",
    "served_by",
    "outcome",
    "health_status",
    "response_time_ms",
)


class ApiLogsRepositoryError(Exception):
    """Raised when an API Logs Repository operation fails."""


def _row_to_log(row: dict) -> ApiLog:
    """Convert a raw database row into an ApiLog dataclass instance."""
    return ApiLog(**dict(row))


def _log_to_values(log: ApiLog) -> tuple:
    """Build the ordered parameter tuple for an insert statement."""
    return (
        log.timestamp,
        log.category,
        log.operation,
        log.collector_name,
        log.provider_id,
        log.role_attempted,
        log.served_by,
        log.outcome,
        log.health_status,
        log.response_time_ms,
    )


class ApiLogsRepository:
    """Repository for ApiLog entity operations, backed exclusively by
    DatabaseManager. Append-only, per Section 5.6."""

    def __init__(self, manager: DatabaseManager) -> None:
        self.manager = manager

    def create(self, log: ApiLog) -> ApiLog:
        """Insert a new ApiLog row. The `id` on the given log is
        ignored; the returned ApiLog carries the database-assigned
        id."""
        columns = ", ".join(_INSERT_COLUMNS)
        placeholders = ", ".join("?" for _ in _INSERT_COLUMNS)

        try:
            with self.manager.transaction() as tx:
                cursor = tx.execute(
                    f"INSERT INTO api_logs ({columns}) VALUES ({placeholders})",
                    _log_to_values(log),
                )
                new_id = cursor.lastrowid
        except DatabaseError as error:
            raise ApiLogsRepositoryError(f"Failed to create api_logs row: {error}") from error

        return self.get_by_id(new_id)

    def get_by_id(self, log_id: int) -> ApiLog | None:
        """Return an ApiLog by its primary key, or None if not found."""
        row = self.manager.fetch_one("SELECT * FROM api_logs WHERE id = ?", (log_id,))
        return _row_to_log(row) if row else None

    def list_by_provider(self, provider_id: int) -> list[ApiLog]:
        """Return every ApiLog row attempted against `provider_id`,
        oldest first."""
        rows = self.manager.fetch_all(
            "SELECT * FROM api_logs WHERE provider_id = ? ORDER BY id", (provider_id,)
        )
        return [_row_to_log(row) for row in rows]

    def list_by_category(self, category: str) -> list[ApiLog]:
        """Return every ApiLog row for `category`, oldest first."""
        rows = self.manager.fetch_all(
            "SELECT * FROM api_logs WHERE category = ? ORDER BY id", (category,)
        )
        return [_row_to_log(row) for row in rows]

    def usage_count(self, provider_id: int) -> int:
        """Total attempts ever made against `provider_id`."""
        row = self.manager.fetch_one(
            "SELECT COUNT(*) AS count FROM api_logs WHERE provider_id = ?", (provider_id,)
        )
        return row["count"] if row else 0

    def success_count(self, provider_id: int) -> int:
        """Successful attempts ever made against `provider_id`."""
        row = self.manager.fetch_one(
            "SELECT COUNT(*) AS count FROM api_logs WHERE provider_id = ? AND outcome = 'SUCCESS'",
            (provider_id,),
        )
        return row["count"] if row else 0
