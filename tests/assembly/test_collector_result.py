"""Unit tests for research_engine.assembly.collector_result."""

import unittest
from datetime import datetime

from research_engine.assembly.collector_result import CollectorResult, CollectorStatus
from research_engine.planner.research_plan import KnowledgeSection


class TestCollectorStatusVocabulary(unittest.TestCase):
    def test_three_statuses_defined(self):
        self.assertEqual(
            {status.value for status in CollectorStatus},
            {"Success", "Partial", "Failed"},
        )


class TestCollectorResultConstruction(unittest.TestCase):
    def test_holds_every_field(self):
        result = CollectorResult(
            collector_name="Financial Information Collector",
            knowledge_section=KnowledgeSection.FINANCIAL_INFORMATION,
            collected_knowledge="Q4 revenue of 412 crore.",
            sources=["Quarterly filing, retrieved 2026-07-09"],
            collection_time=datetime(2026, 7, 9, 9, 6, 0),
            collector_status=CollectorStatus.SUCCESS,
        )
        self.assertEqual(result.collector_name, "Financial Information Collector")
        self.assertEqual(result.knowledge_section, KnowledgeSection.FINANCIAL_INFORMATION)
        self.assertEqual(result.collected_knowledge, "Q4 revenue of 412 crore.")
        self.assertEqual(result.sources, ["Quarterly filing, retrieved 2026-07-09"])
        self.assertEqual(result.collector_status, CollectorStatus.SUCCESS)

    def test_failed_result_can_carry_no_collected_knowledge(self):
        result = CollectorResult(
            collector_name="Technical Analysis Collector",
            knowledge_section=KnowledgeSection.TECHNICAL_ANALYSIS,
            collected_knowledge=None,
            sources=[],
            collection_time=datetime(2026, 7, 9, 9, 9, 0),
            collector_status=CollectorStatus.FAILED,
        )
        self.assertIsNone(result.collected_knowledge)
        self.assertEqual(result.sources, [])


if __name__ == "__main__":
    unittest.main()
