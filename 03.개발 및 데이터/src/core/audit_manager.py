# -*- coding: utf-8 -*-
"""
Audit History Manager (성적서 검사 누적 이력 관리자)
신규 성적서 판정 시 영구 DB(data/audit_history.json)에 감사 로그 누적 저장 및 이력 조회
"""

import os
import json
from datetime import datetime
from typing import Dict, Any, List

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
HISTORY_FILE = os.path.join(DATA_DIR, "audit_history.json")


def get_default_history() -> List[Dict[str, Any]]:
    """초기 누적 이력 시드 데이터 (과거 실적)"""
    return [
        {
            "id": "AUDIT-2026-0001",
            "timestamp": "2026-09-28 09:15:22",
            "filename": "Blender Inspection Report(ACCEPT)BL-E01EMG 20250911.pdf",
            "supplier": "HOTOEM",
            "model_code": "BL-E01",
            "product_name": "초고속 블렌더 BL-E01",
            "report_no": "HT-25-0911",
            "order_qty": 3000,
            "sample_qty": 125,
            "final_verdict": "PASS",
            "status_label": "[정상]",
            "defect_count": 0,
            "note": "치수 4종 및 전기안전 전수 기준 만족. 정상 입고 가결."
        },
        {
            "id": "AUDIT-2026-0002",
            "timestamp": "2026-09-28 11:40:15",
            "filename": "Blender Inspection Report(REJECT)BL-E01GMG 20260811.pdf",
            "supplier": "HOTOEM",
            "model_code": "BL-E01",
            "product_name": "초고속 블렌더 BL-E01",
            "report_no": "HT-26-0811",
            "order_qty": 2500,
            "sample_qty": 125,
            "final_verdict": "FAIL",
            "status_label": "[부적합]",
            "defect_count": 2,
            "note": "칼날-바닥 간극 기준(2.2~3.8mm) 이탈(4.1mm). 출하보류 및 NCR 발행."
        },
        {
            "id": "AUDIT-2026-0003",
            "timestamp": "2026-09-29 14:10:04",
            "filename": "Blender Inspection Report(ACCEPT)BL-D01ATG 20240823.pdf",
            "supplier": "MYLUX",
            "model_code": "BL-D01",
            "product_name": "진공 블렌더 BL-D01",
            "report_no": "ML-24-0823",
            "order_qty": 1800,
            "sample_qty": 80,
            "final_verdict": "PASS",
            "status_label": "[정상]",
            "defect_count": 0,
            "note": "베이스 외경 및 소비전력 규격 합치. 입고 승인."
        },
        {
            "id": "AUDIT-2026-0004",
            "timestamp": "2026-09-29 16:45:50",
            "filename": "COA_Sample_02_Injection_NG_Tolerance.pdf",
            "supplier": "MYLUX",
            "model_code": "BL-D01",
            "product_name": "진공 블렌더 BL-D01",
            "report_no": "QA-2026-0922-B09",
            "order_qty": 2000,
            "sample_qty": 80,
            "final_verdict": "FAIL",
            "status_label": "[부적합]",
            "defect_count": 1,
            "note": "본체 베이스 외경 186.2mm 검출 (+0.4mm 공차 초과). 표준 NCR/8D 요구."
        },
        {
            "id": "AUDIT-2026-0005",
            "timestamp": "2026-09-30 10:20:18",
            "filename": "240708-티메이커_TM-HB1FWH_출하검사성적서.pdf",
            "supplier": "크리스탈",
            "model_code": "TM-HB1",
            "product_name": "스마트 티마스터 TM-HB1",
            "report_no": "CR-24-0708",
            "order_qty": 1500,
            "sample_qty": 80,
            "final_verdict": "PASS",
            "status_label": "[정상]",
            "defect_count": 0,
            "note": "전원코드 인장강도 63.5N (하한 60N 이상 만족). 정상 승인."
        }
    ]


class AuditManager:
    def __init__(self, data_file: str = HISTORY_FILE):
        self.data_file = data_file
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        if not os.path.exists(self.data_file):
            self.save_all(get_default_history())

    def load_all(self) -> List[Dict[str, Any]]:
        """누적 감사 이력 전체 조회"""
        if not os.path.exists(self.data_file):
            return get_default_history()
        try:
            with open(self.data_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return get_default_history()

    def save_all(self, history: List[Dict[str, Any]]) -> bool:
        """누적 이력 전체 저장"""
        try:
            with open(self.data_file, "w", encoding="utf-8") as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Error saving audit history: {e}")
            return False

    def add_record(self, file_path: str, parsed_data: Dict[str, Any], eval_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        신규 성적서 검토 완료 시 즉시 영구 저장소에 추가
        """
        history = self.load_all()
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        filename = os.path.basename(file_path) if file_path else "Unknown_Report.pdf"
        
        verdict = eval_result.get("final_verdict", "FAIL")
        is_pass = (verdict == "PASS")
        status_label = "[정상]" if is_pass else "[부적합]"
        
        reasons = eval_result.get("ng_reasons", [])
        defect_count = len(reasons)
        note = "모든 공차 규격 기준 만족. 입고 승인." if is_pass else (", ".join(reasons) if reasons else "공차 한계 초과 결함")
        
        seq_num = len(history) + 1
        new_entry = {
            "id": f"AUDIT-2026-{seq_num:04d}",
            "timestamp": now_str,
            "filename": filename,
            "supplier": eval_result.get("supplier", "협력사"),
            "model_code": eval_result.get("model_code", "N/A"),
            "product_name": eval_result.get("product_name", "N/A"),
            "report_no": parsed_data.get("report_no", "N/A"),
            "order_qty": parsed_data.get("order_qty", 0),
            "sample_qty": parsed_data.get("sample_qty", 0),
            "final_verdict": verdict,
            "status_label": status_label,
            "defect_count": defect_count,
            "note": note
        }
        
        # 최신 건이 위로 오도록 앞에 추가
        history.insert(0, new_entry)
        self.save_all(history)
        return new_entry

    def get_summary_kpis(self) -> Dict[str, Any]:
        """누적 검사 통계 산출"""
        history = self.load_all()
        total = len(history)
        pass_count = sum(1 for h in history if h.get("final_verdict") == "PASS")
        fail_count = sum(1 for h in history if h.get("final_verdict") == "FAIL")
        hold_count = total - (pass_count + fail_count)
        pass_rate = round((pass_count / total * 100), 1) if total > 0 else 0.0
        
        return {
            "total_inspections": total,
            "pass_count": pass_count,
            "fail_count": fail_count,
            "hold_count": hold_count,
            "pass_rate": pass_rate
        }
