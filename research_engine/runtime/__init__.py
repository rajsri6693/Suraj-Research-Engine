"""
Research Runtime

Public entry point for the Research Engine's collector-wiring helper,
per Claude-Prompts/IMP_10I_Research_Runtime.md and its follow-up
architecture refactor. This package used to also hold ResearchRuntime,
a second orchestrator that re-implemented IntegrationEngine.run()'s own
Planner/Workflow/Collectors/Assembly/Verification/Chart sequence purely
to obtain live-APIManager-bound collectors. That duplication has been
removed: research_engine.integration.integration_engine.IntegrationEngine
now accepts optional `registry`/`factory` constructor parameters for
exactly that purpose (fully backward compatible -- every existing
zero-arg `IntegrationEngine()` caller is unaffected), so
IntegrationEngine.run() is once again the single orchestration path.

What remains here -- build_collector_registry()/build_collector_factory()
-- is not orchestration; it is the one piece of wiring logic that is
still genuinely needed regardless of which class orchestrates: since
CollectorFactory.create_collector() always instantiates a registered
class with zero constructor arguments, threading one shared APIManager
into every collector that accepts one still requires registering a
small bound subclass per collector. research.py at the repository root
builds a registry/factory via this module and passes the factory
straight into `IntegrationEngine(factory=...)`.
"""

from __future__ import annotations

from .collector_wiring import build_collector_factory, build_collector_registry

__all__ = [
    "build_collector_registry",
    "build_collector_factory",
]
