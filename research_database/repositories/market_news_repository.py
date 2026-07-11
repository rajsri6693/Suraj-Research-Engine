"""
Market News Repository

Provides Create, Read, and lookup operations for the Market News entity
(MarketNewsItem) of the Verified Knowledge Database, per
DATABASE_ARCHITECTURE.md Layer 4. The `market_news` table itself
already existed (research_database/schema/market_news.py, registered
in database_initializer.py's SCHEMA_MODULES since before this
repository existed) -- this module only adds the CRUD access layer for
it, following the exact pattern MarketDataRepository/CompanyRepository
already established.

`extracted_facts` is JSON-encoded on write and decoded on read, exactly
as CompanyRepository already does for its own List[str] columns -- the
`market_news` table has no array column type, so this is the existing,
established way a schema's List[str] field is stored in SQLite here.

Per Claude-Prompts/IMP_10F_NewsAPI_Integration.md's follow-up URL
requirement, `url` (research_database/schema/market_news.py) is the one
new column this change adds. DatabaseInitializer only ever issues
`CREATE TABLE IF NOT EXISTS` (database_initializer.py), so a
`market_news` table created before this change -- as the real project
database already has -- never gains the new column on its own.
`_ensure_url_column()` closes that gap with a single, idempotent
`ALTER TABLE ... ADD COLUMN`, checked once per repository instance
before every read or write, so this repository works unchanged against
either a pre-existing table or a freshly initialized one. This remains
the only module allowed to compose SQL for the `market_news` table.
"""

import json

from research_database.database_manager import DatabaseError, DatabaseManager
from research_database.schema.market_news import MarketNewsItem

_INSERT_UPDATE_COLUMNS = (
    "company_id",
    "headline",
    "event_date",
    "summary",
    "extracted_facts",
    "url",
)

_ADD_URL_COLUMN_SQL = "ALTER TABLE market_news ADD COLUMN url TEXT"


class MarketNewsRepositoryError(Exception):
    """Raised when a Market News Repository operation fails."""


def _row_to_item(row: dict) -> MarketNewsItem:
    """Convert a raw database row into a MarketNewsItem dataclass instance."""
    data = dict(row)
    data["extracted_facts"] = json.loads(data["extracted_facts"]) if data.get("extracted_facts") else []
    # A row written before this column existed (or read back before
    # migration on a legacy table) has no url value -- "" preserves
    # backward compatibility rather than surfacing None for a str field.
    data["url"] = data.get("url") or ""
    return MarketNewsItem(**data)


def _item_to_values(item: MarketNewsItem) -> tuple:
    """Build the ordered parameter tuple for an insert statement."""
    return (
        item.company_id,
        item.headline,
        item.event_date,
        item.summary,
        json.dumps(item.extracted_facts),
        item.url,
    )


class MarketNewsRepository:
    """Repository for MarketNewsItem entity operations, backed
    exclusively by DatabaseManager."""

    def __init__(self, manager: DatabaseManager) -> None:
        self.manager = manager
        self._url_column_ensured = False

    def _ensure_url_column(self) -> None:
        """Add the `url` column to an already-existing `market_news`
        table that predates it. A no-op once the column is present --
        checked via PRAGMA table_info rather than assumed, so this is
        safe to call before every operation without ever issuing a
        duplicate ALTER TABLE."""
        if self._url_column_ensured:
            return
        columns = {row["name"] for row in self.manager.fetch_all("PRAGMA table_info(market_news)")}
        if "url" not in columns:
            self.manager.execute(_ADD_URL_COLUMN_SQL)
            self.manager.commit()
        self._url_column_ensured = True

    def create(self, item: MarketNewsItem) -> MarketNewsItem:
        """Insert a new MarketNewsItem. The `id` on the given item is
        ignored; the returned item carries the database-assigned id."""
        self._ensure_url_column()
        columns = ", ".join(_INSERT_UPDATE_COLUMNS)
        placeholders = ", ".join("?" for _ in _INSERT_UPDATE_COLUMNS)

        try:
            with self.manager.transaction() as tx:
                cursor = tx.execute(
                    f"INSERT INTO market_news ({columns}) VALUES ({placeholders})",
                    _item_to_values(item),
                )
                new_id = cursor.lastrowid
        except DatabaseError as error:
            raise MarketNewsRepositoryError(f"Failed to create market_news record: {error}") from error

        return self.get_by_id(new_id)

    def get_by_id(self, item_id: int) -> MarketNewsItem | None:
        """Return a MarketNewsItem by its primary key, or None if not found."""
        self._ensure_url_column()
        row = self.manager.fetch_one("SELECT * FROM market_news WHERE id = ?", (item_id,))
        return _row_to_item(row) if row else None

    def list_by_company(self, company_id: int) -> list[MarketNewsItem]:
        """Return every MarketNewsItem for `company_id`, ordered by id."""
        self._ensure_url_column()
        rows = self.manager.fetch_all(
            "SELECT * FROM market_news WHERE company_id = ? ORDER BY id", (company_id,)
        )
        return [_row_to_item(row) for row in rows]
