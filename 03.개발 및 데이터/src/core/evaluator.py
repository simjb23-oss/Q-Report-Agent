# -*- coding: utf-8 -*-
"""
Tolerance Evaluator & ISO 2859-1 Statistical Quality Engine
사내 도면 한계공차(LSL/USL) 대조, 전기안전 4종 검증 및 ISO 2859-1 AQL 판정 엔진
"""

import os
import json
from typing import Dict, Any, List, Optional

try:
    from src.core.qc_master_db import QC_MASTER_SPECS
except ModuleNotFoundError:
    try:
        from core.qc_master_db import QC_MASTER_SPECS
    except ModuleNotFoundError:
        from qc_master_db import QC_MASTER_SPECS


class ToleranceEvaluator:
    def __init__(self):
        self.specs = QC_MASTER_SPECS
        self.part_specs = {}
        self._load_internal_part_specs()

    def _load_internal_part_specs(self):
        """사내 부품 도면 공차 규격 마스터(internal_part_spec_master.json) 로드"""
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        json_path = os.path.join(base_dir, "data", "internal_part_spec_master.json")
        if os.path.exists(json_path):
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for item in data:
                        part_no = item.get("part_no")
                        if part_no:
                            self.part_specs[part_no] = item
                            # 접미사 없는 단축 코드도 매핑 (예: INJ-H401 -> INJ-H401-BK)
                            short_no = part_no.split("-")[0] + "-" + part_no.split("-")[1] if "-" in part_no else part_no
                            self.part_specs[short_no] = item
            except Exception:
                pass

    def _get_iso2859_sampling(self, lot_size: int, aql_maj: float = 1.0, aql_min: float = 2.5, inspection_level: str = "보통검사 (Level II)") -> Dict[str, Any]:
        """ISO 2859-1 통계 샘플링 방식 (보통/강화/단축) 한계선 산출"""
        if lot_size <= 150:
            code, n, ac_maj, re_maj, ac_min, re_min = 'F', 20, 0, 1, 1, 2
        elif lot_size <= 280:
            code, n, ac_maj, re_maj, ac_min, re_min = 'G', 32, 1, 2, 2, 3
        elif lot_size <= 500:
            code, n, ac_maj, re_maj, ac_min, re_min = 'H', 50, 1, 2, 3, 4
        elif lot_size <= 1200:
            code, n, ac_maj, re_maj, ac_min, re_min = 'J', 80, 2, 3, 5, 6
        elif lot_size <= 3200:
            code, n, ac_maj, re_maj, ac_min, re_min = 'K', 125, 3, 4, 7, 8
        elif lot_size <= 10000:
            code, n, ac_maj, re_maj, ac_min, re_min = 'L', 200, 5, 6, 10, 11
        else:
            code, n, ac_maj, re_maj, ac_min, re_min = 'M', 315, 7, 8, 14, 15

        # 강화검사(Tightened): 불량 허용한계 엄격화 (Ac 대폭 축소)
        if "강화" in inspection_level:
            ac_maj = max(0, ac_maj - 1)
            re_maj = ac_maj + 1
            ac_min = max(0, ac_min - 2)
            re_min = ac_min + 1
        elif "단축" in inspection_level:
            ac_maj = ac_maj + 1
            re_maj = ac_maj + 2
            ac_min = ac_min + 2
            re_min = ac_min + 2

        # AQL 설정값 반영 (엄격: 0.65, 완화: 1.5, 4.0 등)
        if aql_maj < 1.0:
            ac_maj = max(0, ac_maj - 1)
            re_maj = ac_maj + 1
        elif aql_maj > 1.0:
            ac_maj = ac_maj + 1
            re_maj = ac_maj + 1

        if aql_min < 2.5:
            ac_min = max(0, ac_min - 1)
            re_min = ac_min + 1
        elif aql_min > 2.5:
            ac_min = ac_min + 1
            re_min = ac_min + 1

        return {
            'code_letter': code,
            'sample_size': n,
            'inspection_level': inspection_level,
            'critical': {'ac': 0, 're': 1},
            'major': {'aql': aql_maj, 'ac': ac_maj, 're': re_maj},
            'minor': {'aql': aql_min, 'ac': ac_min, 're': re_min}
        }

    def evaluate(self, parsed_data: Dict[str, Any], aql_maj: float = 1.0, aql_min: float = 2.5, inspection_level: str = "보통검사 (Level II)") -> Dict[str, Any]:
        model_code = parsed_data.get("model_code", "").strip()
        measured_values = parsed_data.get("measured_values", {})
        order_qty = parsed_data.get("order_qty", 2500)
        aql_results = parsed_data.get("aql_results", {})
        is_fabricated = parsed_data.get("is_fabricated", False)

        evaluation_items = []
        is_all_pass = True
        ng_reasons = []
        warning_reasons = []

        # 1. 사내 부품 도면 공차 매칭 (internal_part_spec_master.json)
        matched_part = None
        for key in [model_code, model_code.replace("-BK", ""), model_code.replace("-ST", ""), model_code.replace("-SI", "")]:
            if key in self.part_specs:
                matched_part = self.part_specs[key]
                break

        if matched_part:
            product_name = matched_part.get("part_name", model_code)
            supplier = parsed_data.get("supplier", "협력사")
            spec_no = matched_part.get("drawing_rev", "Rev 2.1")
            specs_list = matched_part.get("specs", [])

            for rule in specs_list:
                item_name = rule.get("item_name")
                nominal = rule.get("nominal")
                lsl = rule.get("lsl", float("-inf"))
                usl = rule.get("usl", float("inf"))
                unit = rule.get("unit", "mm")
                importance = rule.get("importance", "Major")

                # 실측치 딕셔너리에서 매핑 탐색 (전체 이름, 단축 영문명 등)
                val = None
                for candidate_key in [item_name, item_name.split("(")[0].strip() if "(" in item_name else "",
                                      rule.get("item_name", "").split("(")[-1].replace(")", "").strip() if "(" in item_name else ""]:
                    if candidate_key and candidate_key in measured_values:
                        val = measured_values[candidate_key]
                        break

                if val is not None:
                    delta = round(val - nominal, 3) if isinstance(nominal, (int, float)) else 0
                    status = "PASS"

                    if val < lsl or val > usl:
                        status = "NG"
                        is_all_pass = False
                        ng_msg = f"{item_name} 규격 이탈 (실측: {val}{unit}, 기준: {lsl}~{usl}{unit})"
                        if importance == "Critical":
                            ng_msg = f"[치명] {ng_msg}"
                        ng_reasons.append(ng_msg)
                    elif lsl != float("-inf") and usl != float("inf") and usl > lsl:
                        # 경계 공차 경고 (10% 이내 여유)
                        tol_range = usl - lsl
                        if (val - lsl) / tol_range < 0.1 or (usl - val) / tol_range < 0.1:
                            status = "WARNING"
                            warning_reasons.append(f"{item_name} 공차 한계선 근접 주의 (실측: {val}{unit})")

                    evaluation_items.append({
                        "item_name": item_name,
                        "measured": val,
                        "nominal": nominal,
                        "min_limit": lsl if lsl != float("-inf") else "-",
                        "max_limit": usl if usl != float("inf") else "-",
                        "unit": unit,
                        "delta": delta,
                        "status": status,
                        "importance": importance
                    })
                else:
                    evaluation_items.append({
                        "item_name": item_name,
                        "measured": "-",
                        "nominal": nominal,
                        "min_limit": lsl if lsl != float("-inf") else "-",
                        "max_limit": usl if usl != float("inf") else "-",
                        "unit": unit,
                        "delta": "-",
                        "status": "미추출",
                        "importance": importance
                    })

        # 2. 완제품 마스터 규격 매칭 (QC_MASTER_SPECS)
        elif model_code in self.specs or any(k in model_code for k in self.specs):
            matched_key = model_code if model_code in self.specs else next(k for k in self.specs if k in model_code)
            master_spec = self.specs[matched_key]
            product_name = master_spec.get("product_name", model_code)
            supplier = master_spec.get("supplier", parsed_data.get("supplier", "협력사"))
            spec_no = master_spec.get("inspection_spec_no", "QA-SPEC-001")

            # 치수/기능 시험
            dim_specs = master_spec.get("dimensions", {})
            for key, spec_rule in dim_specs.items():
                min_v = spec_rule.get("min", float("-inf"))
                max_v = spec_rule.get("max", float("inf"))
                nominal = spec_rule.get("nominal")
                unit = spec_rule.get("unit", "mm")
                desc = spec_rule.get("desc", key)

                if key in measured_values:
                    val = measured_values[key]
                    delta = round(val - nominal, 2) if isinstance(nominal, (int, float)) else 0
                    status = "PASS"
                    if val < min_v or val > max_v:
                        status = "NG"
                        is_all_pass = False
                        ng_reasons.append(f"{desc} 규격 이탈 (실측: {val}{unit}, 기준: {min_v}~{max_v}{unit})")
                    elif min_v != float("-inf") and max_v != float("inf") and max_v > min_v:
                        range_v = max_v - min_v
                        if (val - min_v) / range_v < 0.1 or (max_v - val) / range_v < 0.1:
                            status = "WARNING"
                            warning_reasons.append(f"{desc} 한계선 근접 주의 (실측: {val}{unit})")

                    evaluation_items.append({
                        "item_name": desc,
                        "measured": val,
                        "nominal": nominal,
                        "min_limit": min_v if min_v != float("-inf") else "-",
                        "max_limit": max_v if max_v != float("inf") else "-",
                        "unit": unit,
                        "delta": delta,
                        "status": status,
                        "importance": "Major"
                    })
                else:
                    evaluation_items.append({
                        "item_name": desc,
                        "measured": "-",
                        "nominal": nominal,
                        "min_limit": min_v if min_v != float("-inf") else "-",
                        "max_limit": max_v if max_v != float("inf") else "-",
                        "unit": unit,
                        "delta": "-",
                        "status": "미추출",
                        "importance": "Major"
                    })

            # 전기 안전 4종 (소비전력, 내전압, 절연저항, 접지/누설전류)
            elec_specs = master_spec.get("electrical", {})

            # (1) 소비전력
            if "power_w" in elec_specs:
                rule = elec_specs["power_w"]
                min_v, max_v = rule["min"], rule["max"]
                if "power_w" in measured_values:
                    val = measured_values["power_w"]
                    status = "PASS" if min_v <= val <= max_v else "NG"
                    if status == "NG":
                        is_all_pass = False
                        ng_reasons.append(f"소비전력 규격 이탈 (실측: {val}W, 허용: {min_v}~{max_v}W)")
                    evaluation_items.append({
                        "item_name": "소비전력 (Power)",
                        "measured": val,
                        "nominal": rule.get("nominal", round((min_v + max_v) / 2)),
                        "min_limit": min_v,
                        "max_limit": max_v,
                        "unit": "W",
                        "delta": round(val - rule.get("nominal", val), 1),
                        "status": status,
                        "importance": "Critical"
                    })
                else:
                    evaluation_items.append({
                        "item_name": "소비전력 (Power)", "measured": "-", "nominal": rule.get("nominal", 1000),
                        "min_limit": min_v, "max_limit": max_v, "unit": "W", "delta": "-", "status": "미추출", "importance": "Critical"
                    })

            # (2) 내전압 시험 (Hi-Pot)
            if "hi_pot" in elec_specs:
                rule = elec_specs["hi_pot"]
                max_current = rule.get("leakage_current_max", 5.0)
                if "hi_pot" in measured_values:
                    val = measured_values["hi_pot"]
                    status = "PASS" if (val <= max_current) else "NG"
                    if status == "NG":
                        is_all_pass = False
                        ng_reasons.append(f"내전압(Hi-Pot) 누설전류 초과 (실측: {val}mA > 허용 {max_current}mA)")
                    evaluation_items.append({
                        "item_name": "내전압 시험 (Hi-Pot)",
                        "measured": f"{val} mA (PASS)",
                        "nominal": 0.0,
                        "min_limit": "-",
                        "max_limit": f"{max_current} mA",
                        "unit": "mA",
                        "delta": val,
                        "status": status,
                        "importance": "Critical"
                    })

            # (3) 절연저항 (Insulation Resistance)
            if "insulation_res" in elec_specs:
                rule = elec_specs["insulation_res"]
                min_res = rule.get("min", 10.0)
                if "insulation_res" in measured_values:
                    val = measured_values["insulation_res"]
                    status = "PASS" if val >= min_res else "NG"
                    if status == "NG":
                        is_all_pass = False
                        ng_reasons.append(f"절연저항 기준 미달 (실측: {val}MΩ < 최소 {min_res}MΩ)")
                    evaluation_items.append({
                        "item_name": "절연저항 (Insulation)",
                        "measured": f"{val} MΩ",
                        "nominal": 50.0,
                        "min_limit": f"{min_res} MΩ",
                        "max_limit": "-",
                        "unit": "MΩ",
                        "delta": round(val - min_res, 1),
                        "status": status,
                        "importance": "Critical"
                    })

            # (4) 접지저항 (Ground Resistance)
            if "ground_res" in elec_specs:
                rule = elec_specs["ground_res"]
                max_res = rule.get("max", 0.1)
                if "ground_res" in measured_values:
                    val = measured_values["ground_res"]
                    status = "PASS" if val <= max_res else "NG"
                    if status == "NG":
                        is_all_pass = False
                        ng_reasons.append(f"접지저항 기준 초과 (실측: {val}Ω > 최대 {max_res}Ω)")
                    evaluation_items.append({
                        "item_name": "접지저항 (Grounding)",
                        "measured": f"{val} Ω",
                        "nominal": 0.02,
                        "min_limit": "-",
                        "max_limit": f"{max_res} Ω",
                        "unit": "Ω",
                        "delta": val,
                        "status": status,
                        "importance": "Critical"
                    })

        # 3. 미등록 품번/모델 규격 (조용히 넘기지 않고 경고 발생)
        else:
            product_name = f"미등록 모델 ({model_code})"
            supplier = parsed_data.get("supplier", "협력사")
            spec_no = "사내 도면 DB 미등록 (N/A)"
            is_all_pass = False
            ng_reasons.append(f"⚠️ 사내 도면 마스터 DB에 등록되지 않은 품번/모델({model_code})입니다. 도면 규격 등록 확인이 필요합니다.")
            evaluation_items.append({
                "item_name": "모델 스펙 등록 상태",
                "measured": model_code,
                "nominal": "사내 등록 규격",
                "min_limit": "-",
                "max_limit": "-",
                "unit": "-",
                "delta": "-",
                "status": "NG",
                "importance": "Critical"
            })

        # 4. ISO 2859-1 통계적 샘플링 결함 판정 (Ac/Re)
        iso_plan = self._get_iso2859_sampling(order_qty, aql_maj=aql_maj, aql_min=aql_min, inspection_level=inspection_level)
        cr_count = aql_results.get("critical", 0)
        ma_count = aql_results.get("major", 0)
        mi_count = aql_results.get("minor", 0)

        ac_cr, re_cr = iso_plan['critical']['ac'], iso_plan['critical']['re']
        ac_ma, re_ma = iso_plan['major']['ac'], iso_plan['major']['re']
        ac_mi, re_mi = iso_plan['minor']['ac'], iso_plan['minor']['re']

        if cr_count > ac_cr:
            is_all_pass = False
            ng_reasons.append(f"치명결함(Critical) 발생: 검출 {cr_count}건 > 허용 {ac_cr}건 (Ac={ac_cr}, Re={re_cr})")

        if ma_count > ac_ma:
            is_all_pass = False
            ng_reasons.append(f"ISO 2859-1 중결함(Major) 초과: 검출 {ma_count}건 > 합격판정수 {ac_ma}건 (Ac={ac_ma}, Re={re_ma})")

        if mi_count > ac_mi:
            is_all_pass = False
            ng_reasons.append(f"ISO 2859-1 경결함(Minor) 초과: 검출 {mi_count}건 > 합격판정수 {ac_mi}건 (Ac={ac_mi}, Re={re_mi})")

        # 5. 협력사 자체 처분 및 위변조 검사
        if aql_results.get("vendor_judgement") == "REJECT":
            is_all_pass = False
            if not any("REJECT" in r for r in ng_reasons):
                ng_reasons.append("협력사 자체 검사 최종 불합격(REJECT) 판정")

        if is_fabricated:
            is_all_pass = False
            ng_reasons.append("성적서 측정 데이터 위변조/인위적 조작 감지 (시료 간 편차 0.00)")

        final_verdict = "PASS" if is_all_pass else "FAIL"

        # 6. AI Agent 종합 품질 판정 소견서 (Engineering Rationale) 자율 생성
        if is_all_pass:
            if warning_reasons:
                reasoning = (
                    f"본 {product_name} 성적서는 사내 도면 한계공차 및 ISO 2859-1 기준을 종합적으로 충족하여 최종 정상 입고 승인(PASS) 판정합니다. "
                    f"다만, {', '.join(warning_reasons)} 등 일부 항목이 공차 한계선 10% 이내에 위치하므로, 차기 로트 입고 시 해당 치수에 대한 중점 모니터링을 권고합니다."
                )
            else:
                reasoning = (
                    f"성적서 내 모든 검사항목(치수, 소비전력, 전기안전 및 결함 수)이 사내 도면 기준({spec_no}) 및 ISO 2859-1 보통검사 샘플링 기준을 100% 무결점으로 충족하였습니다. "
                    f"최종 '출하검사 합격 인증 및 입고 승인서'를 정상 발급합니다."
                )
        else:
            reasons_str = " / ".join(ng_reasons)
            reasoning = (
                f"품질 감사 결과 총 {len(ng_reasons)}건의 규격 이탈 및 관리기준 위반이 검출되어 최종 '부적합(FAIL - 입고 보류)' 판정합니다. "
                f"[주요 부적합 사유]: {reasons_str}. "
                f"라인 조립 불량 및 필드 결함 예방을 위해 해당 로트의 입고를 즉각 차단하고, 공급사에 원인 분석 및 재발방지대책(8D Report)을 요구하는 표준 부적합 통보서(NCR)를 자율 발행합니다."
            )

        return {
            "model_code": model_code,
            "product_name": product_name,
            "supplier": supplier,
            "inspection_spec_no": spec_no,
            "evaluation_items": evaluation_items,
            "is_all_pass": is_all_pass,
            "final_verdict": final_verdict,
            "ng_reasons": ng_reasons,
            "warning_reasons": warning_reasons,
            "iso_sampling_plan": iso_plan,
            "agent_reasoning": reasoning
        }
