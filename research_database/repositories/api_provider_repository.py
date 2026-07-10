"""
API Provider Repository

Provides Create, Read, Update, Delete, and lookup operations for the
ApiProvider entity -- the API Manager's persisted Category -> Primary
Provider -> Backup Provider mapping, per
project_documentation/API_MANAGER_ARCHITECTURE.md Section 10.1. This is
the only module allowed to compose SQL for the `api_provider` table.
"""

from research_database.database_manager import DatabaseError, DatabaseManager
from research_database.schema.api_provider import ApiProvider

_INSERT_UPDATE_COLUMNS = (
    "provider_name",
    "category",
    "role",
    "key_env_var",
    "active",
)


class ApiProviderRepositoryError(Exception):
    """Raised when an API Provider Repository operation fails."""


def _row_to_provider(row: dict) -> ApiProvider:
    """Convert a raw database row into an ApiProvider dataclass instance."""
    data = dict(row)
    data["active"] = bool(data["active"])
    return ApiProvider(**data)


def _provider_to_values(provider: ApiProvider) -> tuple:
    """Build the ordered parameter tuple for an insert or update statement."""
    return (
        provider.provider_name,
        provider.category,
        provider.role,
        provider.key_env_var,
        int(provider.active),
    )


class ApiProviderRepository:
    """Repository for ApiProvider entity operations, backed exclusively
    by DatabaseManager."""

    def __init__(self, manager: DatabaseManager) -> None:
        self.manager = manager

    def create(self, provider: ApiProvider) -> ApiProvider:
        """Insert a new ApiProvider record. The `id` on the given
        provider is ignored; the returned ApiProvider carries the
        database-assigned id."""
        columns = ", ".join(_INSERT_UPDATE_COLUMNS)
        placeholders = ", ".join("?" for _ in _INSERT_UPDATE_COLUMNS)

        try:
            with self.manager.transaction() as tx:
                cursor = tx.execute(
                    f"INSERT INTO api_provider ({columns}) VALUES ({placeholders})",
                    _provider_to_values(provider),
                )
                new_id = cursor.lastrowid
        except DatabaseError as error:
            raise ApiProviderRepositoryError(
                f"Failed to create api_provider: {error}"
            ) from error

        return self.get_by_id(new_id)

    def update(self, provider: ApiProvider) -> ApiProvider | None:
        """Update an existing ApiProvider record identified by its id.
        Returns the updated ApiProvider, or None if no such id exists."""
        assignments = ", ".join(f"{column} = ?" for column in _INSERT_UPDATE_COLUMNS)

        try:
            with self.manager.transaction() as tx:
                tx.execute(
                    f"UPDATE api_provider SET {assignments} WHERE id = ?",
                    _provider_to_values(provider) + (provider.id,),
                )
        except DatabaseError as error:
            raise ApiProviderRepositoryError(
                f"Failed to update api_provider {provider.id}: {error}"
            ) from error

        return self.get_by_id(provider.id)

    def delete(self, provider_id: int) -> bool:
        """Delete an ApiProvider record by id. Returns True if a row
        was deleted."""
        try:
            with self.manager.transaction() as tx:
                cursor = tx.execute("DELETE FROM api_provider WHERE id = ?", (provider_id,))
                return cursor.rowcount > 0
        except DatabaseError as error:
            raise ApiProviderRepositoryError(
                f"Failed to delete api_provider {provider_id}: {error}"
            ) from error

    def get_by_id(self, provider_id: int) -> ApiProvider | None:
        """Return an ApiProvider by its primary key, or None if not found."""
        row = self.manager.fetch_one("SELECT * FROM api_provider WHERE id = ?", (provider_id,))
        return _row_to_provider(row) if row else None

    def get_by_category_role(self, category: str, role: str) -> ApiProvider | None:
        """Return the ApiProvider currently holding `role` for
        `category`, or None if not found."""
        row = self.manager.fetch_one(
            "SELECT * FROM api_provider WHERE category = ? AND role = ?",
            (category, role),
        )
        return _row_to_provider(row) if row else None

    def list_all(self) -> list[ApiProvider]:
        """Return every ApiProvider record."""
        rows = self.manager.fetch_all("SELECT * FROM api_provider ORDER BY id")
        return [_row_to_provider(row) for row in rows]
