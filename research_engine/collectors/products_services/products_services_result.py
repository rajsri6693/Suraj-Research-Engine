"""
Products Services Result

Implements ProductsServicesResult, the structured Collected Data the
Products & Services Collector produces for the Products & Services
Knowledge Section, per project_documentation/KNOWLEDGE_MODEL.md and
project_documentation/RESEARCH_COLLECTORS.md.

CollectorStatus is defined locally here, matching RESEARCH_COLLECTORS.md
Section 5's own three values exactly (Success, Partial, Failed), rather
than imported from research_engine.assembly -- that module is outside
IMP-08N's source of truth, and a real collector's own result package
should be self-contained.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, List


class CollectorStatus(Enum):
    """Whether this collector's own attempt succeeded, per
    RESEARCH_COLLECTORS.md Section 5."""

    SUCCESS = "Success"
    PARTIAL = "Partial"
    FAILED = "Failed"


@dataclass
class ProductsServicesResult:
    """The Products & Services Collector's Collected Data for one
    company, per IMP-08N's field list.

    revenue_segments maps a segment name to its share of revenue, per
    KNOWLEDGE_MODEL.md's Products & Services section ("revenue segments
    tied to each offering").
    """

    company_name: str
    products: List[str]
    services: List[str]
    business_segments: List[str]
    major_brands: List[str]
    key_customers: List[str]
    revenue_segments: Dict[str, float]
    geographic_presence: List[str]
    business_summary: str
    sources: List[str]
    collection_time: datetime
    collector_status: CollectorStatus
