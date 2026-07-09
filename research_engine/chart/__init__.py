"""
Chart package.

Public entry point for Chart Generator, which turns a Historical Price
Result and a Technical Analysis Result into one chart-ready
GeneratedChart, per Claude-Prompts/IMP_09D_Chart_Support.md.
"""

from .chart_generator import ChartGenerator, GeneratedChart

__all__ = [
    "ChartGenerator",
    "GeneratedChart",
]
