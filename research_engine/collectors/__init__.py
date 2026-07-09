"""
Research Collectors framework.

Public entry point for the Collectors package, implementing the
framework defined in project_documentation/RESEARCH_COLLECTORS.md. No
real collector is implemented here -- only BaseCollector, CollectorRegistry,
and CollectorFactory.
"""

from .base_collector import BaseCollector
from .collector_factory import CollectorFactory, CollectorUnavailableError
from .collector_registry import (
    CollectorNotFoundError,
    CollectorRegistry,
    DuplicateCollectorError,
)

__all__ = [
    "BaseCollector",
    "CollectorRegistry",
    "CollectorFactory",
    "DuplicateCollectorError",
    "CollectorNotFoundError",
    "CollectorUnavailableError",
]
