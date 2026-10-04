# -*- coding: utf-8 -*-
"""
Audit History Manager (성적서 검사 누적 이력 관리자)
신규 성적서 판정 시 영구 DB(data/audit_history.json)에 감사 로그 누적 저장 및 이력 조회
"""

import os
import json
from datetime import datetime
from typing import Dict, Any, List

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DATA_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "..", "data"))
if not os.path.exists(PROJECT_DATA_DIR):
    PROJECT_DATA_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "data"))
DATA_DIR = PROJECT_DATA_DIR
HISTORY_FILE = os.path.join(DATA_DIR, "audit_history.json")

CONFIG_FILE = os.path.join(DATA_DIR, "sheet_config.json")

def get_sheet_config() -> dict:
    """구글 시트 연동 설정 로드"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"webhook_url": "", "sheet_url": ""}

def sync_to_google_sheet(record: dict, webhook_url: str = None) -> (bool, str):
    """단일 검사 기록을 구글 스프레드시트에 전송 (모듈 레벨 래퍼)"""
    mgr = AuditManager()
    return mgr.sync_to_google_sheet(record, webhook_url)

def sync_all_to_google_sheet(history: list = None, webhook_url: str = None) -> dict:
    """누적된 전체 이력을 구글 시트에 일괄 동기화 (모듈 레벨 래퍼)"""
    mgr = AuditManager()
    if not webhook_url:
        cfg = get_sheet_config()
        webhook_url = cfg.get("webhook_url", "")
    
    if not webhook_url:
        return {"status": "error", "message": "구글 웹훅 URL이 설정되지 않았습니다.", "count": 0}
    
    target_list = history if history is not None else mgr.load_all()
    if not target_list:
        return {"status": "warning", "message": "동기화할 검사 이력이 없습니다.", "count": 0}
        
    cnt = 0
    for item in reversed(target_list):
        ok, _ = mgr.sync_to_google_sheet(item, webhook_url)
        if ok:
            cnt += 1
    return {"status": "success", "count": cnt, "message": f"{cnt}건 동기화 성공"}

def save_sheet_config(webhook_url: str, sheet_url: str = "") -> bool:
    """구글 시트 연동 설정 저장"""
    try:
        data = {"webhook_url": webhook_url.strip(), "sheet_url": sheet_url.strip()}
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Error saving sheet config: {e}")
        return False



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


    def get_historical_precautions(self, supplier: str, model_code: str, eval_result: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        AI 기반 과거 이력 바탕 중점 유의점 및 리스크 진단 도출
        """
        history = self.load_all()
        supp_clean = (supplier or "").strip()
        model_clean = (model_code or "").strip()

        # 1. 협력사 / 모델 과거 이력 필터링 (키워드 매칭)
        supp_matched = []
        for h in history:
            h_supp = str(h.get("supplier", ""))
            h_model = str(h.get("model_code", ""))
            
            # 협력사명 부분 일치
            supp_match = False
            for token in [supp_clean, supp_clean.split()[0] if supp_clean else ""]:
                token = token.replace("(", "").replace(")", "").replace("주", "").strip()
                if token and (token in h_supp or h_supp in token):
                    supp_match = True
                    break
            
            # 모델 일치
            model_match = bool(model_clean and (model_clean in h_model or h_model in model_clean))
            
            if supp_match or model_match:
                supp_matched.append(h)

        if not supp_matched:
            supp_matched = history[:4]

        total_cnt = len(supp_matched)
        fail_cnt = sum(1 for h in supp_matched if h.get("final_verdict") == "FAIL")
        pass_cnt = total_cnt - fail_cnt
        defect_rate = round((fail_cnt / total_cnt * 100), 1) if total_cnt > 0 else 0.0

        # 2. 과거 발생 결함 및 유의 항목 집계
        past_defect_notes = []
        for h in supp_matched:
            if h.get("final_verdict") == "FAIL" and h.get("note"):
                past_defect_notes.append(f"[{h.get('timestamp', '')[:10]}] {h.get('note')}")

        # 3. AI 유의점 및 권고 대책 수립
        precautions = []
        action_guides = []
        risk_grade = "주의 (관찰 요망)"

        if fail_cnt > 0:
            risk_grade = "고위험 (집중 검사 대상)" if defect_rate >= 30.0 else "주의 (중점 관리)"
            precautions.append(f"과거 동일 협력사/모델에서 부적합(FAIL) 이력이 {fail_cnt}건 확인되었습니다 (누적 불합격률: {defect_rate}%).")
            precautions.append(f"주요 과거 결함 이력: {past_defect_notes[0] if past_defect_notes else '공차 한계 초과 및 이탈'}")
            action_guides.append("동일 결함 재발 방지를 위해 과거 이탈 검사항목의 실측치 마진(Cpk 1.33 이상 여부)을 2차 교차 검증하십시오.")
            action_guides.append("차기 출하 로트에 대해 ISO 2859-1 엄격검사(Tightened) 적용 및 시료수 1.5배 확대를 권고합니다.")
        else:
            risk_grade = "양호 (안정적 관리)"
            precautions.append(f"해당 공급사/모델의 과거 감사 이력({total_cnt}건) 기준 공정 안정성이 양호(합격률 100%)하게 유지되고 있습니다.")
            precautions.append("다만 기온/사출압/가공 툴 마모 등 계절적/환경적 요인에 따른 미세 공차 편차(Drift)를 주기적으로 모니터링하십시오.")
            action_guides.append("현재 합격 품질 수준을 유지하며 일반검사(Level II) 표준 샘플링을 지속하십시오.")
            action_guides.append("성적서 실측치 평균이 공차 상/하한선(LSL/USL)의 80% 이상에 접근 시 조기 경보를 가동하십시오.")

        # 현재 성적서의 평가 결과가 불합격인 경우 긴급 유의점 추가
        if eval_result and eval_result.get("final_verdict") == "FAIL":
            precautions.insert(0, "● [긴급 경보] 당일 제출된 성적서에서 치명 공차 이탈 또는 데이터 이상이 발견되었습니다.")
            action_guides.insert(0, "금일 로트는 즉시 ERP 입고 락(Lock)을 걸고 협력사에 공식 부적합 통보서(NCR)를 24시간 이내 송부하십시오.")

        return {
            "supplier": supp_clean,
            "model_code": model_clean,
            "total_inspections": total_cnt,
            "fail_count": fail_cnt,
            "pass_count": pass_cnt,
            "defect_rate": defect_rate,
            "risk_grade": risk_grade,
            "precautions": precautions,
            "action_guides": action_guides,
            "past_defect_notes": past_defect_notes[:3]
        }

    def sync_to_google_sheet(self, record: Dict[str, Any], webhook_url: str = None) -> (bool, str):
        """단일 검사 기록을 구글 스프레드시트에 전송 (Google Apps Script Webhook)"""
        if not webhook_url:
            cfg = get_sheet_config()
            webhook_url = cfg.get("webhook_url", "")
        
        if not webhook_url:
            return False, "Webhook URL이 설정되지 않았습니다."
        
        try:
            import requests
            payload = {"action": "append", "data": record}
            resp = requests.post(webhook_url, json=payload, timeout=8)
            if resp.status_code in [200, 302]:
                return True, "구글 스프레드시트 동기화 성공"
            return False, f"HTTP 상태 코드: {resp.status_code}"
        except Exception as e:
            return False, f"동기화 오류: {str(e)}"

    def sync_all_to_google_sheet(self, webhook_url: str = None) -> (int, str):
        """누적된 전체 이력을 구글 시트에 일괄 동기화"""
        history = self.load_all()
        if not history:
            return 0, "동기화할 이력이 없습니다."
        
        success_count = 0
        for item in reversed(history):
            ok, _ = self.sync_to_google_sheet(item, webhook_url)
            if ok:
                success_count += 1
        return success_count, f"{success_count}건 동기화 완료"


    def fetch_sheet_data_via_csv(self) -> List[Dict[str, Any]]:
        """구글 스프레드시트 발행(pub) CSV 엔드포인트에서 라이브 데이터 추출"""
        cfg = get_sheet_config()
        sheet_url = cfg.get("sheet_url", "")
        if not sheet_url:
            return []
            
        csv_url = sheet_url
        if "pubhtml" in sheet_url:
            csv_url = sheet_url.replace("pubhtml", "pub?output=csv")
        elif "docs.google.com/spreadsheets/d/" in sheet_url and "/edit" in sheet_url:
            doc_id = sheet_url.split("/d/")[1].split("/")[0]
            csv_url = f"https://docs.google.com/spreadsheets/d/{doc_id}/export?format=csv"
            
        try:
            import urllib.request
            import csv
            import io
            req = urllib.request.Request(csv_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=6) as resp:
                if resp.status == 200:
                    raw_text = resp.read().decode("utf-8")
                    reader = csv.DictReader(io.StringIO(raw_text))
                    return list(reader)
        except Exception as e:
            print(f"Error fetching sheet data via CSV: {e}")
            
        return []
