"""
Sources Result

Implements SourcesResult, the structured Collected Data the Sources
Collector produces for the Sources Knowledge Section, per
project_documentation/KNOWLEDGE_MODEL.md,
project_documentation/RESEARCH_COLLECTORS.md, and
project_documentation/COLLECTOR_SOURCE_STRATEGY.md.

CollectorStatus is defined locally here, matching RESEARCH_COLLECTORS.md
Section 5's own three values exactly (Success, Partial, Failed), rather
than imported from research_engine.assembly -- that module is outside
IMP-08O's source of truth, and a real collector's own result package
should be self-contained.

Field note: IMP-08O's field list names both "Collection Timestamp" and
"Collection Time," and both "Source Name" and "Sources." These are
deliberately distinct, not duplicates:

- Source Name / Source Type / Source Category / Source Priority /
  Source Reliability / Source Language / Collection Timestamp / Source
  Notes describe the ONE external source this entry catalogs -- what it
  is, per KNOWLEDGE_MODEL.md's Sources section ("source name, source URL
  or reference, source type... retrieval date").
- Sources / Collection Time / Collector Status are the standard three
  trailing fields every Collector Result carries, per
  RESEARCH_COLLECTORS.md Section 5 -- here, Sources traces what the
  Sources Collector itself drew from to compile this catalog entry, and
  Collection Time is when this collector's own attempt ran, distinct
  from Collection Timestamp (when the catalogued source was retrieved).
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


class SourcePriority(Enum):
    """The three-tier priority a source was consulted under, per
    COLLECTOR_SOURCE_STRATEGY.md Section 3 (Priority Rules)."""

    PRIMARY = "Primary Source"
    SECONDARY = "Secondary Source"
    FALLBACK = "Fallback Source"


class SourceCategory(Enum):
    """The ten trusted Source Categories, per
    COLLECTOR_SOURCE_STRATEGY.md Section 2."""

    OFFICIAL_COMPANY_INFORMATION = "Official Company Information"
    OFFICIAL_EXCHANGE_INFORMATION = "Official Exchange Information"
    OFFICIAL_REGULATORY_INFORMATION = "Official Regulatory Information"
    GOVERNMENT_INFORMATION = "Government Information"
    OFFICIAL_FINANCIAL_STATEMENTS = "Official Financial Statements"
    OFFICIAL_CORPORATE_FILINGS = "Official Corporate Filings"
    MARKET_DATA_PROVIDERS = "Market Data Providers"
    FINANCIAL_NEWS_SOURCES = "Financial News Sources"
    SECTOR_INFORMATION_SOURCES = "Sector Information Sources"
    TECHNICAL_MARKET_DATA_SOURCES = "Technical Market Data Sources"


@dataclass
class SourcesResult:
    """The Sources Collector's Collected Data cataloging one external
    source, per IMP-08O's field list."""

    source_name: str
    source_type: str
    source_category: SourceCategory
    source_priority: SourcePriority
    source_reliability: str
    source_language: str
    collection_timestamp: datetime
    source_notes: str
    sources: List[str]
    collection_time: datetime
    collector_status: CollectorStatus
