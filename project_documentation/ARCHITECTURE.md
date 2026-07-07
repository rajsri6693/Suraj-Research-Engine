# Architecture

This document describes the responsibilities of each architectural layer in
Suraj Research Engine. It describes responsibilities only — no implementation
details.

## Research Layer

Responsible for determining what should be researched. Owns the definition of
research topics, scope, and objectives before any data gathering begins.

## Research Execution Layer

Responsible for carrying out the research plan. Owns the process of gathering
raw research data from sources defined by the Research Layer.

## Fact Validation Layer

Responsible for verifying the accuracy and reliability of gathered research.
Owns the distinction between raw, unverified data and confirmed, trustworthy
data.

## AI Intelligence Layer

Responsible for orchestrating AI-driven reasoning across the pipeline. Owns
analysis of validated research and generation of derived content such as
scripts.

## Notion Integration Layer

Responsible for publishing and syncing research outputs into Notion. Owns the
mapping between internal research artifacts and their external representation.

## Production Layer

Responsible for cross-cutting production concerns: quality control, shared
infrastructure (logging, configuration, exceptions, utilities), and the
conditions under which output is considered release-ready.
