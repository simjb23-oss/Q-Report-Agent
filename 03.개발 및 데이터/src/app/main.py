# -*- coding: utf-8 -*-
"""
COA-Guard AI Agent (Check-Mate QA Inspector)
출하검사 성적서 자동 판정 & 품질 감사 Agent
순정 Streamlit 1.30+ 네이티브 컨테이너 & 다크 테마 최적화 버전
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
from PIL import Image

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

# 앱 아이콘 로드
APP_ICON_PATH = os.path.join(PROJECT_ROOT, "app_icon.ico")
APP_PNG_PATH = os.path.join(PROJECT_ROOT, "app_icon.png")

# 페이지 설정
st.set_page_config(
    page_title="칼퇴보증 : 성적서 분석 에이전트",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

# [사용자 지정 고대비 다크 테마 CSS]
st.markdown("""
<style>
/* Streamlit 최상위 CSS 변수 강제 통일 */
:root {
    --text-color: #F8FAFC !important;
    --background-color: #0E1117 !important;
    --secondary-background-color: #1E293B !important;
}

/* 1. 메인 화면 전체 배경 & 글자 */
.stApp, [data-testid="stAppViewContainer"] {
    background-color: #0E1117 !important;
    color: #F8FAFC !important;
}

/* 2. 모든 텍스트 요소를 흰색으로 강제 */
.stApp p, .stApp span, .stApp div, .stApp label, .stApp h1, .stApp h2, .stApp h3, .stApp h4 {
    color: #F8FAFC !important;
}

/* 3. 사이드바 배경 및 일반 글자 */
[data-testid="stSidebar"] {
    background-color: #1E293B !important;
}
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] h4,
[data-testid="stSidebar"] div:not([data-baseweb="select"]):not([data-baseweb="select"] *) {
    color: #F8FAFC !important;
}

/* 4. 입력창 & 셀렉트박스 (사이드바/메인 공통): 흰 배경 + 칠흑 블랙 글씨 강제 */
input, textarea, select, [data-baseweb="select"],
[data-testid="stSidebar"] input,
[data-testid="stSidebar"] textarea,
[data-testid="stSidebar"] select,
[data-testid="stSidebar"] [data-baseweb="select"] {
    background-color: #FFFFFF !important;
    color: #000000 !important;
}

/* 셀렉트박스 및 인풋 내부의 모든 텍스트/스팬/태그에 완전한 검은색 강제 */
input *, textarea *, select *, [data-baseweb="select"] *,
[data-testid="stSidebar"] input *,
[data-testid="stSidebar"] textarea *,
[data-testid="stSidebar"] select *,
[data-testid="stSidebar"] [data-baseweb="select"] *,
[data-testid="stSidebar"] [data-baseweb="select"] span,
[data-testid="stSidebar"] [data-baseweb="select"] div {
    color: #000000 !important;
    -webkit-text-fill-color: #000000 !important;
    font-weight: 600 !important;
}

/* 드롭다운 옵션 메뉴 팝오버 */
[data-baseweb="popover"], [data-baseweb="popover"] *,
[data-baseweb="menu"], [data-baseweb="menu"] *,
li[role="option"], li[role="option"] * {
    background-color: #FFFFFF !important;
    color: #000000 !important;
    -webkit-text-fill-color: #000000 !important;
}
</style>
""", unsafe_allow_html=True)

# 세션 상태 초기화
if "analysis_done"not in st.session_state:
    st.session_state.analysis_done = False
if "parsed_data"not in st.session_state:
    st.session_state.parsed_data = None
if "eval_result"not in st.session_state:
    st.session_state.eval_result = None
if "active_file_path"not in st.session_state:
    st.session_state.active_file_path = None
if "appr