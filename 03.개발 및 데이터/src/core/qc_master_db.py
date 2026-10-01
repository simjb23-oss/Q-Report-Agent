# -*- coding: utf-8 -*-
"""
QC Master Specifications Database
사내 품질 기준 및 공차 마스터 DB
"""

QC_MASTER_SPECS = {
    "BL-E01": {
        "product_name": "초고속 블렌더 BL-E01",
        "category": "블렌더",
        "supplier": "HOTOEM",
        "inspection_spec_no": "QA-25-109-01",
        "aql": {
            "critical": 0,
            "major": 1.0,
            "minor": 4.0
        },
        "electrical": {
            "voltage": "220-240V",
            "frequency": "50-60Hz",
            "power_w": {"nominal": 1200, "min": 1080, "max": 1260, "unit": "W"},  # -10%, +5%
            "hi_pot": {"test_voltage": 1500, "leakage_current_max": 5.0, "unit": "mA"},
            "insulation_res": {"min": 10.0, "unit": "MΩ"},
            "ground_res": {"max": 0.1, "unit": "Ω"}
        },
        "dimensions": {
            "cord_length": {"nominal": 1000, "min": 950, "max": 1050, "unit": "mm", "desc": "전원코드 길이"},
            "cup_outer_diameter": {"nominal": 142.0, "min": 141.2, "max": 142.8, "unit": "mm", "desc": "용기 상단 외경"},
            "cup_height": {"nominal": 255.0, "min": 253.5, "max": 256.5, "unit": "mm", "desc": "용기 총 높이"},
            "blade_clearance": {"nominal": 3.0, "min": 2.2, "max": 3.8, "unit": "mm", "desc": "칼날-바닥 간극"}
        }
    },
    "BL-D01": {
        "product_name": "진공 블렌더 BL-D01",
        "category": "블렌더",
        "supplier": "MYLUX",
        "inspection_spec_no": "QA-23-109-012",
        "aql": {
            "critical": 0,
            "major": 1.0,
            "minor": 2.5
        },
        "electrical": {
            "voltage": "220-230V",
            "frequency": "50-60Hz",
            "power_w": {"nominal": 900, "min": 810, "max": 945, "unit": "W"},
            "hi_pot": {"test_voltage": 1500, "leakage_current_max": 5.0, "unit": "mA"},
            "insulation_res": {"min": 10.0, "unit": "MΩ"},
            "ground_res": {"max": 0.1, "unit": "Ω"}
        },
        "dimensions": {
            "cord_length": {"nominal": 1000, "min": 950, "max": 1050, "unit": "mm", "desc": "전원선 길이"},
            "body_outer_diameter": {"nominal": 185.0, "min": 184.2, "max": 185.8, "unit": "mm", "desc": "본체 베이스 외경"},
            "cup_capacity": {"nominal": 1500, "min": 1480, "max": 1550, "unit": "mL", "desc": "용기 정격 용량"}
        }
    },
    "BL-C01": {
        "product_name": "콤팩트 블렌더 BL-C01",
        "category": "블렌더",
        "supplier": "MYLUX",
        "inspection_spec_no": "QA-20-109-006",
        "aql": {
            "critical": 0,
            "major": 1.0,
            "minor": 2.5
        },
        "electrical": {
            "voltage": "220V",
            "frequency": "50-60Hz",
            "power_w": {"nominal": 500, "min": 450, "max": 525, "unit": "W"},
            "hi_pot": {"test_voltage": 1500, "leakage_current_max": 5.0, "unit": "mA"},
            "insulation_res": {"min": 10.0, "unit": "MΩ"},
            "ground_res": {"max": 0.1, "unit": "Ω"}
        },
        "dimensions": {
            "upper_cover_size": {"nominal": 9.92, "min": 9.80, "max": 10.05, "unit": "mm", "desc": "상부 커버 체결 치수"}
        }
    },
    "TM-HB1": {
        "product_name": "스마트 티마스터 TM-HB1",
        "category": "전기주전자",
        "supplier": "CRASTAL",
        "inspection_spec_no": "QA-19-TM-003",
        "aql": {
            "critical": 0,
            "major": 1.0,
            "minor": 2.5
        },
        "electrical": {
            "voltage": "220V",
            "frequency": "60Hz",
            "power_w": {"nominal": 1200, "min": 1080, "max": 1260, "unit": "W"}, # -10%, +5%
            "hi_pot": {"test_voltage": 1500, "leakage_current_max": 0.5, "unit": "mA", "duration_sec": 2},
            "insulation_res": {"min": 10.0, "unit": "MΩ"},
            "ground_res": {"max": 0.1, "unit": "Ω"},
            "leakage_current": {"max": 0.75, "unit": "mA"}
        },
        "dimensions": {
            "temperature_85c": {"nominal": 85.0, "min": 80.75, "max": 89.25, "unit": "°C", "desc": "85℃ 유지 온도(±5%)"},
            "temperature_95c": {"nominal": 95.0, "min": 90.25, "max": 99.75, "unit": "°C", "desc": "95℃ 유지 온도(±5%)"},
            "gap_clearance": {"nominal": 0.5, "min": 0.0, "max": 0.5, "unit": "mm", "desc": "간극 허용공차(0.5mm 이하)"},
            "power_cord_pull": {"nominal": 60.0, "min": 60.0, "max": 200.0, "unit": "N", "desc": "전원코드 인장강도 (60N/6.1kgf)"}
        }
    },
    "CJ-B03": {
        "product_name": "전자동 전동스퀴저 CJ-B03",
        "category": "전동스퀴저",
        "supplier": "필립전기 (PHILP / 余姚市菲尔浦电器)",
        "inspection_spec_no": "MIL-STD-105E II",
        "aql": {
            "critical": 0,
            "major": 0.65,
            "minor": 2.5
        },
        "electrical": {
            "voltage": "220V",
            "frequency": "60Hz",
            "power_w": {"nominal": 100, "min": 80, "max": 120, "unit": "W"},
            "hi_pot": {"test_voltage": 1500, "leakage_current_max": 5.0, "unit": "mA"},
            "insulation_res": {"min": 10.0, "unit": "MΩ"}
        },
        "dimensions": {
            "rotation_rpm": {"nominal": 55, "min": 45, "max": 65, "unit": "RPM", "desc": "착즙 콘 회전속도"},
            "noise_level": {"nominal": 65, "min": 0, "max": 72, "unit": "dB", "desc": "작동 소음"}
        }
    }
}
