"""
Base Collector

Defines BaseCollector, the common interface every Research Collector
implements, per project_documentation/RESEARCH_COLLECTORS.md. This phase
implements only the framework -- no real collector, no research, no API
calls, no live data collection, and no dependency on any other Research
Engine module.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseCollector(ABC):
    """The common interface every Research Collector must implement.

    Per RESEARCH_COLLECTORS.md Section 2, a collector is scoped to
    exactly one Knowledge Section, gathers only what it can find for
    that section, and returns its result -- it never verifies, approves,
    or writes to a database.

    collector_name and knowledge_section have no default: a subclass
    must define both before it can be instantiated at all. collect() has
    a default -- it always raises NotImplementedError -- since this
    phase defines the collector framework only, per IMP-05; no real
    collection logic exists yet.
    """

    @property
    @abstractmethod
    def collector_name(self) -> str:
        """This collector's own name, per RESEARCH_COLLECTORS.md Section
        6 (for example, "Financial Information Collector")."""
        raise NotImplementedError

    @property
    @abstractmethod
    def knowledge_section(self) -> str:
        """The single Knowledge Section, per KNOWLEDGE_MODEL.md, this
        collector is scoped to."""
        raise NotImplementedError

    def collect(self) -> Any:
        """Gather this collector's Knowledge Section and return a
        Collector Result.

        The default implementation always raises NotImplementedError.
        A concrete collector overrides this to perform actual
        collection -- no such override exists in this phase.
        """
        raise NotImplementedError(
            "collect() must be implemented by a concrete collector; "
            "BaseCollector defines the interface only."
        )
