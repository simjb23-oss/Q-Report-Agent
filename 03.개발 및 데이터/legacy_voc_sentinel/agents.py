import re
import json
import pandas as pd
import numpy as np
from typing import Dict, List, Any

class MultilingualClassifierAgent:
    """Agent 1: 다국어 정밀 정제 및 엔지니어링 온톨로지 매핑 Agent"""
    
    ONTOLOGY = {
        "Nozzle Lock Ring": {
            "keywords": ["lock ring", "schließring", "khớp nối", "락링", "coupling", "nozzle joint", "vòi xịt"],
            "defect_types": ["defect_leakage", "defect_crack"]
        },
        "Nozzle O-ring": {
            "keywords": ["o-ring", "dichtungsring", "오링", "패킹", "rubber seal", "밀폐"],
            "defect_types": ["defect_leakage"]
        },
        "Motor Housing": {
            "keywords": ["motor", "burning", "hot", "heiß", "nóng", "mótơ", "모터", "과열", "연기", "smell", "odor"],
            "defect_types": ["defect_overheat"]
        },
        "Battery Latch": {
            "keywords": ["battery", "latch", "pin", "lỏng lẻo", "배터리", "유격", "체결", "loose", "disconnection"],
            "defect_types": ["defect_tolerance"]
        }
    }

    NOISE_KEYWORDS = [
        "box", "shipping", "courier", "delivery", "karton", "versand", "giao hàng", "택배", "배송",
        "wrist", "heavy", "color", "returning", "schwer", "farbe", "환불", "무겁", "색상"
    ]

    POSITIVE_KEYWORDS = [
        "amazing", "solid", "gutes", "trâu", "rất êm", "만족", "최고", "smooth", "recommend"
    ]

    def process_review(self, text: str, rating: int) -> Dict[str, Any]:
        text_lower = text.lower()

        # 1. 긍정 리뷰 체크
        if rating >= 4:
            return {
                "category": "normal_positive",
                "is_defect": False,
                "target_part": "None",
                "severity": 0,
                "reasoning": "별점 4점 이상 및 정상 만족 후기"
            }

        # 2. 노이즈 체크 (배송/변심)
        for kw in self.NOISE_KEYWORDS:
            if kw in text_lower:
                return {
                    "category": "noise_logistics_or_preference",
                    "is_defect": False,
                    "target_part": "None",
                    "severity": 0,
                    "reasoning": f"비결함 노이즈 키워드 감지: '{kw}'"
                }

        # 3. 하드웨어 결함 키워드 온톨로지 매핑
        for part, meta in self.ONTOLOGY.items():
            for kw in meta["keywords"]:
                if kw in text_lower:
                    defect_type = meta["defect_types"][0]
                    if "crack" in text_lower or "nứt" in text_lower or "크랙" in text_lower:
                        defect_type = "defect_crack"
                    return {
                        "category": defect_type,
                        "is_defect": True,
                        "target_part": part,
                        "severity": 3 if rating == 1 else 2,
                        "reasoning": f"[{part}] 결함 키워드 '{kw}' 검출 ➔ {defect_type} 분류"
                    }

        # 4. 기타 불량
        return {
            "category": "defect_general",
            "is_defect": True,
            "target_part": "General",
            "severity": 1,
            "reasoning": "기타 잠재적 품질 클레임"
        }


class EarlyAnomalyDetectorAgent:
    """Agent 2: 품질 골든타임 조기 경보 및 이상치(Anomaly) 분석 Agent"""
    
    def analyze_anomalies(self, df: pd.DataFrame) -> Dict[str, Any]:
        defect_df = df[df['is_defect'] == True]
        total_reviews = len(df)
        total_defects = len(defect_df)
        
        part_counts = defect_df['target_part'].value_counts()
        if len(part_counts) == 0:
            return {"status": "NORMAL", "risk_score": 10, "top_defect_part": None}

        top_part = part_counts.index[0]
        top_part_count = int(part_counts.iloc[0])
        top_part_ratio = (top_part_count / total_defects) * 100 if total_defects > 0 else 0
        
        # 이상치 스파이크 지수 (Z-score 시뮬레이션: 통상 비율 10% 기준)
        expected_ratio = 10.0
        z_score = round((top_part_ratio - expected_ratio) / 8.5, 2)
        risk_score = min(99, int(z_score * 20 + 20))
        
        is_critical = z_score >= 2.5 or top_part_ratio >= 35.0

        return {
            "status": "CRITICAL" if is_critical else "WARNING",
            "z_score": z_score,
            "risk_score": risk_score,
            "total_defects": total_defects,
            "defect_ratio": round((total_defects / total_reviews) * 100, 1),
            "top_part": top_part,
            "top_part_count": top_part_count,
            "top_part_ratio": round(top_part_ratio, 1),
            "estimated_loss_krw": "2억 4,000만 원 (출시 3주차 기준 추정치)",
            "action_required": "R&D 설계변경권고서(ECO) 긴급 발행 필요"
        }


class EngineeringAdvisorAgent:
    """Agent 3: FMEA 원인 추론 및 설계 변경 권고서(ECO) 자동 발행 Agent"""
    
    ENGINEERING_KNOWLEDGE_BASE = {
        "Nozzle Lock Ring": {
            "mechanism": "고압 분사 시 발생하는 반복 맥동 수압(Water Hammer) 및 진동 피로 파괴",
            "root_cause_material": "현재 ABS 사출 소재의 인장 강도 부족 및 저온 취성으로 인한 미세 헤어라인 크랙",
            "root_cause_tolerance": "체결부 락링 멈춤턱 공차 누적(±0.08mm)으로 인한 고압 체결력 이탈",
            "action_material": "고강도 유리섬유 강화 폴리아미드(PA66-GF30) 또는 황동(Brass) 인서트 사출로 변경",
            "action_tolerance": "O-링 안착 홈(Groove) 가공 공차를 ±0.05mm ➔ ±0.02mm로 정밀화",
            "action_qa": "공장 출하 전 에어 리크(Air Leak) 전수 검사 압력 기준 10 bar ➔ 13 bar(1.3배) 상향 테스트"
        },
        "Motor Housing": {
            "mechanism": "모터 고속 회전 시 방열 불량에 따른 열변형 및 벤트홀 체적 부족",
            "root_cause_material": "하우징 내열 플라스틱(PP-GF)의 열변형온도(HDT) 기준 미달",
            "root_cause_tolerance": "모터 고정 브래킷 압입 유격 과다로 인한 진동 유발",
            "action_material": "난연 내열 강화 PBT 소재로 변경",
            "action_tolerance": "냉각 공기 흡배기 벤트홀 단면적 25% 확장 설계 변경",
            "action_qa": "연속 구동 신뢰성 시험 기준 30분 ➔ 120분으로 강화"
        },
        "Battery Latch": {
            "mechanism": "작업 진동에 의한 래치 후크 이탈 및 접점 단속 현상",
            "root_cause_material": "래치 스프링 탄성 계수 저하",
            "root_cause_tolerance": "배터리 레일 슬라이드 공차 유격(0.5mm 초과)",
            "action_material": "SUS304 고탄성 스프링 및 POM 소재 래치 적용",
            "action_tolerance": "슬라이드 결합부 공차를 0.15mm 이내로 가이드 리브(Rib) 추가",
            "action_qa": "진동 낙하 복합 시험(MIL-STD-810G) 전수 통과 확인"
        }
    }

    def generate_eco_report(self, product_name: str, anomaly_data: Dict[str, Any], sample_reviews: List[Dict[str, str]]) -> str:
        part = anomaly_data.get("top_part", "Nozzle Lock Ring")
        kb = self.ENGINEERING_KNOWLEDGE_BASE.get(part, self.ENGINEERING_KNOWLEDGE_BASE["Nozzle Lock Ring"])
        
        reviews_snippet = "\n".join([f"- **[{r['country']}/{r['channel']}]** ⭐{r['rating']}: *\"{r['text']}\"*" for r in sample_reviews[:3]])

        report = f"""# 📋 [긴급] 설계 변경 권고서 (Engineering Change Order: ECO 초안)

* **문서 식별 번호:** ECO-{pd.Timestamp.now().strftime('%Y%m%d')}-VOC-{part.replace(' ', '')[:4].upper()}
* **발행 주체:** VOC-Sentinel R&D Advisor Agent (AI 자율 발행)
* **발행 일자:** {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}
* **대상 모델:** {product_name}
* **긴급도:** 🚨 **{anomaly_data.get('status', 'CRITICAL')} (품질 골든타임 경보)**
* **수신 부서:** 기구설계팀, 재료연구팀, 품질보증(QA)팀, 생산기술팀

---

### 1. 필드 불량 현상 및 데이터 증빙 (Field Evidence)
* **집중 결함 부품:** **{part}**
* **결함 점유율:** 전체 결함 VOC 중 **{anomaly_data.get('top_part_ratio', 42.0)}%** 집중 매핑 (총 {anomaly_data.get('top_part_count', 11)}건 감지)
* **이상치 지수 (Z-Score):** **+{anomaly_data.get('z_score', 3.42)}** (위험 수준 관리한계선 초과)
* **대표 해외 고객 클레임 원문:**
{reviews_snippet}

---

### 2. 엔지니어링 메커니즘 원인 추론 (Root Cause Analysis - FMEA)
* **고장 메커니즘:** {kb['mechanism']}
* **[소재 관점 원인]:** {kb['root_cause_material']}
* **[기구 공차 관점 원인]:** {kb['root_cause_tolerance']}

---

### 3. R&D 설계 및 제조 공정 시정조치 권고안 (Engineering Action Plan)
1. **[기구 도면 수정 (Mechanical Design)]**
   * {kb['action_tolerance']}
2. **[소재 변경 권고 (Material Specification)]**
   * {kb['action_material']}
3. **[품질 공정 검사 기준 강화 (Quality Assurance)]**
   * {kb['action_qa']}

---

### 4. 경제적 기대 효과 및 리스크 차단 효과
* **예상 손실 방지:** {anomaly_data.get('estimated_loss_krw', '약 2억 4천만 원')} 규모의 아마존 대량 반품 및 리콜 선제 차단
* **품질 골든타임 단축:** 통상 3~6개월 소요되는 사후 대응을 **출시 2~3주 이내 설계 피드백(Closed-loop) 완료**
"""
        return report
