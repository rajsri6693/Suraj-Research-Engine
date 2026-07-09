# Research Engine
# IMP-09D - Chart Support
# Version 1.0

Read and execute this document completely.

Work ONLY inside the current repository.

Do NOT modify anything outside this repository.

--------------------------------------------------

OBJECTIVE

Implement complete Chart Support for the Research Engine.

The system must automatically detect when the user requests a chart in the Research Topic and include chart data in the research pipeline.

Examples:

BEL
→ No Chart

BEL chart
→ Chart Required

BEL with chart
→ Chart Required

BEL analysis with chart
→ Chart Required

BEL vs HAL with chart
→ Chart Required

--------------------------------------------------

SOURCE OF TRUTH

Use ONLY

project_documentation/

RESEARCH_INPUT_STANDARD.md

RESEARCH_PLANNER.md

RESEARCH_WORKFLOW.md

KNOWLEDGE_MODEL.md

--------------------------------------------------

IMPLEMENT

Update the existing modules only where required.

Do NOT create a separate Planner.

--------------------------------------------------

Planner

Add

chart_required : bool

Planner must automatically detect chart requests using natural-language keywords such as:

chart

with chart

price chart

technical chart

candlestick chart

--------------------------------------------------

Historical Price Collector

Extend the result model to support chart generation.

Include

OHLC Data

Timeframe

Chart Dataset

--------------------------------------------------

Technical Analysis Collector

Extend the result model.

Include

Chart Data

Chart Type

Indicators Available

--------------------------------------------------

Chart Generator

Create

research_engine/chart/

    __init__.py

    chart_generator.py

Responsibilities

Receive Historical Price data.

Generate chart-ready data.

No external chart libraries.

No PNG generation.

No image rendering.

Return structured chart data only.

--------------------------------------------------

Integration Engine

If

chart_required=True

then

Historical Price Collector

↓

Technical Analysis Collector

↓

Chart Generator

↓

Research Package

Otherwise

skip Chart Generator completely.

--------------------------------------------------

Human Review

Attach chart data to the Review Package.

Human Review must expose

Chart Available

Chart Type

Chart Dataset

--------------------------------------------------

Approval

Persist chart metadata together with the approved research.

--------------------------------------------------

DO NOT

Generate images.

Call external chart services.

Use JavaScript.

Use React.

Generate HTML.

Generate PNG.

Only prepare structured chart data.

--------------------------------------------------

UNIT TESTS

Verify

Planner detects chart keywords.

chart_required is correct.

Chart Generator runs only when required.

Chart data attached to Research Package.

Chart metadata saved after approval.

Existing tests continue to pass.

--------------------------------------------------

VERIFY

Confirm

1. Planner updated.

2. Historical Price Collector updated.

3. Technical Analysis Collector updated.

4. Chart Generator created.

5. Integration Engine updated.

6. Human Review updated.

7. Approval updated.

8. Existing modules unchanged except where required.

9. All tests pass.

10. Compilation passes.

Print the final report.