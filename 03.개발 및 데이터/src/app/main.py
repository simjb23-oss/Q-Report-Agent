# -*- coding: utf-8 -*-
"""
COA-Guard AI Agent (Check-Mate QA Inspector)
출하검사 성적서 자동 판정 & 품질 감사 Agent
"""

import os
import sys
import glob
import time
import base64
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

# 모듈 경로 추가
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, '..', '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.parsers.report_parser import InspectionReportParser
from src.core.evaluator import ToleranceEvaluator
from src.core.ncr_generator import NCRGenerator
from src.core.audit_manager import AuditManager, get_sheet_config, save_sheet_config
from src.core.email_drafter import EmailDrafter

from PIL import Image

# 앱 아이콘 로드 (app_icon.ico 및 Base64 인라인)
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
    page_icon=None,
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

# 사이드바 설정
with st.sidebar:
    # -------------------------------------------------------------
    # [블록 1] 브랜드 및 상태 인디케이터
    # -------------------------------------------------------------
    status_label = "AUDIT_COMPLETE (System Ready)" if st.session_state.get("analysis_done") else "IDLE (System Ready)"
    status_color = "#16a34a"
    
    st.markdown(f"""
    <div class="sb-brand-card">
        <div style="font-size:16px; font-weight:800; color:#ffffff !important; margin:0 0 6px 0; display:flex; align-items:center; gap:6px;">
            <span style="color:#ffffff !important;">Q-Report Agent</span>
            <span style="font-size:12px; color:#38bdf8 !important; font-weight:700;">| 칼퇴보증 팀</span>
        </div>
        <div style="font-size:12px; font-weight:700; color:#ffffff !important; display:flex; align-items:center; gap:6px; background-color:#1e293b; padding:6px 10px; border-radius:6px; border:1px solid #334155;">
            <span style="display:inline-block; width:8px; height:8px; border-radius:50%; background-color:{status_color};"></span>
            <span style="color:#ffffff !important;">Status: <b style="color:#ffffff !important;">{status_label}</b></span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # -------------------------------------------------------------
    # [블록 2] 메뉴 네비게이션
    # -------------------------------------------------------------
    st.markdown("""
    <div class="sb-title-label" style="font-size:13px; font-weight:800; margin-bottom:6px;">
        [메뉴 네비게이션]
    </div>
    """, unsafe_allow_html=True)
    nav_menu = st.radio(
        "화면 바로가기",
        [
            "1. 성적서 자율 판독",
            "2. 협력사 품질 분석"