"""
Technical Analysis Result

Implements TechnicalAnalysisResult, the structured Collected Data the
Technical Analysis Collector produces for the Technical Analysis
Knowledge Section, per project_documentation/KNOWLEDGE_MODEL.md and
project_documentation/RESEARCH_COLLECTORS.md.

CollectorStatus is defined locally here, matching RESEARCH_COLLECTORS.md
Section 5's own three values exactly (Success, Partial, Failed), rather
than imported from research_engine.assembly -- that module is outside
IMP-08E's source of truth, and a real collector's own result package
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
class TechnicalAnalysisResult:
    """The Technical Analysis Collector's Collected Data for one
    company, per IMP-08E's field list.

    moving_averages maps a label (for example "50-day", "200-day") to
    its computed value, since more than one moving average is normally
    reported together.
    """

    current_price: float
    support_levels: List[float]
    resistance_levels: List[float]
    trend: str
    moving_averages: Dict[str, float]
    rsi: float
    macd: str
    volume_analysis: str
    pattern: str
    technical_summary: str
    sources: List[str]
    collection_time: datetime
    collector_status: CollectorStatus
