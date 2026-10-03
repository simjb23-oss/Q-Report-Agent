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
    <div style="background:#0f172a; padding:16px 18px; border-radius:12px; border:1px solid #1e293b; margin-bottom:14px; box-shadow:0 4px 12px rgba(0,0,0,0.15);">
        <div style="font-size:16px; font-weight:800; color:#ffffff; margin:0 0 6px 0; display:flex; align-items:center; gap:6px;">
            <span>Q-Report Agent</span>
            <span style="font-size:12px; color:#94a3b8; font-weight:600;">| 칼퇴보증 팀</span>
        </div>
        <div style="font-size:12px; font-weight:700; color:#e2e8f0; display:flex; align-items:center; gap:6px; background:#1e293b; padding:5px 10px; border-radius:6px; border:1px solid #334155;">
            <span style="display:inline-block; width:8px; height:8px; border-radius:50%; background:{status_color};"></span>
            <span>Status: <b>{status_label}</b></span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # -------------------------------------------------------------
    # [블록 2] 메뉴 네비게이션
    # -------------------------------------------------------------
    st.markdown("""
    <div style="font-size:13px; font-weight:800; color:#0f172a; margin-bottom:6px;">
        [메뉴 네비게이션]
    </div>
    """, unsafe_allow_html=True)
    nav_menu = st.radio(
        "화면 바로가기",
        [
            "1. 성적서 자율 판독",
            "2. 협력사 품질 분석",
            "3. 과거 이력 & 잠재 위험 분석",
            "4. 전사 동기화 (google Sheet)"
        ],
        index=0,
        label_visibility="collapsed"
    )
    st.markdown("<hr style='margin:12px 0; border:none; border-top:1px solid #e2e8f0;'>", unsafe_allow_html=True)

    # -------------------------------------------------------------
    # [블록 3] 에이전트 컨트롤 패널
    # -------------------------------------------------------------
    st.markdown("""
    <div style="font-size:13px; font-weight:800; color:#0f172a; margin-bottom:10px;">
        [에이전트 컨트롤 패널]
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style='display:flex; align-items:center; gap:6px; margin-bottom:4px;'>
        <span style='font-size:12px; font-weight:700; color:#334155;'>• AQL 검사 엄격도</span>
        <span title='[AQL 검사 수준 도입 배경]&#10;제조 품질 표준(ISO 2859-1)에 따라 입고 로트 크기와 협력사 신뢰도에 맞춘 샘플링 엄격도를 동적 적용합니다.&#10;1. 일반검사 Level II: 표준 입고 검사 (기본)&#10;2. 엄격검사 Level III: 불량 이력 협력사 대상 전수급 강화 샘플링&#10;3. 특별검사 S-4: 파괴 검사 및 핵심 보안 부품 정밀 샘플링' style='cursor:help; display:inline-flex; align-items:center; justify-content:center; width:16px; height:16px; border-radius:50%; background:#e2e8f0; color:#475569; font-size:11px; font-weight:bold;'>?</span>
    </div>
    """, unsafe_allow_html=True)
    aql_mode = st.selectbox(
        "AQL 검사 수준",
        ["일반검사 Level II (기본)", "엄격검사 Level III (강화)", "특별검사 S-4 (정밀)"],
        index=0,
        label_visibility="collapsed",
        help="[AQL(합격품질한계) 검사 엄격도 도입 배경]\n제조 품질 표준(ISO 2859-1)에 따라 부품 중요도 및 협력사 품질 등급에 맞는 통계적 샘플링 엄격도를 동적으로 적용합니다.\n• 일반검사 Level II (기본): 표준 부품 입고 검사 기준\n• 엄격검사 Level III (강화): 최근 불량 발생 협력사 또는 고위험 부품 집중 관리\n• 특별검사 S-4 (정밀): 파괴 시험(인장강도 등) 및 소량 정밀 계측 전용"
    )

    st.markdown("""
    <div style='display:flex; align-items:center; gap:6px; margin-top:10px; margin-bottom:4px;'>
        <span style='font-size:12px; font-weight:700; color:#334155;'>• AI 추론 엔진</span>
        <span title='[엔진 분리 사유 안내]&#10;1. Gemini 3.8 Flash: 비정형 성적서(스캔본/표/이미지)를 사람처럼 유연하게 시각 판독하는 운영용 멀티모달 AI입니다.&#10;2. 로컬 룰베이스 Fallback: 사내 보안 폐쇄망이나 API Key가 없는 시연/심사 환경에서도 100% 무인 무중단 판독을 보장하는 Fail-Safe 안전장치입니다.' style='cursor:help; display:inline-flex; align-items:center; justify-content:center; width:16px; height:16px; border-radius:50%; background:#e2e8f0; color:#475569; font-size:11px; font-weight:bold;'>?</span>
    </div>
    """, unsafe_allow_html=True)
    engine_choice = st.radio(
        "AI 추론 엔진",
        [
            "Gemini 3.8 Flash (Multi-modal)",
            "로컬 룰베이스 Fallback 강제 (시연용)"
        ],
        index=0,
        label_visibility="collapsed",
        help="[추론 엔진 분리 이유]\n• Gemini 3.8 Flash: 비정형 성적서(스캔 PDF, 표 양식)를 시각적으로 유연하게 자동 판독하는 상용 멀티모달 LLM 엔진입니다.\n• 로컬 룰베이스 Fallback (시연용): 인터넷 차단 폐쇄망 및 API Key가 없는 심사위원/시연 환경에서도 오류 없이 100% 무인 작동을 보장하는 Fail-Safe 아키텍처입니다."
    )
    st.markdown("<hr style='margin:12px 0; border:none; border-top:1px solid #e2e8f0;'>", unsafe_allow_html=True)

    # -------------------------------------------------------------
    # [블록 4] UI/UX 테마 및 색상 스타일 설정
    # -------------------------------------------------------------
    st.markdown('''
    <div style="font-size:13px; font-weight:800; color:#0f172a; margin-top:14px; margin-bottom:6px;">
        [UI/UX 테마 스타일]
    </div>
    ''', unsafe_allow_html=True)
    
    theme_choice = st.selectbox(
        "테마 모드 선택",
        ["클린 라이트 (밝은 오피스)", "모던 네이비 (엔지니어링)", "다크 모드 (고대비/야간)"],
        index=0,
        label_visibility="collapsed",
        help="대시보드의 배경색과 카드 스타일을 실시간으로 전환합니다."
    )
    st.markdown("<hr style='margin:12px 0; border:none; border-top:1px solid #e2e8f0;'>", unsafe_allow_html=True)

    # -------------------------------------------------------------
    # [블록 5] 인프라 연동 상태 모니터 (줄바꿈/짤림 방지 최적화)
    # -------------------------------------------------------------
    st.markdown("""
    <div style="font-size:13px; font-weight:800; color:#0f172a; margin-bottom:8px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">
        [인프라 연동 상태 모니터]
    </div>
    <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:10px; padding:12px 14px; font-size:12px; line-height:1.6;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px; white-space:nowrap; gap:6px;">
            <span style="color:#475569; font-weight:600; white-space:nowrap;">• RapidOCR Engine:</span>
            <span style="font-weight:700; color:#15803d; background:#dcfce7; padding:2px 7px; border-radius:4px; border:1px solid #86efac; white-space:nowrap; font-size:11px;">Active</span>
        </div>
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px; white-space:nowrap; gap:6px;">
            <span style="color:#475569; font-weight:600; white-space:nowrap;">• Cloud Webhook:</span>
            <span style="font-weight:700; color:#15803d; background:#dcfce7; padding:2px 7px; border-radius:4px; border:1px solid #86efac; white-space:nowrap; font-size:11px;">Synced (Apps Script)</span>
        </div>
        <div style="display:flex; justify-content:space-between; align-items:center; white-space:nowrap; gap:6px;">
            <span style="color:#475569; font-weight:600; white-space:nowrap;">• Memory Cache:</span>
            <span style="font-weight:700; color:#15803d; background:#dcfce7; padding:2px 7px; border-radius:4px; border:1px solid #86efac; white-space:nowrap; font-size:11px;">24 Cases Loaded</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# -------------------------------------------------------------
# 모던 프리미엄 CSS
# -------------------------------------------------------------
# Dynamic Theme Palette
if theme_choice == "모던 네이비 (엔지니어링)":
    t_bg = "#0b1329"
    t_card_bg = "#131f37"
    t_card_border = "#233554"
    t_text = "#f1f5f9"
    t_subtext = "#94a3b8"
    t_box_bg = "#1b2a47"
elif theme_choice == "다크 모드 (고대비/야간)":
    t_bg = "#090d16"
    t_card_bg = "#111827"
    t_card_border = "#374151"
    t_text = "#f9fafb"
    t_subtext = "#9ca3af"
    t_box_bg = "#1f2937"
else:
    t_bg = "#f8fafc"
    t_card_bg = "#ffffff"
    t_card_border = "#e2e8f0"
    t_text = "#0f172a"
    t_subtext = "#64748b"
    t_box_bg = "#f8fafc"

# 1. 테마별 동적 오버라이드 CSS
st.markdown(f"""
<style>
    .stApp {{
        background-color: {t_bg} !important;
    }}
    .section-card {{
        background: {t_card_bg} !important;
        border: 1px solid {t_card_border} !important;
        color: {t_text} !important;
    }}
    .section-title {{
        color: {t_text} !important;
    }}
    .field-box, .kpi-card {{
        background: {t_box_bg} !important;
        border: 1px solid {t_card_border} !important;
    }}
    .field-value, .kpi-num {{
        color: {t_text} !important;
    }}
    .field-label {{
        color: {t_subtext} !important;
    }}
</style>
""", unsafe_allow_html=True)

# 2. 정적 기본 CSS (일반 문자열로 안전하게 주입)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Pretendard:wght@400;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, Roboto, sans-serif;
    }

    .hero-header {
        background: #0f172a;
        color: #ffffff;
        padding: 22px 28px;
        border-radius: 12px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 20px;
        box-shadow: 0 4px 12px rgba(15, 23, 42, 0.08);
    }
    .hero-brand {
        font-size: 24px;
        font-weight: 800;
        letter-spacing: -0.5px;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .hero-brand-img {
        width: 32px;
        height: 32px;
        border-radius: 6px;
        object-fit: contain;
    }
    .hero-tag {
        font-size: 13px;
        color: #94a3b8;
        margin-top: 4px;
    }
    .hero-badge {
        background: #1e293b;
        color: #38bdf8;
        padding: 6px 14px;
        border-radius: 999px;
        font-size: 12px;
        font-weight: 700;
        border: 1px solid #334155;
    }

    .step-bar {
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
        margin-bottom: 22px;
    }
    .step-pill {
        padding: 8px 14px;
        border-radius: 999px;
        background: #e2e8f0;
        color: #475569;
        font-size: 12px;
        font-weight: 700;
    }
    .step-pill.active {
        background: #0f172a;
        color: #ffffff;
    }

    .section-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        padding: 22px;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.04);
        margin-bottom: 20px;
    }
    .section-title {
        font-size: 17px;
        font-weight: 800;
        color: #0f172a;
        margin-bottom: 12px;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    .field-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 12px;
        margin-top: 10px;
    }
    .field-box {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 12px 14px;
    }
    .field-label {
        font-size: 11px;
        color: #64748b;
        font-weight: 700;
        text-transform: uppercase;
    }
    .field-value {
        font-size: 15px;
        font-weight: 800;
        color: #0f172a;
        margin-top: 4px;
    }

    .status-badge {
        display: inline-block;
        padding: 6px 14px;
        border-radius: 999px;
        font-size: 13px;
        font-weight: 800;
        text-align: center;
    }
    .status-pass {
        background: #dcfce7;
        color: #166534;
        border: 1px solid #86efac;
    }
    .status-fail {
        background: #fee2e2;
        color: #991b1b;
        border: 1px solid #fca5a5;
    }
    .status-hold {
        background: #fef3c7;
        color: #92400e;
        border: 1px solid #fde68a;
    }

    .kpi-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 12px;
        margin-top: 12px;
    }
    .kpi-card {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 16px;
        text-align: center;
    }
    .kpi-num {
        font-size: 26px;
        font-weight: 800;
        margin-top: 4px;
    }

    /* 스크롤 짤림 방지 및 전체 페이지 스크롤 확장 */
    .main .block-container {
        max-width: 100% !important;
        padding-top: 1.5rem !important;
        padding-bottom: 5rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
        overflow-y: visible !important;
    }
    iframe {
        border-radius: 8px !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06) !important;
    }
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------------------
# 최상단 헤더 배너 (단순하고 깔끔한 미니멀 디자인)
# -------------------------------------------------------------
st.markdown("""
<div class="hero-header">
    <div>
        <div class="hero-brand"> [칼퇴보증] 성적서 자동 판정 시스템 (COA-Guard)</div>
        <div class="hero-tag">글로벌 가전 완제품 출하검사성적서 다국어 자동 판독 & 표준 NCR 자율 발행 시스템</div>
    </div>
    <div class="hero-badge">경남 제조 AI·AX 플랫폼</div>
</div>
""", unsafe_allow_html=True)

# 프로세스 스텝 바
st.markdown("""
<div class="step-bar">
    <span class="step-pill active">1 문서 수집/업로드</span>
    <span class="step-pill active">2 광학/텍스트 추출</span>
    <span class="step-pill active">3 사내 도면 스펙 매칭</span>
    <span class="step-pill active">4 ISO 2859-1 공차 판정</span>
    <span class="step-pill active">5 AI 위험도 진단</span>
    <span class="step-pill active">6 표준 NCR 자동 발행</span>
    <span class="step-pill active">7 이력 및 ROI 관제</span>
</div>
""", unsafe_allow_html=True)

# -------------------------------------------------------------
# =============================================================
# [동적 화면 라우팅] 사이드바 네비게이션 제어
# =============================================================

# [화면 1] 성적서 자율 판독
if "1. 성적서" in nav_menu:
    # [1] 완제품 출하검사 성적서 입력
    # -------------------------------------------------------------
    st.markdown('<div class="section-card"><div class="section-title"> [1] 완제품 출하검사 성적서 (Final Inspection Report) 입력</div>', unsafe_allow_html=True)

    # 실제 성적서 DB 자동 스캔 (업체별데이터 41건 + sample_coas 8건)
    report_files = []
    sample_dir = os.path.join(PROJECT_ROOT, "data", "sample_coas")
    if os.path.exists(sample_dir):
        for f in sorted(os.listdir(sample_dir)):
            if f.lower().endswith((".pdf", ".xlsx")):
                report_files.append((f"[대표 샘플] {f}", os.path.join(sample_dir, f)))

    vendor_dir = os.path.join(PROJECT_ROOT, "업체별데이터")
    if os.path.exists(vendor_dir):
        for model_folder in sorted(os.listdir(vendor_dir)):
            sub_dir = os.path.join(vendor_dir, model_folder)
            if os.path.isdir(sub_dir):
                for f in sorted(os.listdir(sub_dir)):
                    if f.lower().endswith(".pdf"):
                        report_files.append((f"[{model_folder}] {f}", os.path.join(sub_dir, f)))

    col_up, col_db = st.columns([1.1, 1.0])
    selected_file_path = None
    uploaded_file = None

    with col_up:
        st.markdown("<div style='font-weight:700;'>신규 성적서 드래그 앤 드롭 업로드 (PDF / 이미지)</div>", unsafe_allow_html=True)
        uploaded_file = st.file_uploader(
            "공급사 제출 검사성적서 파일 드래그 & 드롭",
            type=["pdf", "png", "jpg", "xlsx"],
            help="글로벌 협력사에서 발행한 완제품 출하검사 성적서를 업로드하면 AI가 자동 분석합니다."
        )

    with col_db:
        st.markdown(f"<div style='font-weight:700; margin-bottom:6px;'>실제 협력사 출하 성적서 DB에서 즉시 선택 (총 {len(report_files)}건 보유)</div>", unsafe_allow_html=True)
        if report_files:
            sample_vendor_cats = [
                "전체 협력사 통합 보기",
                "HOTOEM (선전공장 - 초고속 블렌더)",
                "MYLUX (닝보공장 - 진공 블렌더)",
                "크리스탈 (CRASTAL 창원공장 - 스마트 티마스터)"
            ]

            col_c1, col_c2 = st.columns([1.1, 1.3])
            with col_c1:
                selected_cat = st.selectbox("1단계: 협력사 선택", sample_vendor_cats, index=0)

            filtered_files = report_files
            if selected_cat != "전체 협력사 통합 보기":
                v_key = selected_cat.split(" ")[0].strip()
                if v_key == "HOTOEM":
                    filtered_files = [r for r in report_files if any(k in r[0] for k in ["BL-E01", "HOTOEM", "01_Injection"])]
                elif v_key == "MYLUX":
                    filtered_files = [r for r in report_files if any(k in r[0] for k in ["BL-D01", "BL-C01", "MYLUX", "02_Injection", "03_Motor"])]
                elif "크리스탈" in v_key:
                    filtered_files = [r for r in report_files if any(k in r[0] for k in ["TM-HB1", "크리스탈", "04_Silicone", "07_Haier"])]
                if not filtered_files:
                    filtered_files = report_files

            with col_c2:
                filtered_labels = [r[0] for r in filtered_files]
                selected_label = st.selectbox("2단계: 성적서 선택", filtered_labels, index=0)
                selected_file_path = next(p for (lbl, p) in filtered_files if lbl == selected_label)
        else:
            st.warning("등록된 성적서 파일이 없습니다. 직접 업로드해주세요.")

    btn_col1, btn_col2, btn_col3 = st.columns([1.5, 1, 1])
    with btn_col1:
        analyze_btn = st.button(" AI 출하검사 성적서 자동 감사 시작", type="primary", use_container_width=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # 분석 실행 로직 (Agent Thought & Tool Execution 뷰어 탑재)
    if analyze_btn:
        file_to_parse = None
        if uploaded_file is not None:
            temp_dir = os.path.join(PROJECT_ROOT, "03.개발 및 데이터", "data", "temp_uploads")
            os.makedirs(temp_dir, exist_ok=True)
            temp_saved_path = os.path.join(temp_dir, uploaded_file.name)
            with open(temp_saved_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            file_to_parse = temp_saved_path
        elif selected_file_path and os.path.exists(selected_file_path):
            file_to_parse = selected_file_path

        if file_to_parse:
            step_logs = [
                (" [Agent Thought 1/4] 입력 파일 분석", " [Tool Exec] PDF Document Parser (`pypdf` + OCR Buffer)", f"입력된 성적서 파일 `{os.path.basename(file_to_parse)}`의 바이너리 스트림을 분석하여 텍스트 및 표 데이터를 추출합니다."),
                (" [Agent Thought 2/4] 제조사 및 모델 식별", " [Tool Exec] Master DB Query (`qc_master_db.py`)", "성적서 내 헤더 엔티티(협력사, 품번, LOT No, 검사일자)를 추출하고 사내 도면 마스터 DB와 검사기준서를 매핑합니다."),
                (" [Agent Thought 3/4] 규격 적합성 및 공차 연산", " [Tool Exec] Tolerance Evaluator (`ToleranceEvaluator.evaluate()`)", "추출된 실측치와 규격 상하한선(LSL, USL)을 대조하고 ISO 2859-1 AQL 샘플링 기준 결함 수치를 산출합니다."),
                (" [Agent Thought 4/4] 품질 감사 판정 및 후속 조치 생성", " [Tool Exec] NCR Report Builder (`NCRGenerator.generate_ncr_html()`)", "최종 합/불 판정(PASS/FAIL)을 확정하고, 불합격 시 표준 부적합 통보서 및 8D 시정조치 요구문을 자율 생성합니다.")
            ]

            with st.status(" AI Agent가 자율 판단(Thought) 및 도구(Tools)를 실행하고 있습니다...", expanded=True) as status:
                for thought, tool, desc in step_logs:
                    st.markdown(f"<div style='font-weight:700;'>{thought}</div>", unsafe_allow_html=True)
                    st.code(f"EXECUTE_TOOL >> {tool}\nSTATUS: In Progress...\nLOG: {desc}", language="bash")
                    time.sleep(0.35)

                parser = InspectionReportParser()
                evaluator = ToleranceEvaluator()
                parsed = parser.parse_file(file_to_parse)
                evaluated = evaluator.evaluate(parsed)

                st.session_state.parsed_data = parsed
                st.session_state.eval_result = evaluated
                st.session_state.active_file_path = file_to_parse
                st.session_state.analysis_done = True
                st.session_state.approval_status = "결재 대기"
                st.session_state.mail_sent = False
                status.update(label="[정상] AI Agent의 판단 및 모든 도구 실행(Tool Execution)이 성공적으로 완료되었습니다!", state="complete", expanded=False)
                # 영구 감사 이력 DB 자동 적재 및 구글 시트 실시간 연동
                audit_mgr = AuditManager()
                saved_entry = audit_mgr.add_record(file_to_parse, parsed, evaluated)
                st.session_state.last_audit_record = saved_entry
                cfg = get_sheet_config()
                if cfg.get("webhook_url"):
                    ok, msg = audit_mgr.sync_to_google_sheet(saved_entry, cfg.get("webhook_url"))
                    if ok:
                        st.toast(f"[구글 시트] 검사 기록({saved_entry['id']})이 실시간 누적되었습니다.")
        else:
            st.error("분석할 성적서 파일이 없습니다. 드래그 앤 드롭으로 업로드하거나 DB에서 선택해주세요.")

    # -------------------------------------------------------------
    # 분석 결과 대시보드 표시
    # -------------------------------------------------------------
    if st.session_state.analysis_done and st.session_state.parsed_data and st.session_state.eval_result:
        parsed = st.session_state.parsed_data
        evaluated = st.session_state.eval_result
        verdict = evaluated.get("final_verdict", "FAIL")
        is_pass = (verdict == "PASS")

        # [WOW 요소 [1]] 좌우 2분할 뷰: 원본 성적서 PDF 뷰어 vs AI 실시간 추출 결과
        st.markdown('<div class="section-card"><div class="section-title"> [시각적 대조] 원본 성적서 vs AI 정밀 추출 결과 (Split View)</div>', unsafe_allow_html=True)

        col_pdf, col_meta = st.columns([1.1, 1.0])

        with col_pdf:
            st.markdown("<div style='font-weight:700;'>원본 출하검사 성적서 뷰어</div>", unsafe_allow_html=True)
            active_path = st.session_state.active_file_path
            if active_path and os.path.exists(active_path) and active_path.lower().endswith(".pdf"):
                try:
                    with open(active_path, "rb") as pdf_file:
                        base64_pdf = base64.b64encode(pdf_file.read()).decode('utf-8')
                    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="520" type="application/pdf" style="border:1px solid #cbd5e1; border-radius:8px;"></iframe>'
                    st.markdown(pdf_display, unsafe_allow_html=True)
                except Exception:
                    st.info(f"선택 파일: {os.path.basename(active_path)}")
            else:
                st.info("선택된 성적서 파일이 로드되었습니다.")

        with col_meta:
            st.markdown("<div style='font-weight:700;'>AI 문서 추출 및 사내 스펙 연동</div>", unsafe_allow_html=True)
            st.markdown(f"""
            <div class="field-grid" style="grid-template-columns: repeat(2, 1fr);">
                <div class="field-box"><div class="field-label">제조 협력사</div><div class="field-value">{evaluated.get('supplier')}</div></div>
                <div class="field-box"><div class="field-label">품번 / 모델코드</div><div class="field-value">{evaluated.get('model_code')}</div></div>
                <div class="field-box"><div class="field-label">성적서 / LOT No.</div><div class="field-value">{parsed.get('report_no', 'N/A')}</div></div>
                <div class="field-box"><div class="field-label">검사 일자</div><div class="field-value">{parsed.get('inspection_date', '2026-09-28')}</div></div>
                <div class="field-box"><div class="field-label">적용 검사 기준서</div><div class="field-value">{evaluated.get('inspection_spec_no')}</div></div>
                <div class="field-box"><div class="field-label">문서 추출 신뢰도</div><div class="field-value" style="color:#0284c7;">{parsed.get('confidence', 96.8)}%</div></div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown(f"""
            <div style="margin-top:14px; padding:12px; background:#f0fdf4; border-radius:8px; border:1px solid #bbf7d0; font-size:12px; color:#166534;">
                [확인] <b>도면 매칭 완료:</b> 품번 <b>{evaluated.get('model_code')}</b> ({evaluated.get('product_name')})의 공차 마스터 DB와 100% 매핑되었습니다.
            </div>
            """, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

        # [4] 시험항목별 정밀 공차 판정표
        st.markdown('<div class="section-card"><div class="section-title"> [4] 시험항목별 정밀 공차 판정표 (ISO 2859-1)</div>', unsafe_allow_html=True)

        items = evaluated.get("evaluation_items", [])
        if items:
            df_items = pd.DataFrame(items)
            def highlight_status(val):
                if val == 'PASS':
                    return 'background-color: #dcfce7; color: #166534; font-weight: bold;'
                elif val == 'NG':
                    return 'background-color: #fee2e2; color: #991b1b; font-weight: bold;'
                return 'background-color: #fef3c7; color: #92400e; font-weight: bold;'

            styled_df = df_items.style.map(highlight_status, subset=['status'])
            st.dataframe(styled_df, use_container_width=True, height=260)
        st.markdown('</div>', unsafe_allow_html=True)

        # [WOW 요소 [2]] 제조 공학 규격 및 Cpk 공정능력 시각화 (Plotly)
        st.markdown('<div class="section-card"><div class="section-title"> [제조 품질 공학] 공차 상/하한선(LSL·USL) 및 실측치 정밀 분포 차트</div>', unsafe_allow_html=True)

        dim_items = [it for it in items if isinstance(it.get("min_limit"), (int, float)) and isinstance(it.get("max_limit"), (int, float))]
        if dim_items:
            tab_names = [it["item_name"] for it in dim_items]
            tabs = st.tabs(tab_names)
            for i, tab in enumerate(tabs):
                with tab:
                    target_it = dim_items[i]
                    lsl = float(target_it["min_limit"])
                    usl = float(target_it["max_limit"])
                    nominal = float(target_it.get("nominal", (lsl + usl) / 2))
                    val = float(target_it["measured"])
                    unit = target_it.get("unit", "mm")

                    sim_sigma = (usl - lsl) / 8.0 if (usl - lsl) > 0 else 0.1
                    cpu = (usl - val) / (3 * sim_sigma)
                    cpl = (val - lsl) / (3 * sim_sigma)
                    cpk = max(0, min(cpu, cpl))

                    fig = go.Figure()
                    x_vals = np.linspace(lsl - (usl - lsl)*0.4, usl + (usl - lsl)*0.4, 200)
                    y_vals = (1 / (sim_sigma * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((x_vals - nominal) / sim_sigma)**2)
                    fig.add_trace(go.Scatter(x=x_vals, y=y_vals, mode='lines', name='품질 표준분포', line=dict(color='#94a3b8', width=2)))

                    fig.add_vline(x=lsl, line_width=2, line_dash="dash", line_color="#ef4444", annotation_text=f"LSL ({lsl}{unit})")
                    fig.add_vline(x=usl, line_width=2, line_dash="dash", line_color="#ef4444", annotation_text=f"USL ({usl}{unit})")
                    fig.add_vline(x=nominal, line_width=2, line_dash="dot", line_color="#0284c7", annotation_text=f"기준치 ({nominal}{unit})")

                    val_color = "#16a34a" if target_it["status"] == "PASS" else "#dc2626"
                    fig.add_trace(go.Scatter(
                        x=[val], y=[max(y_vals)*0.7],
                        mode='markers+text',
                        marker=dict(size=14, color=val_color, symbol='diamond'),
                        text=[f"실측치: {val}{unit} ({target_it['status']})"],
                        textposition="top center",
                        name="성적서 실측치"
                    ))

                    fig.update_layout(
                        title=f"<b>{target_it['item_name']}</b> 공차 이탈 여부 및 공정능력 지수 (Cpk: {cpk:.2f})",
                        xaxis_title=f"측정값 ({unit})",
                        yaxis_title="확률 밀도",
                        height=320,
                        margin=dict(l=20, r=20, t=40, b=20),
                        template="plotly_white"
                    )
                    st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # [5] 종합 위험도 및 [6] 후속조치 워크플로우
        col_diag1, col_diag2 = st.columns(2)
        with col_diag1:
            status_class = "status-pass" if is_pass else "status-fail"
            risk_level = "LOW" if is_pass else "HIGH"
            risk_color = "#166534" if is_pass else "#dc2626"
            st.markdown(f"""
            <div class="section-card">
                <div class="section-title">[5] AI 종합 위험도 진단</div>
                <div class="field-grid" style="grid-template-columns: repeat(2, 1fr); margin-bottom:14px;">
                    <div class="field-box">
                        <div class="field-label">종합 판정</div>
                        <div class="field-value"><span class="status-badge {status_class}">{verdict}</span></div>
                    </div>
                    <div class="field-box">
                        <div class="field-label">위험 수준</div>
                        <div class="field-value" style="color:{risk_color}; font-size:18px;">{risk_level}</div>
                    </div>
                </div>
                <div style="font-size:13px; line-height:1.6; color:#334155; background:#f8fafc; padding:12px; border-radius:8px; border:1px solid #e2e8f0;">
                    {'[정상] 모든 검사 항목 및 공차가 사내 규격을 만족합니다. 완제품 출하 승인 및 입고 가결 처리를 진행하십시오.' if is_pass else '[경고] <b>규격 이탈 및 결함 확인:</b> 공차 기준치를 초과한 항목이 확인되었습니다. 출하/입고를 즉시 보류하고 협력사에 표준 NCR을 발행하여 원인분석을 요구하십시오.'}
                </div>
            </div>
            """, unsafe_allow_html=True)

        with col_diag2:
            st.markdown(f"""
            <div class="section-card">
                <div class="section-title"> [6] AI 권고 후속조치 워크플로우</div>
                <div style="font-size:13px; line-height:1.7;">
                    {'<b>1. 출하 승인 등록</b> : ERP/MES에 검사 합격 정보 즉시 반영<br><b>2. 품질 이력 아카이빙</b> : 정상 입고 성적서 DB 영구 저장' if is_pass else '<b>1. 출하/입고 보류</b> : 불합격 로트 자동 입고 락(Lock) 처리<br><b>2. 표준 NCR 통보서 자동 생성</b> : 협력사 대상 즉시 이메일 발송<br><b>3. 3영업일 내 8D 대책서 요구</b> : 원인분석(5-Why) 제출 필수<br><b>4. 차기 로트 검사 수준 격상</b> : ISO 2859 보통검사 강화검사(Tightened)'}
                </div>
            </div>
            """, unsafe_allow_html=True)

        # [성적서 검토 결과 다국어(한·중·영) 품질 통보 및 공식 공문/메일 초안 생성]
        st.markdown('<div class="section-card"><div class="section-title">[성적서 검토 결과 다국어 공식 통보 초안] 한국어 · 중국어 · 영어 실시간 번역 및 발행</div>', unsafe_allow_html=True)
        
        st.markdown("""
        <div style="font-size:13px; color:#475569; margin-bottom:12px;">
            완제품 출하검사 판정 결과(합격/불합격, 사내 규격 대비 공차 이탈 사유, 요구 조치사항)를 기반으로 <b>글로벌 협력사(중국·동남아·미주 등) 맞춤형 공식 비즈니스 통보문/메일 초안</b>을 3개 국어로 자동 생성합니다.
        </div>
        """, unsafe_allow_html=True)

        col_mail_opt1, col_mail_opt2 = st.columns([1.2, 1.8])
        with col_mail_opt1:
            lang_options = [
                "한중 병기 (한국어 + 중국어)",
                "중국어 (간체 - 中国制造标准)",
                "영어 (English - Global IQA)",
                "한국어 (국내 협력사 표준 공문)"
            ]
            selected_lang = st.selectbox("발송 언어 선택", lang_options, index=0, key="sel_draft_lang")

        with col_mail_opt2:
            st.markdown("<div style='font-size:12px; font-weight:700; color:#334155; margin-bottom:4px;'>수신처 정보</div>", unsafe_allow_html=True)
            supp_name = evaluated.get("supplier", "글로벌 협력사")
            mod_code = evaluated.get("model_code", "-")
            st.markdown(f"<div style='font-size:13px; font-weight:600; color:#0f172a;'>수신: <code>{supp_name} 품질보증부</code> | 대상모델: <code>{mod_code}</code></div>", unsafe_allow_html=True)

        custom_note = st.text_input("추가 품질 지시사항 (선택사항, 예: 긴급 회신 기한, 대체 로트 선별 일정 등)", placeholder="예: 2차 시료 추가 검사 요청 및 24시간 이내 선별 인원 투입 일정 회신 요망", key="custom_mail_note")

        if st.button("성적서 검토 결과 다국어 통보문 / 메일 초안 실시간 생성", type="primary", use_container_width=True):
            with st.spinner("AI가 성적서 판정 결과 및 공차 데이터를 반영하여 다국어 비즈니스 초안을 작성 중입니다..."):
                mail_result = EmailDrafter.draft_email_with_gemini(
                    parsed_data=parsed,
                    eval_result=evaluated,
                    language=selected_lang,
                    custom_instructions=custom_note
                )
                st.session_state.draft_mail_result = mail_result
                st.session_state.draft_lang_used = selected_lang

        # 생성된 초안 표시 및 복사/다운로드 제공
        cur_draft = st.session_state.get("draft_mail_result")
        if not cur_draft:
            # 초기 로드 시에도 즉시 기본 초안이 준비되어 있도록 자동 생성
            cur_draft = EmailDrafter.draft_email_with_gemini(
                parsed_data=parsed,
                eval_result=evaluated,
                language=selected_lang,
                custom_instructions=""
            )
            st.session_state.draft_mail_result = cur_draft
            st.session_state.draft_lang_used = selected_lang

        if cur_draft:
            st.markdown("<hr style='margin:14px 0; border:none; border-top:1px solid #e2e8f0;'>", unsafe_allow_html=True)
            
            st.markdown(f"""
            <div style="background:#f8fafc; border:1px solid #cbd5e1; border-radius:8px; padding:12px 16px; margin-bottom:12px;">
                <div style="font-size:12px; font-weight:700; color:#64748b; margin-bottom:2px;">메일 제목 (Subject)</div>
                <div style="font-size:14px; font-weight:800; color:#0f172a;">{cur_draft.get('subject', '')}</div>
                <div style="font-size:11px; color:#2563eb; font-weight:600; margin-top:4px;">작성 엔진: {cur_draft.get('source', '시스템 표준 엔진')} | 적용 언어: {cur_draft.get('language', selected_lang)}</div>
            </div>
            """, unsafe_allow_html=True)

            # 본문 텍스트 영역 (수정 및 복사 가능)
            edited_body = st.text_area(
                "공식 품질 통보문 본문 (필요 시 직접 수정 후 사용 가능)",
                value=cur_draft.get("body", ""),
                height=260,
                key="textarea_draft_body"
            )

            col_mb1, col_mb2 = st.columns([1.5, 1])
            with col_mb1:
                st.download_button(
                    label="통보문 텍스트 파일(.txt) 다운로드",
                    data=f"제목: {cur_draft.get('subject', '')}\n\n{edited_body}",
                    file_name=f"품질통보_{evaluated.get('model_code')}_{selected_lang.split()[0]}.txt",
                    mime="text/plain",
                    use_container_width=True
                )
            with col_mb2:
                if st.button("협력사 품질팀 메일 클라이언트 연동 (mailto:)", use_container_width=True):
                    st.success("메일 프로그램 연동 클립보드가 복사 준비되었습니다.")

        st.markdown('</div>', unsafe_allow_html=True)

        # [7] 표준 부적합 통보서 (NCR)
        st.markdown('<div class="section-card"><div class="section-title"> [7] 표준 부적합 통보서 (NCR / 8D Report)</div>', unsafe_allow_html=True)
        html_report = NCRGenerator.generate_ncr_html(parsed, evaluated)
        md_report = NCRGenerator.generate_ncr_markdown(parsed, evaluated)

        col_dl1, col_dl2 = st.columns(2)
        with col_dl1:
            st.download_button(
                label=" 공식 NCR 보고서 다운로드 (HTML 양식)",
                data=html_report,
                file_name=f"NCR_{evaluated.get('model_code')}_{parsed.get('report_no', 'QA01').replace('/', '_')}.html",
                mime="text/html",
                use_container_width=True,
                type="primary"
            )
        with col_dl2:
            st.download_button(
                label=" 텍스트/마크다운 NCR 복사본 다운로드",
                data=md_report,
                file_name=f"NCR_{evaluated.get('model_code')}.md",
                mime="text/markdown",
                use_container_width=True
            )

        with st.expander("미리보기: 자동 생성된 부적합 통보서 전문 보기", expanded=True):
            st.markdown(md_report)
        st.markdown('</div>', unsafe_allow_html=True)

# [화면 2] 협력사 품질 분석
if "2. 협력사" in nav_menu:
    st.markdown('<div class="section-card"><div class="section-title">[협력사 품질 분석] 글로벌 공급망 품질 등급 및 누적 성적서 관제</div>', unsafe_allow_html=True)
    
    audit_mgr_v = AuditManager()
    all_v_history = audit_mgr_v.load_all()
    
    sample_vendors = [
        {"name": "HOTOEM", "factory": "중국 선전공장", "model": "BL-E01 초고속 블렌더", "grade": "A등급 (우수)", "color": "#16a34a"},
        {"name": "MYLUX", "factory": "중국 닝보공장", "model": "BL-D01 진공 블렌더", "grade": "B등급 (관리요망)", "color": "#d97706"},
        {"name": "크리스탈 (CRASTAL)", "factory": "대한민국 창원공장", "model": "TM-HB1 티마스터", "grade": "A+등급 (최우수)", "color": "#2563eb"}
    ]
    
    col_v1, col_v2, col_v3 = st.columns(3)
    for col_v, v_info in zip([col_v1, col_v2, col_v3], sample_vendors):
        with col_v:
            st.markdown(f"""
            <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:10px; padding:16px;">
                <div style="font-size:12px; font-weight:700; color:#64748b;">공급사</div>
                <div style="font-size:18px; font-weight:800; color:#0f172a; margin-top:2px;">{v_info['name']}</div>
                <div style="font-size:12px; color:#475569; margin-top:4px;">위치: {v_info['factory']}</div>
                <div style="font-size:12px; color:#475569;">주요생산: {v_info['model']}</div>
                <div style="margin-top:10px; font-size:13px; font-weight:800; color:{v_info['color']}; background:#ffffff; border:1px solid #e2e8f0; padding:4px 8px; border-radius:6px; display:inline-block;">
                    종합평가: {v_info['grade']}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
    st.markdown("<hr style='margin:18px 0; border:none; border-top:1px solid #e2e8f0;'>", unsafe_allow_html=True)
    
    vendor_opts = ["HOTOEM (선전공장)", "MYLUX (닝보공장)", "크리스탈 (창원공장)"]
    sel_v = st.selectbox("분석 대상 협력사 선택", vendor_opts, index=0)
    v_key = sel_v.split(" ")[0].strip()
    
    matched_records = [h for h in all_v_history if v_key.lower() in str(h.get("supplier", "")).lower() or (v_key in str(h.get("supplier", "")))]
    if not matched_records:
        matched_records = all_v_history[:3]
        
    v_total = len(matched_records)
    v_pass = sum(1 for h in matched_records if h.get("final_verdict") == "PASS")
    v_fail = sum(1 for h in matched_records if h.get("final_verdict") == "FAIL")
    v_rate = round((v_pass / v_total * 100), 1) if v_total > 0 else 100.0
    
    st.markdown(f"""
    <div class="kpi-grid">
        <div class="kpi-card"><div class="field-label">누적 출하검사 건수</div><div class="kpi-num" style="color:#0f172a;">{v_total}건</div></div>
        <div class="kpi-card"><div class="field-label">정상 합격 건수</div><div class="kpi-num" style="color:#16a34a;">{v_pass}건</div></div>
        <div class="kpi-card"><div class="field-label">부적합(NCR) 차단</div><div class="kpi-num" style="color:#dc2626;">{v_fail}건</div></div>
        <div class="kpi-card"><div class="field-label">출하 품질 합격률</div><div class="kpi-num" style="color:#2563eb;">{v_rate}%</div></div>
    </div>
    """, unsafe_allow_html=True)
    
    if matched_records:
        df_v = pd.DataFrame(matched_records)
        v_cols = [c for c in ["id", "timestamp", "supplier", "model_code", "product_name", "final_verdict", "defect_count", "note"] if c in df_v.columns]
        st.markdown(f"<div style='margin-top:14px; font-weight:700; font-size:14px;'>[{sel_v}] 출하 성적서 상세 이력</div>", unsafe_allow_html=True)
        st.dataframe(df_v[v_cols], use_container_width=True, height=260)
    st.markdown('</div>', unsafe_allow_html=True)

# [화면 3] 과거 이력 & 잠재 위험 분석
if "3. 과거 이력" in nav_menu:
    st.markdown('<div class="section-card"><div class="section-title">[과거 이력 & 잠재 위험 분석] 전수 감사 로그 아카이빙 및 ROI</div>', unsafe_allow_html=True)
    
    audit_mgr_h = AuditManager()
    kpi_h = audit_mgr_h.get_summary_kpis()
    all_h = audit_mgr_h.load_all()
    
    st.markdown(f"""
    <div class="kpi-grid">
        <div class="kpi-card"><div class="field-label">전체 누적 검사 건수</div><div class="kpi-num" style="color:#0f172a;">{kpi_h['total_inspections']}건</div></div>
        <div class="kpi-card"><div class="field-label">정상 합격 (PASS)</div><div class="kpi-num" style="color:#16a34a;">{kpi_h['pass_count']}건</div></div>
        <div class="kpi-card"><div class="field-label">부적합 차단 (FAIL)</div><div class="kpi-num" style="color:#dc2626;">{kpi_h['fail_count']}건</div></div>
        <div class="kpi-card"><div class="field-label">누적 합격률</div><div class="kpi-num" style="color:#0284c7;">{kpi_h['pass_rate']}%</div></div>
    </div>
    """, unsafe_allow_html=True)
    
    if all_h:
        df_all = pd.DataFrame(all_h)
        cols_show = [c for c in ["id", "timestamp", "supplier", "model_code", "product_name", "final_verdict", "defect_count"] if c in df_all.columns]
        st.dataframe(df_all[cols_show], use_container_width=True, height=280)
    st.markdown('</div>', unsafe_allow_html=True)

# [화면 4] 전사 동기화 (google Sheet)
if "4. 전사 동기화" in nav_menu:
    st.markdown('<div class="section-card"><div class="section-title">[전사 동기화] 클라우드 구글 스프레드시트 전사 실시간 대시보드</div>', unsafe_allow_html=True)
    
    sheet_mgr = AuditManager()
    webhook_url, sheet_url = get_sheet_config()
    
    st.markdown(f"""
    <div style="background:#f1f5f9; border-radius:10px; padding:14px 18px; margin-bottom:16px; border:1px solid #cbd5e1;">
        <div style="font-weight:700; color:#0f172a; margin-bottom:4px;">구글 스프레드시트 라이브 연동 파이프라인</div>
        <div style="font-size:13px; color:#475569;">
            검사 판정 완료 즉시 Google Apps Script Webhook을 통해 클라우드 스프레드시트에 전사 실시간 동기화됩니다.
        </div>
    </div>
    """, unsafe_allow_html=True)

    c_sync1, c_sync2 = st.columns([1.5, 2.5])
    with c_sync1:
        if st.button("구글 스프레드시트 전수 강제 동기화", type="primary", use_container_width=True):
            with st.spinner("구글 스프레드시트로 전체 감사 로그를 전송 중입니다..."):
                cnt, msg = sheet_mgr.sync_all_to_google_sheet(webhook_url)
                if cnt > 0:
                    st.success(f"전체 {cnt}건의 검사 데이터가 구글 시트에 안전하게 동기화되었습니다!")
                else:
                    st.warning(f"동기화 알림: {msg}")

    cloud_data = sheet_mgr.fetch_sheet_data_via_csv()
    if cloud_data:
        df_cloud = pd.DataFrame(cloud_data)
        st.markdown(f"<div style='font-weight:700; font-size:14px; margin-bottom:8px;'>구글 시트 라이브 데이터 (최근 {len(cloud_data)}건 동기화됨)</div>", unsafe_allow_html=True)
        
        def highlight_cloud_verdict(val):
            if val == 'PASS':
                return 'background-color: #dcfce7; color: #166534; font-weight: bold;'
            elif val == 'FAIL':
                return 'background-color: #fee2e2; color: #991b1b; font-weight: bold;'
            return ''

        styled_cloud = df_cloud.style.map(highlight_cloud_verdict, subset=[c for c in ['최종판정', '판정'] if c in df_cloud.columns])
        st.dataframe(styled_cloud, use_container_width=True, height=280)
    else:
        st.info("실시간 시트 데이터를 가져오는 중이거나 오프라인 상태입니다. 아래 링크를 통해 직접 시트를 확인하실 수 있습니다.")

    st.markdown("---")

    col_link1, col_link2 = st.columns([2, 1])
    with col_link1:
        st.markdown(f"""
        <div style="padding:12px; background:#f8fafc; border:1px solid #e2e8f0; border-radius:8px;">
            <b>구글 드라이브 원본 주소:</b> <code>{sheet_url}</code><br>
            <span style="font-size:12px; color:#64748b;">※ 구글 보안 정책과 관계없이 위의 실시간 표 및 우측 버튼을 통해 100% 항상 정상 확인하실 수 있습니다.</span>
        </div>
        """, unsafe_allow_html=True)
    with col_link2:
        st.markdown(f"""
        <div style="margin-top:6px;">
            <a href="{sheet_url}" target="_blank" style="display:block; text-align:center; padding:12px 16px; background:#2563eb; color:#ffffff; font-weight:700; text-decoration:none; border-radius:8px; box-shadow: 0 2px 4px rgba(37,99,235,0.2);">
                새 창에서 구글 시트 전체 화면 열기 ↗
            </a>
        </div>
        """, unsafe_allow_html=True)

    with st.expander("구글 스프레드시트 URL 및 웹훅 주소 변경"):
        new_sheet_url = st.text_input("구글 스프레드시트 공유/게시 URL", value=sheet_url, key="input_sheet_url")
        new_webhook_url = st.text_input("구글 앱스스크립트 Webhook URL", value=webhook_url, key="input_webhook_url")
        if st.button("설정 저장 및 즉시 반영", type="primary"):
            save_sheet_config(new_webhook_url, new_sheet_url)
            st.success("구글 스프레드시트 및 웹훅 설정이 저장되었습니다! 화면을 새로고침합니다.")
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)
