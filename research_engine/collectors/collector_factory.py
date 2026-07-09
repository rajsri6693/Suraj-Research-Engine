"""
Collector Factory

Implements CollectorFactory, which creates collector instances by looking
them up in a CollectorRegistry, per
project_documentation/RESEARCH_COLLECTORS.md. It performs no research,
calls no APIs, and collects no live data -- it only instantiates whatever
collector class is registered for a Knowledge Section.
"""

from __future__ import annotations

from .base_collector import BaseCollector
from .collector_registry import CollectorRegistry


class CollectorUnavailableError(Exception):
    """Raised when no collector is available for the requested Knowledge
    Section."""


class CollectorFactory:
    """Creates collector instances for a Knowledge Section, using a
    CollectorRegistry to look up which collector class to instantiate."""

    def __init__(self, registry: CollectorRegistry) -> None:
        self._registry = registry

    def is_available(self, knowledge_section: str) -> bool:
        """Validate collector availability.

        True only if a collector is registered for `knowledge_section`.
        """
        return knowledge_section in self._registry.list_collectors()

    def create_collector(self, knowledge_section: str) -> BaseCollector:
        """Create Collector.

        Looks up the collector class registered for `knowledge_section`
        and returns a fresh instance of it. Raises
        CollectorUnavailableError if no collector is registered for that
        section.
        """
        if not self.is_available(knowledge_section):
            raise CollectorUnavailableError(
                f"No collector is available for '{knowledge_section}'."
            )
        collector_class = self._registry.get_collector(knowledge_section)
        return collector_class()
