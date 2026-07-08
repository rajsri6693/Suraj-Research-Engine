"""
Company Repository

Provides Create, Read, Update, Delete, search, and statistics operations
for the Company entity. This is the only module allowed to compose SQL
for the `company` table, and it does so exclusively through
DatabaseManager — it never touches sqlite3 directly.
"""

import json

from research_database.database_manager import DatabaseError, DatabaseManager
from research_database.schema.company import Company

_LIST_FIELDS = (
    "stock_exchanges",
    "ticker_symbols",
    "geographic_footprint",
    "customer_segments",
)

_INSERT_UPDATE_COLUMNS = (
    "legal_name",
    "common_name",
    "registration_details",
    "incorporation_country",
    "headquarters_location",
    "founding_date",
    "website",
    "stock_exchanges",
    "ticker_symbols",
    "business_description",
    "mission",
    "industry",
    "sector_id",
    "business_model_summary",
    "geographic_footprint",
    "customer_segments",
)


class CompanyRepositoryError(Exception):
    """Raised when a Company Repository operation fails."""


def _deserialize_list(value) -> list:
    """Deserialize a JSON-encoded list column back into a Python list."""
    return json.loads(value) if value else []


def _row_to_company(row: dict) -> Company:
    """Convert a raw database row into a Company dataclass instance."""
    data = dict(row)
    for field_name in _LIST_FIELDS:
        data[field_name] = _deserialize_list(data.get(field_name))
    return Company(**data)


def _company_to_values(company: Company) -> tuple:
    """Build the ordered parameter tuple for an insert or update statement."""
    return (
        company.legal_name,
        company.common_name,
        company.registration_details,
        company.incorporation_country,
        company.headquarters_location,
        company.founding_date,
        company.website,
        json.dumps(company.stock_exchanges),
        json.dumps(company.ticker_symbols),
        company.business_description,
        company.mission,
        company.industry,
        company.sector_id,
        company.business_model_summary,
        json.dumps(company.geographic_footprint),
        json.dumps(company.customer_segments),
    )


class CompanyRepository:
    """Repository for Company entity operations, backed exclusively by
    DatabaseManager."""

    def __init__(self, manager: DatabaseManager) -> None:
        self.manager = manager

    def create(self, company: Company) -> Company:
        """Insert a new Company record. The `id` on the given Company is
        ignored; the returned Company carries the database-assigned id."""
        columns = ", ".join(_INSERT_UPDATE_COLUMNS)
        placeholders = ", ".join("?" for _ in _INSERT_UPDATE_COLUMNS)

        try:
            with self.manager.transaction() as tx:
                cursor = tx.execute(
                    f"INSERT INTO company ({columns}) VALUES ({placeholders})",
                    _company_to_values(company),
                )
                new_id = cursor.lastrowid
        except DatabaseError as error:
            raise CompanyRepositoryError(f"Failed to create company: {error}") from error

        return self.get_by_id(new_id)

    def update(self, company: Company) -> Company | None:
        """Update an existing Company record identified by its id.
        Returns the updated Company, or None if no such id exists."""
        assignments = ", ".join(f"{column} = ?" for column in _INSERT_UPDATE_COLUMNS)

        try:
            with self.manager.transaction() as tx:
                tx.execute(
                    f"UPDATE company SET {assignments} WHERE id = ?",
                    _company_to_values(company) + (company.id,),
                )
        except DatabaseError as error:
            raise CompanyRepositoryError(
                f"Failed to update company {company.id}: {error}"
            ) from error

        return self.get_by_id(company.id)

    def delete(self, company_id: int) -> bool:
        """Delete a Company record by id. Returns True if a row was deleted."""
        try:
            with self.manager.transaction() as tx:
                cursor = tx.execute("DELETE FROM company WHERE id = ?", (company_id,))
                return cursor.rowcount > 0
        except DatabaseError as error:
            raise CompanyRepositoryError(
                f"Failed to delete company {company_id}: {error}"
            ) from error

    def get_by_id(self, company_id: int) -> Company | None:
        """Return a Company by its primary key, or None if not found."""
        row = self.manager.fetch_one("SELECT * FROM company WHERE id = ?", (company_id,))
        return _row_to_company(row) if row else None

    def get_by_symbol(self, symbol: str) -> Company | None:
        """Return a Company whose ticker symbols include the given symbol
        (case-insensitive, exact match)."""
        symbol_lower = symbol.lower()
        for row in self.manager.fetch_all("SELECT * FROM company"):
            tickers = _deserialize_list(row.get("ticker_symbols"))
            if any(ticker.lower() == symbol_lower for ticker in tickers):
                return _row_to_company(row)
        return None

    def search(self, term: str) -> list[Company]:
        """Search companies by legal name, common name, ticker symbol, or
        exchange symbol (case-insensitive, partial match)."""
        pattern = f"%{term.lower()}%"
        rows = self.manager.fetch_all(
            "SELECT * FROM company WHERE "
            "LOWER(legal_name) LIKE ? OR LOWER(common_name) LIKE ? OR "
            "LOWER(ticker_symbols) LIKE ? OR LOWER(stock_exchanges) LIKE ? "
            "ORDER BY common_name",
            (pattern, pattern, pattern, pattern),
        )
        return [_row_to_company(row) for row in rows]

    def list_all(self) -> list[Company]:
        """Return every Company record."""
        rows = self.manager.fetch_all("SELECT * FROM company ORDER BY common_name")
        return [_row_to_company(row) for row in rows]

    def statistics(self) -> dict:
        """Return aggregate statistics: total companies, total sectors,
        and database version (if available)."""
        total_companies = self.manager.fetch_one(
            "SELECT COUNT(*) AS count FROM company"
        )["count"]
        total_sectors = self.manager.fetch_one(
            "SELECT COUNT(*) AS count FROM sector"
        )["count"]

        version_row = self.manager.fetch_one(
            "SELECT version FROM schema_version WHERE id = 1"
        )
        database_version = version_row["version"] if version_row else "unknown"

        return {
            "total_companies": total_companies,
            "total_sectors": total_sectors,
            "database_version": database_version,
        }
