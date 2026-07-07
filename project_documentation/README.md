# Suraj Research Engine

## Project Overview

Suraj Research Engine is a modular research automation system. It plans research
tasks, executes research gathering, validates facts, applies AI-driven analysis,
generates scripts from research output, enforces quality control, and integrates
findings into Notion.

## Purpose

To provide a structured, extensible pipeline that turns a research topic into
verified, analyzed, production-ready content — with every stage isolated,
testable, and independently replaceable.

## High-Level Architecture

The system is organized into distinct layers, each with a single responsibility:

- Research Layer — planning what to research
- Research Execution Layer — gathering raw research data
- Fact Validation Layer — verifying accuracy of gathered data
- AI Intelligence Layer — orchestrating AI-driven analysis and generation
- Notion Integration Layer — publishing results to Notion
- Production Layer — shared infrastructure, quality control, and delivery

See `ARCHITECTURE.md` for full layer responsibilities.

## Folder Overview

- `project_configuration/` — project-level configuration
- `project_documentation/` — this documentation set
- `research_planning/` — research planning logic
- `research_execution/` — research execution logic
- `research_database/` — raw and verified research storage
- `fact_validation/` — fact-checking and validation logic
- `ai_orchestration/` — AI orchestration logic
- `research_analysis/` — research analysis logic
- `script_generation/` — script generation logic
- `quality_control/` — quality control logic
- `notion_integration/` — Notion integration logic
- `shared_core/` — shared logging, configuration, exceptions, and utilities
- `models/` — data models
- `prompts/` — prompt templates
- `logs/` — runtime logs
- `tests/` — test suites

## Development Philosophy

- One module, one responsibility.
- No hidden side effects.
- Root cause fixes only.
- Build in verifiable phases — structure, then documentation, then logic.
- Every completed phase is tested, committed, and documented before moving on.

## Future Phases

See `ROADMAP.md` for the complete phase-by-phase development plan.
