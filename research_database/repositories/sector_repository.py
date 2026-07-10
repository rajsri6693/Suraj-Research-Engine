"""
Sector Repository

Provides Create, Read, and lookup operations for the Sector entity of
the Verified Knowledge Database, per DATABASE_ARCHITECTURE.md Layer 4.
The `sector` table itself already existed (research_database/schema/
sector.py, registered in database_initializer.py's SCHEMA_MODULES since
before this repository existed) -- this module only adds the CRUD
access layer for it, following the exact pattern CompanyRepository
already established. It does not add, remove, or alter any column.

This is the only module allowed to compose SQL for the `sector` table.
"""

from research_database.database_manager import DatabaseError, DatabaseManager
from research_database.schema.sector import Sector

_INSERT_UPDATE_COLUMNS = (
    "name",
    "size",
    "growth_trend",
    "dynamics_summary",
    "regulatory_environment",
    "benchmark_summary",
)


class SectorRepositoryError(Exception):
    """Raised when a Sector Repository operation fails."""


def _row_to_sector(row: dict) -> Sector:
    """Convert a raw database row into a Sector dataclass instance."""
    return Sector(**dict(row))


def _sector_to_values(sector: Sector) -> tuple:
    """Build the ordered parameter tuple for an insert or update statement."""
    return (
        sector.name,
        sector.size,
        sector.growth_trend,
        sector.dynamics_summary,
        sector.regulatory_environment,
        sector.benchmark_summary,
    )


class SectorRepository:
    """Repository for Sector entity operations, backed exclusively by
    DatabaseManager."""

    def __init__(self, manager: DatabaseManager) -> None:
        self.manager = manager

    def create(self, sector: Sector) -> Sector:
        """Insert a new Sector record. The `id` on the given Sector is
        ignored; the returned Sector carries the database-assigned id."""
        columns = ", ".join(_INSERT_UPDATE_COLUMNS)
        placeholders = ", ".join("?" for _ in _INSERT_UPDATE_COLUMNS)

        try:
            with self.manager.transaction() as tx:
                cursor = tx.execute(
                    f"INSERT INTO sector ({columns}) VALUES ({placeholders})",
                    _sector_to_values(sector),
                )
                new_id = cursor.lastrowid
        except DatabaseError as error:
            raise SectorRepositoryError(f"Failed to create sector: {error}") from error

        return self.get_by_id(new_id)

    def get_by_id(self, sector_id: int) -> Sector | None:
        """Return a Sector by its primary key, or None if not found."""
        row = self.manager.fetch_one("SELECT * FROM sector WHERE id = ?", (sector_id,))
        return _row_to_sector(row) if row else None

    def get_by_name(self, name: str) -> Sector | None:
        """Return the Sector with this exact name (case-insensitive),
        or None if not found."""
        row = self.manager.fetch_one(
            "SELECT * FROM sector WHERE LOWER(name) = LOWER(?)", (name,)
        )
        return _row_to_sector(row) if row else None

    def get_or_create(self, sector: Sector) -> Sector:
        """Return the existing Sector matching `sector.name`, or create
        it if none exists yet -- Sector is a shared entity per
        DATABASE_ARCHITECTURE.md Section 3, recorded once and
        referenced by every Company that belongs to it."""
        existing = self.get_by_name(sector.name)
        if existing is not None:
            return existing
        return self.create(sector)

    def list_all(self) -> list[Sector]:
        """Return every Sector record."""
        rows = self.manager.fetch_all("SELECT * FROM sector ORDER BY name")
        return [_row_to_sector(row) for row in rows]
