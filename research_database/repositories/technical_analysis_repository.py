"""
Technical Analysis Repository

Provides Create, Read, and lookup operations for the Technical Analysis
entity (TechnicalIndicator) of the Verified Knowledge Database, per
DATABASE_ARCHITECTURE.md Layer 6. The `technical_analysis` table itself
already existed (research_database/schema/technical_analysis.py,
registered in database_initializer.py's SCHEMA_MODULES since before
this repository existed) -- this module only adds the CRUD access
layer for it, following the exact pattern CompanyRepository already
established. It does not add, remove, or alter any column.

This is the only module allowed to compose SQL for the
`technical_analysis` table.
"""

from research_database.database_manager import DatabaseError, DatabaseManager
from research_database.schema.technical_analysis import TechnicalIndicator

_INSERT_UPDATE_COLUMNS = (
    "company_id",
    "price_history_id",
    "indicator_name",
    "indicator_value",
    "computed_date",
    "lookback_period",
)


class TechnicalAnalysisRepositoryError(Exception):
    """Raised when a Technical Analysis Repository operation fails."""


def _row_to_indicator(row: dict) -> TechnicalIndicator:
    """Convert a raw database row into a TechnicalIndicator dataclass instance."""
    return TechnicalIndicator(**dict(row))


def _indicator_to_values(indicator: TechnicalIndicator) -> tuple:
    """Build the ordered parameter tuple for an insert statement."""
    return (
        indicator.company_id,
        indicator.price_history_id,
        indicator.indicator_name,
        indicator.indicator_value,
        indicator.computed_date,
        indicator.lookback_period,
    )


class TechnicalAnalysisRepository:
    """Repository for TechnicalIndicator entity operations, backed
    exclusively by DatabaseManager."""

    def __init__(self, manager: DatabaseManager) -> None:
        self.manager = manager

    def create(self, indicator: TechnicalIndicator) -> TechnicalIndicator:
        """Insert a new TechnicalIndicator record. The `id` on the
        given indicator is ignored; the returned indicator carries the
        database-assigned id."""
        columns = ", ".join(_INSERT_UPDATE_COLUMNS)
        placeholders = ", ".join("?" for _ in _INSERT_UPDATE_COLUMNS)

        try:
            with self.manager.transaction() as tx:
                cursor = tx.execute(
                    f"INSERT INTO technical_analysis ({columns}) VALUES ({placeholders})",
                    _indicator_to_values(indicator),
                )
                new_id = cursor.lastrowid
        except DatabaseError as error:
            raise TechnicalAnalysisRepositoryError(
                f"Failed to create technical_analysis record: {error}"
            ) from error

        return self.get_by_id(new_id)

    def get_by_id(self, indicator_id: int) -> TechnicalIndicator | None:
        """Return a TechnicalIndicator by its primary key, or None if not found."""
        row = self.manager.fetch_one(
            "SELECT * FROM technical_analysis WHERE id = ?", (indicator_id,)
        )
        return _row_to_indicator(row) if row else None

    def list_by_company(self, company_id: int) -> list[TechnicalIndicator]:
        """Return every TechnicalIndicator record for `company_id`,
        ordered by id."""
        rows = self.manager.fetch_all(
            "SELECT * FROM technical_analysis WHERE company_id = ? ORDER BY id",
            (company_id,),
        )
        return [_row_to_indicator(row) for row in rows]
