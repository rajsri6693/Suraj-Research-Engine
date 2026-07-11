"""
Market News Result

Implements MarketNewsResult, the structured Collected Data the Market
News Collector produces for the Market News Knowledge Section, per
project_documentation/KNOWLEDGE_MODEL.md and
project_documentation/RESEARCH_COLLECTORS.md.

CollectorStatus is defined locally here, matching RESEARCH_COLLECTORS.md
Section 5's own three values exactly (Success, Partial, Failed), rather
than imported from research_engine.assembly -- that module is outside
IMP-08C's source of truth, and a real collector's own result package
should be self-contained.

Per Claude-Prompts/IMP_10F_NewsAPI_Integration.md's follow-up URL
requirement, `url` was added after IMP-08C's original field list to
carry the source article's own URL through to the persisted News
record. It defaults to "" (rather than being required) so this remains
a purely additive change -- any existing construction of
MarketNewsResult that predates this field keeps working unchanged.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import List


class CollectorStatus(Enum):
    """Whether this collector's own attempt succeeded, per
    RESEARCH_COLLECTORS.md Section 5."""

    SUCCESS = "Success"
    PARTIAL = "Partial"
    FAILED = "Failed"


@dataclass
class MarketNewsResult:
    """The Market News Collector's Collected Data for one news item, per
    IMP-08C's field list."""

    news_title: str
    news_summary: str
    news_category: str
    published_time: datetime
    source_name: str
    related_companies: List[str]
    related_sectors: List[str]
    impact: str
    sources: List[str]
    collection_time: datetime
    collector_status: CollectorStatus
    url: str = ""
