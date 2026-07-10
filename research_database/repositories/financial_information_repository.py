"""
Financial Information Repository

Provides Create, Read, and lookup operations for the Financial
Information entity (FinancialRecord) of the Verified Knowledge
Database, per DATABASE_ARCHITECTURE.md Layer 3. The
`financial_information` table itself already existed
(research_database/schema/financial_information.py, registered in
database_initializer.py's SCHEMA_MODULES since before this repository
existed) -- this module only adds the CRUD access layer for it,
following the exact pattern CompanyRepository already established. It
does not add, remove, or alter any column.

This is the only module allowed to compose SQL for the
`financial_information` table.
"""

import json

from research_database.database_manager import DatabaseError, DatabaseManager
from research_database.schema.financial_information import FinancialRecord

_INSERT_UPDATE_COLUMNS = (
    "company_id",
    "reporting_period",
    "currency",
    "revenue",
    "profit",
    "gross_margin",
    "operating_margin",
    "net_margin",
    "balance_sheet_summary",
    "cash_flow_summary",
    "key_ratios",
)


class FinancialInformationRepositoryError(Exception):
    """Raised when a Financial Information Repository operation fails."""


def _row_to_financial_record(row: dict) -> FinancialRecord:
    """Convert a raw database row into a FinancialRecord dataclass instance."""
    data = dict(row)
    data["key_ratios"] = json.loads(data["key_ratios"]) if data.get("key_ratios") else {}
    return FinancialRecord(**data)


def _financial_record_to_values(record: FinancialRecord) -> tuple:
    """Build the ordered parameter tuple for an insert or update statement."""
    return (
        record.company_id,
        record.reporting_period,
        record.currency,
        record.revenue,
        record.profit,
        record.gross_margin,
        record.operating_margin,
        record.net_margin,
        record.balance_sheet_summary,
        record.cash_flow_summary,
        json.dumps(record.key_ratios),
    )


class FinancialInformationRepository:
    """Repository for FinancialRecord entity operations, backed
    exclusively by DatabaseManager."""

    def __init__(self, manager: DatabaseManager) -> None:
        self.manager = manager

    def create(self, record: FinancialRecord) -> FinancialRecord:
        """Insert a new FinancialRecord. The `id` on the given record
        is ignored; the returned FinancialRecord carries the
        database-assigned id."""
        columns = ", ".join(_INSERT_UPDATE_COLUMNS)
        placeholders = ", ".join("?" for _ in _INSERT_UPDATE_COLUMNS)

        try:
            with self.manager.transaction() as tx:
                cursor = tx.execute(
                    f"INSERT INTO financial_information ({columns}) VALUES ({placeholders})",
                    _financial_record_to_values(record),
                )
                new_id = cursor.lastrowid
        except DatabaseError as error:
            raise FinancialInformationRepositoryError(
                f"Failed to create financial_information record: {error}"
            ) from error

        return self.get_by_id(new_id)

    def get_by_id(self, record_id: int) -> FinancialRecord | None:
        """Return a FinancialRecord by its primary key, or None if not found."""
        row = self.manager.fetch_one(
            "SELECT * FROM financial_information WHERE id = ?", (record_id,)
        )
        return _row_to_financial_record(row) if row else None

    def list_by_company(self, company_id: int) -> list[FinancialRecord]:
        """Return every FinancialRecord for `company_id`, ordered by id."""
        rows = self.manager.fetch_all(
            "SELECT * FROM financial_information WHERE company_id = ? ORDER BY id",
            (company_id,),
        )
        return [_row_to_financial_record(row) for row in rows]
