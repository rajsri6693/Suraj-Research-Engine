"""
Collector Registry

Implements CollectorRegistry, the lookup and lifecycle-tracking structure
for registered collector classes, per
project_documentation/RESEARCH_COLLECTORS.md. It holds no data of its
own -- only which collector class is registered for which Knowledge
Section.
"""

from __future__ import annotations

from typing import Dict, List, Type

from .base_collector import BaseCollector


class DuplicateCollectorError(Exception):
    """Raised when attempting to register a collector for a Knowledge
    Section that already has a registered collector -- one collector per
    section, per RESEARCH_COLLECTORS.md Section 6."""


class CollectorNotFoundError(Exception):
    """Raised when looking up or unregistering a collector for a
    Knowledge Section that has no registered collector."""


class CollectorRegistry:
    """Tracks which collector class is registered for which Knowledge
    Section. One collector per Knowledge Section, per
    RESEARCH_COLLECTORS.md Section 6 -- registration never allows a
    second collector class to replace one already registered.
    """

    def __init__(self) -> None:
        self._collectors: Dict[str, Type[BaseCollector]] = {}

    def register_collector(
        self, knowledge_section: str, collector_class: Type[BaseCollector]
    ) -> None:
        """Register Collector.

        Raises TypeError if `collector_class` is not a BaseCollector
        subclass, and DuplicateCollectorError if a collector is already
        registered for `knowledge_section`.
        """
        if not (isinstance(collector_class, type) and issubclass(collector_class, BaseCollector)):
            raise TypeError(
                f"'{collector_class!r}' is not a BaseCollector subclass."
            )
        if knowledge_section in self._collectors:
            raise DuplicateCollectorError(
                f"A collector is already registered for '{knowledge_section}'."
            )
        self._collectors[knowledge_section] = collector_class

    def unregister_collector(self, knowledge_section: str) -> None:
        """Unregister Collector.

        Raises CollectorNotFoundError if no collector is registered for
        `knowledge_section`.
        """
        if knowledge_section not in self._collectors:
            raise CollectorNotFoundError(
                f"No collector is registered for '{knowledge_section}'."
            )
        del self._collectors[knowledge_section]

    def get_collector(self, knowledge_section: str) -> Type[BaseCollector]:
        """Get Collector.

        Raises CollectorNotFoundError if no collector is registered for
        `knowledge_section`.
        """
        try:
            return self._collectors[knowledge_section]
        except KeyError as exc:
            raise CollectorNotFoundError(
                f"No collector is registered for '{knowledge_section}'."
            ) from exc

    def list_collectors(self) -> List[str]:
        """List Collectors.

        Returns every Knowledge Section that currently has a registered
        collector.
        """
        return list(self._collectors.keys())
