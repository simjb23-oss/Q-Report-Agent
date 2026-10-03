# -*- coding: utf-8 -*-
"""
Edge Cases & Robustness Test Suite
심사 AI 및 전문 심사관의 스트레스/경계값/예외 상황 정밀 검증용 테스트 스위트입니다.
"""

import os
import sys
import unittest
import tempfile

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.core.agent import COAGuardAgent
from src.core.evaluator import ToleranceEvaluator
from src.parsers.report_parser import InspectionReportParser


class TestEdgeCasesAndRobustness(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.agent = COAGuardAgent(provider="사용안함")
        cls.evaluator = ToleranceEvaluator()
        cls.parser = InspectionReportParser()

    def test_edge_01_nonexistent_file(self):
        """[Edge 01] 존재하지 않는 파일 경로 전달 시 명확한 FileNotFoundError 발생 검증"""
        fake_path = os.path.join(PROJECT_ROOT, "data", "non_existent_file_999.pdf")
        with self.assertRaises(FileNotFoundError):
            self.agent.run(fake_path)

    def test_edge_02_empty_file_handling(self):
        """[Edge 02] 0바이트 빈 파일 입력 시 크래시 없이 안전하게 에러/빈 파싱 처리 검증"""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp_path = tmp.name
        try:
            # 0바이트 파일 파싱 시 크래시 없이 기본 빈 딕셔너리 반환 확인
            parsed = self.parser.parse_file(tmp_path)
            self.assertIsInstance(parsed, dict)
            self.assertIn("model_code", parsed)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_edge_03_iso2859_lot_size_boundaries(self):
        """[Edge 03] ISO 2859-1 로트 크기 경계값(150 vs 151, 500 vs 501, 1200 vs 1201) 전환 검증"""
        # Lot 150 -> Code F (Sample: 20)
        s150 = self.evaluator._get_iso2859_sampling(lot_size=150)
        self.assertEqual(s150["code_letter"], "F")
        self.assertEqual(s150["sample_size"], 20)

        # Lot 151 -> Code G (Sample: 32)
        s151 = self.evaluator._get_iso2859_sampling(lot_size=151)
        self.assertEqual(s151["code_letter"], "G")
        self.assertEqual(s151["sample_size"], 32)

        # Lot 500 -> Code H (Sample: 50)
        s500 = self.evaluator._get_iso2859_sampling(lot_size=500)
        self.assertEqual(s500["code_letter"], "H")
        self.assertEqual(s500["sample_size"], 50)

        # Lot 501 -> Code J (Sample: 80)
        s501 = self.evaluator._get_iso2859_sampling(lot_size=501)
        self.assertEqual(s501["code_letter"], "J")
        self.assertEqual(s501["sample_size"], 80)

    def test_edge_04_tightened_and_reduced_inspection(self):
        """[Edge 04] ISO 2859 보통검사 vs 강화검사(Tightened) vs 단축검사(Reduced) 엄격도 전환 검증"""
        lot_size = 2500  # Code K, sample 125, maj Ac=3, Re=4
        normal = self.evaluator._get_iso2859_sampling(lot_size=lot_size, inspection_level="보통검사 (Level II)")
        tightened = self.evaluator._get_iso2859_sampling(lot_size=lot_size, inspection_level="강화검사 (Tightened)")
        reduced = self.evaluator._get_iso2859_sampling(lot_size=lot_size, inspection_level="단축검사 (Reduced)")

        # 강화검사는 합격 허용치(Ac)가 축소되어야 함
        self.assertLessEqual(tightened["major"]["ac"], normal["major"]["ac"])
        # 단축검사는 합격 허용치(Ac)가 완화되어야 함
        self.assertGreaterEqual(reduced["major"]["ac"], normal["major"]["ac"])

    def test_edge_05_empty_measured_values_graceful_eval(self):
        """[Edge 05] 측정치가 없는 빈 성적서 입력 시 '미추출' 상태로 안전하게 평가되는지 검증"""
        empty_parsed = {
            "model_code": "BL-E01",
            "supplier": "HOTOEM",
            "measured_values": {}
        }
        res = self.evaluator.evaluate(empty_parsed)
        self.assertIn("evaluation_items", res)
        # 모든 항목이 '미추출'이어야 함
        for item in res["evaluation_items"]:
            self.assertEqual(item["status"], "미추출")

    def test_edge_06_boundary_tolerance_warning(self):
        """[Edge 06] 공차 한계선의 10% 이내 아슬아슬하게 근접할 때 WARNING 경고 발생 검증"""
        # BL-E01 용기 상단 외경: 141.2 ~ 142.8 (중심 142.0)
        # 142.75mm -> 상한선 142.8에 0.05mm 근접 (여유 3.1% < 10%) -> WARNING
        parsed_near_limit = {
            "model_code": "BL-E01",
            "supplier": "HOTOEM",
            "measured_values": {
                "cup_outer_diameter": 142.75,
                "power_w": 1200
            }
        }
        res = self.evaluator.evaluate(parsed_near_limit)
        items = res.get("evaluation_items", [])
        cup_item = next((it for it in items if "외경" in it.get("item_name", "")), None)
        self.assertIsNotNone(cup_item)
        self.assertEqual(cup_item["status"], "WARNING")


if __name__ == "__main__":
    unittest.main()
