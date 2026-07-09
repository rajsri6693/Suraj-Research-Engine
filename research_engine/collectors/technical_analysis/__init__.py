"""
Technical Analysis Collector package.

Public entry point for the Technical Analysis Collector, implementing
the Technical Analysis Knowledge Section per
project_documentation/RESEARCH_COLLECTORS.md.
"""

from .technical_analysis_collector import (
    InvalidResearchTopicError,
    TechnicalAnalysisCollector,
)
from .technical_analysis_result import (
    CollectorStatus,
    TechnicalAnalysisResult,
    TechnicalChartData,
)

__all__ = [
    "TechnicalAnalysisCollector",
    "TechnicalAnalysisResult",
    "TechnicalChartData",
    "CollectorStatus",
    "InvalidResearchTopicError",
]
