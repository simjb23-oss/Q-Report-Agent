# -*- coding: utf-8 -*-
"""
Vendor / Supplier Management Master
협력업체(공급사) 등록, 조회, 수정 및 품질 이력 관리 모듈
"""

import os
import json
from datetime import datetime
from typing import Dict, Any, List, Optional

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
VENDORS_FILE = os.path.join(DATA_DIR, "vendors.json")

# 초기 기본 협력업체 데이터 (최초 실행 시 생성)
DEFAULT_VENDORS = [
    {
        "vendor_code": "VND-HOTOEM",
        "vendor_name": "HOTOEM Electronics Co., Ltd.",
        "short_name": "HOTOEM",
        "country": "🇨🇳 중국 (선전)",
        "category": "블렌더 / 믹서",
        "supplied_models": ["BL-E01"],
        "inspection_spec": "QA-25-109-01 (ISO 2859-1 Level II)",
        "quality_grade": "A",
        "status": "정상 가동",
        "contact_person": "Zhang Wei (품질팀장)",
        "contact_email": "zhang.wei@hotoem.cn",
        "contact_phone": "+86-755-8932-1100",
        "registered_date": "2024-03-15",
        "last_inspection_date": "2026-09-28",
        "total_inspections": 15,
        "pass_count": 14,
        "ncr_count": 1,
        "notes": "초고속 모터 특화 공급사. ISO 9001/14001 인증 보유."
    },
    {
        "vendor_code": "VND-MYLUX",
        "vendor_name": "MYLUX Appliance Industrial",
        "short_name": "MYLUX",
        "country": "🇨🇳 중국 (닝보)",
        "category": "진공 블렌더 / 콤팩트 믹서",
        "supplied_models": ["BL-D01", "BL-C01"],
        "inspection_spec": "QA-23-109-012 (ISO 2859-1)",
        "quality_grade": "B",
        "status": "중점 관리",
        "contact_person": "Lin Xiao (해외품질책임)",
        "contact_email": "lin.xiao@mylux.com",
        "contact_phone": "+86-574-8712-4433",
        "registered_date": "2023-08-20",
        "last_inspection_date": "2026-09-28",
        "total_inspections": 18,
        "pass_count": 15,
        "ncr_count": 3,
        "notes": "용기 사출 외경 공차 편차 발생 이력 있어 강화검사 적용 중."
    },
    {
        "vendor_code": "VND-CRASTAL",
        "vendor_name": "(주)크리스탈 일렉트릭",
        "short_name": "CRASTAL",
        "country": "🇰🇷 대한민국 (경남 창원)",
        "category": "전기주전자 / 스마트 티마스터",
        "supplied_models": ["TM-HB1"],
        "inspection_spec": "QA-19-TM-003 (ISO 2859-1 Level I)",
        "quality_grade": "A",
        "status": "정상 가동",
        "contact_person": "김진석 팀장 (품질관리부)",
        "contact_email": "jskim@crastal.co.kr",
        "contact_phone": "055-288-4900",
        "registered_date": "2022-11-10",
        "last_inspection_date": "2026-09-28",
        "total_inspections": 12,
        "pass_count": 11,
        "ncr_count": 1,
        "notes": "국내 핵심 전략 협력사. 온도 제어 정밀도 우수."
    },
    {
        "vendor_code": "VND-PHILP",
        "vendor_name": "余姚市菲尔浦电器有限公司 (필립전기)",
        "short_name": "PHILP (필립전기)",
        "country": "🇨🇳 중국 (저장성 위야오)",
        "category": "전동 스퀴저 / 착즙기",
        "supplied_models": ["CJ-B03"],
        "inspection_spec": "MIL-STD-105E II",
        "quality_grade": "B",
        "status": "정상 가동",
        "contact_person": "Chen Ming (수출품질이사)",
        "contact_email": "chen.m@philp-elec.com",
        "contact_phone": "+86-574-6288-9901",
        "registered_date": "2024-01-05",
        "last_inspection_date": "2026-09-28",
        "total_inspections": 9,
        "pass_count": 8,
        "ncr_count": 1,
        "notes": "모터 저소음 구동 및 착즙 기어 설계 우수."
    }
]

class VendorManager:
    """협력업체 마스터 관리자 클래스"""
    
    def __init__(self, data_file: str = VENDORS_FILE):
        self.data_file = data_file
        self._ensure_storage()

    def _ensure_storage(self):
        """데이터 저장 디렉토리 및 초기 파일 생성"""
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        if not os.path.exists(self.data_file):
            self.save_all(DEFAULT_VENDORS)

    def load_all(self) -> List[Dict[str, Any]]:
        """모든 협력업체 목록 로드"""
        try:
            with open(self.data_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return DEFAULT_VENDORS

    def save_all(self, vendors: List[Dict[str, Any]]) -> bool:
        """협력업체 목록 전체 저장"""
        try:
            with open(self.data_file, "w", encoding="utf-8") as f:
                json.dump(vendors, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Error saving vendors: {e}")
            return False

    def get_vendor(self, vendor_code_or_name: str) -> Optional[Dict[str, Any]]:
        """코드 또는 이름(약칭 포함)으로 협력사 단건 검색"""
        vendors = self.load_all()
        query = vendor_code_or_name.strip().upper()
        for v in vendors:
            if v["vendor_code"].upper() == query:
                return v
            if v["short_name"].upper() in query or query in v["short_name"].upper():
                return v
            if query in v["vendor_name"].upper():
                return v
        return None

    def add_vendor(self, vendor_data: Dict[str, Any]) -> tuple[bool, str]:
        """
        신규 협력업체 등록
        """
        vendors = self.load_all()
        code = vendor_data.get("vendor_code", "").strip()
        name = vendor_data.get("vendor_name", "").strip()

        if not code or not name:
            return False, "업체 코드와 업체명은 필수 입력 항목입니다."

        # 중복 검사
        for v in vendors:
            if v["vendor_code"].upper() == code.upper():
                return False, f"이미 등록된 업체 코드('{code}')입니다."
            if v["short_name"].upper() == vendor_data.get("short_name", "").strip().upper():
                return False, f"이미 등록된 협력사명/약칭('{vendor_data.get('short_name')}')입니다."

        # 기본값 설정
        now_str = datetime.now().strftime("%Y-%m-%d")
        new_entry = {
            "vendor_code": code,
            "vendor_name": name,
            "short_name": vendor_data.get("short_name", name),
            "country": vendor_data.get("country", "🇰🇷 대한민국"),
            "category": vendor_data.get("category", "가전부품 / 완제품"),
            "supplied_models": vendor_data.get("supplied_models", []),
            "inspection_spec": vendor_data.get("inspection_spec", "ISO 2859-1 Level II"),
            "quality_grade": vendor_data.get("quality_grade", "A"),
            "status": vendor_data.get("status", "정상 가동"),
            "contact_person": vendor_data.get("contact_person", "-"),
            "contact_email": vendor_data.get("contact_email", "-"),
            "contact_phone": vendor_data.get("contact_phone", "-"),
            "registered_date": now_str,
            "last_inspection_date": "-",
            "total_inspections": 0,
            "pass_count": 0,
            "ncr_count": 0,
            "notes": vendor_data.get("notes", "")
        }

        vendors.append(new_entry)
        if self.save_all(vendors):
            return True, f"협력사 '{name}' ({code}) 등록이 완료되었습니다."
        return False, "저장 중 오류가 발생했습니다."

    def update_vendor(self, vendor_code: str, update_fields: Dict[str, Any]) -> tuple[bool, str]:
        """기존 협력업체 정보 수정"""
        vendors = self.load_all()
        found = False
        for i, v in enumerate(vendors):
            if v["vendor_code"] == vendor_code:
                vendors[i].update(update_fields)
                found = True
                break
        
        if not found:
            return False, "해당 업체를 찾을 수 없습니다."

        if self.save_all(vendors):
            return True, f"협력사({vendor_code}) 정보가 업데이트되었습니다."
        return False, "업데이트 저장 중 오류가 발생했습니다."

    def delete_vendor(self, vendor_code: str) -> tuple[bool, str]:
        """협력업체 삭제"""
        vendors = self.load_all()
        orig_len = len(vendors)
        vendors = [v for v in vendors if v["vendor_code"] != vendor_code]
        
        if len(vendors) == orig_len:
            return False, "삭제할 업체를 찾을 수 없습니다."

        if self.save_all(vendors):
            return True, f"협력사({vendor_code})가 삭제되었습니다."
        return False, "삭제 저장 중 오류가 발생했습니다."

    def record_inspection_result(self, vendor_keyword: str, is_pass: bool):
        """성적서 검사 결과(합격/불합격)를 해당 협력업체 이력에 자동 반영"""
        vendor = self.get_vendor(vendor_keyword)
        if not vendor:
            return
        
        vendors = self.load_all()
        for v in vendors:
            if v["vendor_code"] == vendor["vendor_code"]:
                v["total_inspections"] = v.get("total_inspections", 0) + 1
                if is_pass:
                    v["pass_count"] = v.get("pass_count", 0) + 1
                else:
                    v["ncr_count"] = v.get("ncr_count", 0) + 1
                v["last_inspection_date"] = datetime.now().strftime("%Y-%m-%d")
                
                # 합격률 80% 미만 시 경고/중점 관리 자동 전환
                total = v["total_inspections"]
                if total >= 3:
                    pass_rate = (v["pass_count"] / total) * 100
                    if pass_rate < 80 and v["status"] == "정상 가동":
                        v["status"] = "중점 관리"
                        v["quality_grade"] = "C"
                break
        self.save_all(vendors)
