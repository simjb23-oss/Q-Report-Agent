# -*- coding: utf-8 -*-
"""
COA-Guard AI Agent (Check-Mate QA Inspector)
글로벌 OEM·ODM 완제품 출하검사 성적서 자동 판정 & 품질 감사 Agent
경남 AI·SW 경진대회 출품작 | 팀명: 칼퇴보증
"""

import os
import sys
import glob
import time
import json
import base64
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from PIL import Image

# 모듈 경로 추가
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, '..', '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.parsers.report_parser import InspectionReportParser
from src.core.evaluator import ToleranceEvaluator
from src.core.ncr_generator import NCRGenerator
from src.core.vendor_manager import VendorManager
from src.core.qc_master_db import QC_MASTER_SPECS

# 앱 아이콘 로드
APP_ICON_PATH = os.path.join(PROJECT_ROOT, "app_icon.ico")
app_icon_img = Image.open(APP_ICON_PATH) if os.path.exists(APP_ICON_PATH) else None

APP_PNG_PATH = os.path.join(PROJECT_ROOT, "app_icon.png")
app_icon_b64 = ""
if os.path.exists(APP_PNG_PATH):
    with open(APP_PNG_PATH, "rb") as f:
        app_icon_b64 = f"data:image/png;base64,{base64.b64encode(f.read()).decode('utf-8')}"
elif os.path.exists(APP_ICON_PATH):
    with open(APP_ICON_PATH, "rb") as f:
        app_icon_b64 = f"data:image/x-icon;base64,{base64.b64encode(f.read()).decode('utf-8')}"

# 페이지 설정
st.set_page_config(
    page_title="칼퇴보증 : 성적서 분석 에이전트",
    page_icon=app_icon_img,
    layout="wide",
    initial_sidebar_state="expanded"
)

# 세션 상태 초기화
if "analysis_done" not in st.session_state:
    st.session_state.analysis_done = False
if "parsed_data" not in st.session_state:
    st.session_state.parsed_data = None
if "eval_result" not in st.session_state:
    st.session_state.eval_result = None
if "active_file_path" not in st.session_state:
    st.session_state.active_file_path = None
if "approval_status" not in st.session_state:
    st.session_state.approval_status = "결재 대기"
if "mail_sent" not in st.session_state:
    st.session_state.mail_sent = False


# -------------------------------------------------------------
# 성적서 파일 자동 탐색 헬퍼 (41건 업체데이터 + 8건 샘플)
# -------------------------------------------------------------
@st.cache_data(show_spinner=False)
def load_available_reports():
    reports = []
    # 1. 대표 샘플 성적서 (sample_coas)
    sample_dir = os.path.join(PROJECT_ROOT, "data", "sample_coas")
    if not os.path.exists(sample_dir):
        sample_dir = os.path.join(PROJECT_ROOT, "03.개발 및 데이터", "data", "sample_coas")
    if os.path.exists(sample_dir):
        for f in sorted(os.listdir(sample_dir)):
            if f.lower().endswith((".pdf", ".xlsx")):
                reports.append({
                    "category": "🌟 대표 검증 샘플 (PASS / NG / Critical)",
                    "filename": f,
                    "filepath": os.path.join(sample_dir, f),
                    "label": f"[대표 샘플] {f}"
                })

    # 2. 실제 협력사 완제품 출하 성적서 (업체별데이터)
    vendor_dir = os.path.join(PROJECT_ROOT, "업체별데이터")
    if not os.path.exists(vendor_dir):
        vendor_dir = os.path.join(PROJECT_ROOT, "03.개발 및 데이터", "업체별데이터")
    if os.path.exists(vendor_dir):
        for model_folder in sorted(os.listdir(vendor_dir)):
            sub_dir = os.path.join(vendor_dir, model_folder)
            if os.path.isdir(sub_dir):
                for f in sorted(os.listdir(sub_dir)):
                    if f.lower().endswith(".pdf"):
                        cat_label = {
                            "블렌더_BL-E01": "🥣 초고속 블렌더 BL-E01 (HOTOEM)",
                            "블렌더_BL-D01": "🌪️ 진공 블렌더 BL-D01 (MYLUX)",
                            "블렌더_BL-C01": "🥤 콤팩트 블렌더 BL-C01 (MYLUX)",
                          