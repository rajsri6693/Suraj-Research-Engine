"""
Price History Repository

Provides Create, Read, and lookup operations for the Historical Price
(OHLC) entity (HistoricalPrice) of the Verified Knowledge Database, per
DATABASE_ARCHITECTURE.md Layer 6. The `price_history` table itself
already existed (research_database/schema/price_history.py, registered
in database_initializer.py's SCHEMA_MODULES since before this
repository existed) -- this module only adds the CRUD access layer for
it, following the exact pattern CompanyRepository already established.
It does not add, remove, or alter any column.

This is the only module allowed to compose SQL for the `price_history`
table.
"""

from research_database.database_manager import DatabaseError, DatabaseManager
from research_database.schema.price_history import HistoricalPrice

_INSERT_UPDATE_COLUMNS = (
    "company_id",
    "period_date",
    "open_price",
    "high_price",
    "low_price",
    "close_price",
    "volume",
)


class PriceHistoryRepositoryError(Exception):
    """Raised when a Price History Repository operation fails."""


def _row_to_historical_price(row: dict) -> HistoricalPrice:
    """Convert a raw database row into a HistoricalPrice dataclass instance."""
    return HistoricalPrice(**dict(row))


def _historical_price_to_values(record: HistoricalPrice) -> tuple:
    """Build the ordered parameter tuple for an insert statement."""
    return (
        record.company_id,
        record.period_date,
        record.open_price,
        record.high_price,
        record.low_price,
        record.close_price,
        record.volume,
    )


class PriceHistoryRepository:
    """Repository for HistoricalPrice entity operations, backed
    exclusively by DatabaseManager."""

    def __init__(self, manager: DatabaseManager) -> None:
        self.manager = manager

    def create(self, record: HistoricalPrice) -> HistoricalPrice:
        """Insert a new HistoricalPrice record. The `id` on the given
        record is ignored; the returned record carries the
        database-assigned id."""
        columns = ", ".join(_INSERT_UPDATE_COLUMNS)
        placeholders = ", ".join("?" for _ in _INSERT_UPDATE_COLUMNS)

        try:
            with self.manager.transaction() as tx:
                cursor = tx.execute(
                    f"INSERT INTO price_history ({columns}) VALUES ({placeholders})",
                    _historical_price_to_values(record),
                )
                new_id = cursor.lastrowid
        except DatabaseError as error:
            raise PriceHistoryRepositoryError(f"Failed to create price_history record: {error}") from error

        return self.get_by_id(new_id)

    def create_many(self, records: list[HistoricalPrice]) -> list[HistoricalPrice]:
        """Insert several HistoricalPrice records for the same company
        (one OHLC series) in a single transaction."""
        return [self.create(record) for record in records]

    def get_by_id(self, record_id: int) -> HistoricalPrice | None:
        """Return a HistoricalPrice by its primary key, or None if not found."""
        row = self.manager.fetch_one("SELECT * FROM price_history WHERE id = ?", (record_id,))
        return _row_to_historical_price(row) if row else None

    def list_by_company(self, company_id: int) -> list[HistoricalPrice]:
        """Return every HistoricalPrice record for `company_id`, ordered
        by period_date."""
        rows = self.manager.fetch_all(
            "SELECT * FROM price_history WHERE company_id = ? ORDER BY period_date",
            (company_id,),
        )
        return [_row_to_historical_price(row) for row in rows]
