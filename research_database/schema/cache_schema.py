"""
Cache Schema

Logical schema for storing reusable research results, to avoid redundant
research execution for previously researched topics.
"""

from dataclasses import dataclass


@dataclass
class CacheEntry:
    """Represents a single cached research result.

    Purpose: store reusable research so previously researched topics can be
    served without repeating the full research pipeline.
    """

    id: int  # Unique identifier for the cache entry.
    cache_key: str  # Lookup key used to retrieve this cached entry.
    cache_value: str  # Cached research result payload.
    expires_at: str  # Timestamp after which this cache entry is invalid.
    created_at: str  # Timestamp when this cache entry was created.


TABLE_NAME = "cache"

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cache_key TEXT NOT NULL UNIQUE,
    cache_value TEXT NOT NULL,
    expires_at TEXT,
    created_at TEXT NOT NULL
)
"""
