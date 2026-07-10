"""
API Health Repository

Provides Read and Upsert operations for the ApiHealth entity -- the
API Manager's persisted, live status per ApiProvider row, per
project_documentation/API_MANAGER_ARCHITECTURE.md Section 10.2. This is
the only module allowed to compose SQL for the `api_health` table.
"""

from research_database.database_manager import DatabaseError, DatabaseManager
from research_database.schema.api_health import ApiHealth

_INSERT_UPDATE_COLUMNS = (
    "provider_id",
    "status",
    "last_health_check",
    "response_time_ms",
    "last_error",
    "consecutive_failures",
)


class ApiHealthRepositoryError(Exception):
    """Raised when an API Health Repository operation fails."""


def _row_to_health(row: dict) -> ApiHealth:
    """Convert a raw database row into an ApiHealth dataclass instance."""
    return ApiHealth(**dict(row))


def _health_to_values(health: ApiHealth) -> tuple:
    """Build the ordered parameter tuple for an insert or update statement."""
    return (
        health.provider_id,
        health.status,
        health.last_health_check,
        health.response_time_ms,
        health.last_error,
        health.consecutive_failures,
    )


class ApiHealthRepository:
    """Repository for ApiHealth entity operations, backed exclusively
    by DatabaseManager. api_provider -> api_health is One-to-One
    (Section 10.4): upsert() enforces this by updating the existing row
    for a provider_id if one exists, inserting only if none does."""

    def __init__(self, manager: DatabaseManager) -> None:
        self.manager = manager

    def upsert(self, health: ApiHealth) -> ApiHealth:
        """Insert or update the single ApiHealth row for
        `health.provider_id`."""
        existing = self.get_by_provider_id(health.provider_id)
        try:
            with self.manager.transaction() as tx:
                if existing is None:
                    columns = ", ".join(_INSERT_UPDATE_COLUMNS)
                    placeholders = ", ".join("?" for _ in _INSERT_UPDATE_COLUMNS)
                    cursor = tx.execute(
                        f"INSERT INTO api_health ({columns}) VALUES ({placeholders})",
                        _health_to_values(health),
                    )
                    record_id = cursor.lastrowid
                else:
                    assignments = ", ".join(f"{column} = ?" for column in _INSERT_UPDATE_COLUMNS)
                    tx.execute(
                        f"UPDATE api_health SET {assignments} WHERE id = ?",
                        _health_to_values(health) + (existing.id,),
                    )
                    record_id = existing.id
        except DatabaseError as error:
            raise ApiHealthRepositoryError(
                f"Failed to upsert api_health for provider {health.provider_id}: {error}"
            ) from error

        return self.get_by_id(record_id)

    def get_by_id(self, health_id: int) -> ApiHealth | None:
        """Return an ApiHealth by its primary key, or None if not found."""
        row = self.manager.fetch_one("SELECT * FROM api_health WHERE id = ?", (health_id,))
        return _row_to_health(row) if row else None

    def get_by_provider_id(self, provider_id: int) -> ApiHealth | None:
        """Return the ApiHealth row for `provider_id`, or None if it
        has never been checked."""
        row = self.manager.fetch_one(
            "SELECT * FROM api_health WHERE provider_id = ?", (provider_id,)
        )
        return _row_to_health(row) if row else None

    def list_all(self) -> list[ApiHealth]:
        """Return every ApiHealth record."""
        rows = self.manager.fetch_all("SELECT * FROM api_health ORDER BY id")
        return [_row_to_health(row) for row in rows]
