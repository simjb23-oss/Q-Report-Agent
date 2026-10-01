# -*- coding: utf-8 -*-
from typing import Dict, Any, List
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

    def evaluate(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        model_code = parsed_data.get("model_code", "BL-D01")
        master_spec = self.specs.get(model_code, self.specs["BL-D01"])
        
        measured_values = parsed_data.get("measured_values", {})
        evaluation_items = []
        is_all_pass = True
        ng_reasons = []

        dim_specs = master_spec.get("dimensions", {})
        for key, spec_rule in dim_specs.items():
            if key in measured_values:
                val = measured_values[key]
                min_v = spec_rule.get("min", float("-inf"))
                max_v = spec_rule.get("max", float("inf"))
                nominal = spec_rule.get("nominal")
                if nominal is None:
                    if min_v != float("-inf") and max_v != float("inf"):
                        nominal = round((min_v + max_v) / 2, 3)
                    elif min_v != float("-inf"):
                        nominal = min_v
                    elif max_v != float("inf"):
                        nominal = max_v
                    else:
                        nominal = val
                unit = spec_rule.get("unit", "mm")
                desc = spec_rule.get("desc", key)

                status = "PASS"
                if val < min_v or val > max_v:
                    status = "NG"
                    is_all_pass = False
                    ng_reasons.append(f"{desc} 규격 이탈 (실측: {val}{unit}, 기준: {min_v}~{max_v}{unit})")
                elif min_v != float("-inf") and max_v != float("inf") and max_v > min_v:
                    range_v = max_v - min_v
                    if (val - min_v) / range_v < 0.1 or (max_v - val) / range_v < 0.1:
                        status = "WARNING"
                elif min_v != float("-inf") and val < min_v * 1.05:
                    status = "WARNING"

                evaluation_items.append({
                    "item_name": desc,
                    "measured": val,
                    "nominal": nominal,
                    "min_limit": min_v if min_v != float("-inf") else "-",
                    "max_limit": max_v if max_v != float("inf") else "-",
                    "unit": unit,
                    "delta": round(val - nominal, 3) if isinstance(nominal, (int, float)) else 0,
                    "status": status
                })

        elec_specs = master_spec.get("electrical", {})
        if "power_w" in elec_specs and "power_w" in measured_values:
            rule = elec_specs["power_w"]
            val = measured_values["power_w"]
            min_v = rule["min"]
            max_v = rule["max"]
            status = "PASS" if min_v <= val <= max_v else "NG"
            if status == "NG":
                is_all_pass = False
                ng_reasons.append(f"소비전력 규격 이탈 (실측: {val}W, 허용: {min_v}~{max_v}W)")
            evaluation_items.append({
                "item_name": "소비전력 (Power)",
                "measured": val,
                "nominal": rule["nominal"],
                "min_limit": min_v,
                "max_limit": max_v,
                "unit": rule["unit"],
                "delta": round(val - rule["nominal"], 1),
                "status": status
            })

        aql_results = parsed_data.get("aql_results", {})
        crit_val = aql_results.get("critical", 0)
        crit_limit = master_spec["aql"]["critical"]
        if crit_val > crit_limit:
            is_all_pass = False
            ng_reasons.append(f"치명결함(Critical) 검출 ({crit_val}건 > 허용 {crit_limit}건)")

        if aql_results.get("vendor_judgement") == "REJECT":
            is_all_pass = False
            if not ng_reasons:
                ng_reasons.append("협력사 자체 검사 최종 불합격(REJECT) 판정")

        final_verdict = "PASS" if is_all_pass else "FAIL"

        return {
            "model_code": model_code,
            "product_name": master_spec.get("product_name", model_code),
            "supplier": master_spec.get("supplier", "협력사"),
            "inspection_spec_no": master_spec.get("inspection_spec_no", "QA-SPEC-001"),
            "evaluation_items": evaluation_items,
            "is_all_pass": is_all_pass,
            "final_verdict": final_verdict,
            "ng_reasons": ng_reasons
        }