# -*- coding: utf-8 -*-
"""
Agent 6-Element Unit Test Suite
Agent 6요소(Goal, Plan, Reason, Tool, Memory, Feedback) 개별 동작 단위 테스트
"""

import os
import sys
import unittest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.core.agent import COAGuardAgent, AgentStatus, AgentStepEvent


class TestAgentSixElements(unittest.TestCase):
    def setUp(self):
        self.agent = COAGuardAgent()
        self.sample_pdf = os.path.join(PROJECT_ROOT, "data", "sample_coas", "COA_Sample_01_Injection_PASS.pdf")

    def test_element_1_goal(self):
        """1. Goal: 에이전트의 목표가 명확히 정의되어 있고 동적 변경 가능한지 검증"""
        self.assertIsNotNone(self.agent.goal)
        self.assertIn("100%", self.agent.goal)
        self.agent.set_goal("새로운 공정 감사 목표")
        self.assertEqual(self.agent.goal, "새로운 공정 감사 목표")

    def test_element_2_planning(self):
        """2. Planning: 목표 달성을 위한 4단계 작업 분해가 올바르게 수립되는지 검증"""
        plan = self.agent.plan(self.sample_pdf)
        self.assertEqual(len(plan), 4)
        self.assertEqual(plan[0]["step_idx"], 1)
        self.assertIn("파싱", plan[0]["name"])
        self.assertIn("마스터 DB", plan[1]["name"])

    def test_element_3_reasoning(self):
        """3. Reasoning: 공차 상하한선 및 ISO 2859-1 통계 추론 검증"""
        evaluator = self.agent.tools["Tool_Tolerance_Evaluator"]
        sampling = evaluator._get_iso2859_sampling(lot_size=2500, aql_maj=1.0, aql_min=2.5)
        self.assertEqual(sampling["code_letter"], "K")
        self.assertEqual(sampling["sample_size"], 125)
        self.assertEqual(sampling["critical"]["ac"], 0)

    def test_element_4_tool_use(self):
        """4. Tool Use: 등록된 5대 도구 레지스트리가 정상 초기화되었는지 검증"""
        expected_tools = [
            "Tool_Document_Parser",
            "Tool_Tolerance_Evaluator",
            "Tool_NCR_Generator",
            "Tool_Vendor_Manager",
            "Tool_Audit_Manager"
        ]
        for t in expected_tools:
            self.assertIn(t, self.agent.tools)

    def test_element_5_memory(self):
        """5. Memory: 에이전트 상태 및 이력 보존 메모리 검증"""
        self.assertIn("session_id", self.agent.memory)
        self.assertIn("execution_history", self.agent.memory)

    def test_element_6_feedback(self):
        """6. Feedback & Self-Correction: 이벤트 스트림에서 단계별 피드백 발생 검증"""
        stream = self.agent.execute_stream(self.sample_pdf)
        events = list(stream)
        self.assertGreaterEqual(len(events), 4)
        step_elements = [e.element for e in events]
        self.assertTrue(any("문서 파싱" in el or "Tool" in el for el in step_elements))
        self.assertTrue(any("공차" in el or "Reasoning" in el for el in step_elements))
        self.assertTrue(any("품질 문서" in el or "Action" in el or "Feedback" in el for el in step_elements))


if __name__ == "__main__":
    unittest.main()
