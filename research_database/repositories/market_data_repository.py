"""
Market Data Repository

Provides Create, Read, and lookup operations for the Market Data entity
(MarketDataSnapshot) of the Verified Knowledge Database, per
DATABASE_ARCHITECTURE.md Layer 6. The `market_data` table itself
already existed (research_database/schema/market_data.py, registered
in database_initializer.py's SCHEMA_MODULES since before this
repository existed) -- this module only adds the CRUD access layer for
it, following the exact pattern CompanyRepository already established.
It does not add, remove, or alter any column.

This is the only module allowed to compose SQL for the `market_data`
table.
"""

from research_database.database_manager import DatabaseError, DatabaseManager
from research_database.schema.market_data import MarketDataSnapshot

_INSERT_UPDATE_COLUMNS = (
    "company_id",
    "snapshot_timestamp",
    "current_price",
    "day_low",
    "day_high",
    "week_52_low",
    "week_52_high",
    "traded_volume",
    "market_capitalization",
    "currency",
)


class MarketDataRepositoryError(Exception):
    """Raised when a Market Data Repository operation fails."""


def _row_to_snapshot(row: dict) -> MarketDataSnapshot:
    """Convert a raw database row into a MarketDataSnapshot dataclass instance."""
    return MarketDataSnapshot(**dict(row))


def _snapshot_to_values(snapshot: MarketDataSnapshot) -> tuple:
    """Build the ordered parameter tuple for an insert statement."""
    return (
        snapshot.company_id,
        snapshot.snapshot_timestamp,
        snapshot.current_price,
        snapshot.day_low,
        snapshot.day_high,
        snapshot.week_52_low,
        snapshot.week_52_high,
        snapshot.traded_volume,
        snapshot.market_capitalization,
        snapshot.currency,
    )


class MarketDataRepository:
    """Repository for MarketDataSnapshot entity operations, backed
    exclusively by DatabaseManager."""

    def __init__(self, manager: DatabaseManager) -> None:
        self.manager = manager

    def create(self, snapshot: MarketDataSnapshot) -> MarketDataSnapshot:
        """Insert a new MarketDataSnapshot. The `id` on the given
        snapshot is ignored; the returned snapshot carries the
        database-assigned id."""
        columns = ", ".join(_INSERT_UPDATE_COLUMNS)
        placeholders = ", ".join("?" for _ in _INSERT_UPDATE_COLUMNS)

        try:
            with self.manager.transaction() as tx:
                cursor = tx.execute(
                    f"INSERT INTO market_data ({columns}) VALUES ({placeholders})",
                    _snapshot_to_values(snapshot),
                )
                new_id = cursor.lastrowid
        except DatabaseError as error:
            raise MarketDataRepositoryError(f"Failed to create market_data record: {error}") from error

        return self.get_by_id(new_id)

    def get_by_id(self, snapshot_id: int) -> MarketDataSnapshot | None:
        """Return a MarketDataSnapshot by its primary key, or None if not found."""
        row = self.manager.fetch_one("SELECT * FROM market_data WHERE id = ?", (snapshot_id,))
        return _row_to_snapshot(row) if row else None

    def list_by_company(self, company_id: int) -> list[MarketDataSnapshot]:
        """Return every MarketDataSnapshot for `company_id`, ordered by id."""
        rows = self.manager.fetch_all(
            "SELECT * FROM market_data WHERE company_id = ? ORDER BY id", (company_id,)
        )
        return [_row_to_snapshot(row) for row in rows]
