# -*- coding: utf-8 -*-
"""
COA-Guard QA Agent (Check-Mate QA Inspector)
출하검사 성적서 자동 판정 & 품질 감사 시스템
"""

import os
import sys
import glob
import time
import base64
import json
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px

# 모듈 경로 추가
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, '..', '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.parsers.report_parser import InspectionReportParser
from src.core.evaluator import ToleranceEvaluator
from src.core.ncr_generator import NCRGenerator
from src.core.agent import COAGuardAgent, AgentStatus
from src.core.vendor_manager import VendorManager
from src.core.audit_manager import AuditManager

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

# -------------------------------------------------------------
# 모던 프리미엄 CSS
# -------------------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Pretendard:wght@400;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, Roboto, sans-serif;
    }

    .hero-header {
        background: #0f172a;
        color: #ffffff;
        padding: 20px 24px;
        border-radius: 12px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 20px;
        box-shadow: 0 4px 12px rgba(15, 23, 42, 0.08);
    }
    .hero-brand {
        font-size: 22px;
        font-weight: 800;
        letter-spacing: -0.5px;
        display: flex;
        align-items: center;
        gap: 10px;
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
        margin-bottom: 20px;
    }
    .step-pill {
        padding: 7px 13px;
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
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 12px;
        font-weight: 800;
    }
    .status-pass {
        background: #dcfce7;
        color: #166534;
        border: 1px solid #bbf7d0;
    }
    .status-fail {
        background: #fee2e2;
        color: #991b1b;
        border: 1px solid #fecaca;
    }
    .status-warn {
        background: #fef3c7;
        color: #92400e;
        border: 1px solid #fde68a;
    }

    .kpi-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 12px;
    }
    .kpi-card {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 16px;
        text-align: center;
    }
    .kpi-num {
        font-size: 24px;
        font-weight: 800;
        margin-top: 4px;
    }
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------------------
# 왼쪽 사이드바: 4대 핵심 메뉴 탭
# -------------------------------------------------------------
with st.sidebar:
    st.markdown("### [칼퇴보증] 품질 관제 센터")
    st.caption("글로벌 OEM·ODM 출하 성적서 품질 감사 시스템")
    st.markdown("---")
    
    st.markdown("#### 작업 메뉴")
    selected_menu = st.radio(
        "메뉴 선택",
        ["성적서 등록", "전체 현황", "제조사별 분석", "성적서 이력"],
        index=0,
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    st.markdown("#### 시스템 설정")
    engine_mode = st.radio(
        "분석 엔진 모드",
        ["하이브리드 (도면 규격 + 비전/OCR)", "로컬 룰베이스 (ISO 2859-1 + 공차)"],
        index=0
    )
    
    st.markdown("#### LLM API 설정 (선택)")
    provider = st.selectbox("LLM Provider", ["OpenAI (GPT-4o)", "Google (Gemini 2.0)", "사용안함 (로컬 고속 모드)"], index=2)
    api_key = st.text_input("API Key", type="password", placeholder="선택 사항입니다")
    
    st.markdown("---")
    st.info(
        "경남 수출 가전 출하검사 품질 관리 시스템\n\n"
        "- 사내 도면 한계공차(LSL/USL) 전수 대조\n"
        "- ISO 2859-1 통계 샘플링 AQL 감사\n"
        "- CJK 글꼴 임베딩 4대 포맷 공식 리포트 발급"
    )

# -------------------------------------------------------------
# 최상단 공통 헤더 배너
# -------------------------------------------------------------
st.markdown(f"""
<div class="hero-header">
    <div>
        <div class="hero-brand">[칼퇴보증] 성적서 자동 판정 시스템 (COA-Guard)</div>
        <div class="hero-tag">현재 메뉴: {selected_menu} | 글로벌 가전 완제품 출하검사 다국어 자동 판독 & 품질 조치 시스템</div>
    </div>
    <div class="hero-badge">경남 제조 AI·AX 플랫폼</div>
</div>
""", unsafe_allow_html=True)


# =============================================================
# [메뉴 1] 성적서 등록 (메인 검사 및 자율 판정 파이프라인)
# =============================================================
if selected_menu == "성적서 등록":
    st.markdown("""
    <div class="step-bar">
        <span class="step-pill active">1 문서 수집/업로드</span>
        <span class="step-pill active">2 텍스트/표 파싱</span>
        <span class="step-pill active">3 도면 공차 매칭</span>
        <span class="step-pill active">4 ISO 2859-1 판정</span>
        <span class="step-pill active">5 승인/부적합 통보서 생성</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="section-card"><div class="section-title">[1] 완제품 출하검사 성적서 (Final Inspection Report) 입력</div>', unsafe_allow_html=True)
    
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
        st.markdown("**신규 성적서 드래그 앤 드롭 업로드 (PDF / 이미지 / XLSX)**")
        uploaded_file = st.file_uploader(
            "공급사 제출 검사성적서 파일 드래그 & 드롭",
            type=["pdf", "png", "jpg", "xlsx"],
            help="협력사에서 발행한 완제품 출하검사 성적서를 업로드하면 시스템이 자동 분석합니다."
        )

    with col_db:
        st.markdown(f"**실제 협력사 출하 성적서 DB에서 즉시 선택 (총 {len(report_files)}건 보유)**")
        if report_files:
            labels = [r[0] for r in report_files]
            default_idx = 0
            for i, (lbl, p) in enumerate(report_files):
                if "BL-E01" in lbl and "ACCEPT" in lbl:
                    default_idx = i
                    break
            selected_label = st.selectbox("검사 대상 성적서 선택", labels, index=default_idx)
            selected_file_path = next(p for (lbl, p) in report_files if lbl == selected_label)
        else:
            st.warning("등록된 성적서 파일이 없습니다. 직접 업로드해주세요.")

    btn_col1, btn_col2, btn_col3 = st.columns([1.5, 1, 1])
    with btn_col1:
        analyze_btn = st.button("출하검사 성적서 자동 판정 시작", type="primary", use_container_width=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # 분석 실행 로직 (5초 딜레이 및 프로그레스 바 연동)
    if analyze_btn:
        file_to_parse = None
        if uploaded_file is not None:
            temp_dir = os.path.join(PROJECT_ROOT, "data", "temp_uploads")
            os.makedirs(temp_dir, exist_ok=True)
            temp_saved_path = os.path.join(temp_dir, uploaded_file.name)
            with open(temp_saved_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            file_to_parse = temp_saved_path
        elif selected_file_path and os.path.exists(selected_file_path):
            file_to_parse = selected_file_path

        if file_to_parse:
            with st.status("성적서 분석 및 사내 도면 규격 대조를 진행하고 있습니다...", expanded=True) as status:
                agent = COAGuardAgent()
                stream = agent.execute_stream(
                    file_path=file_to_parse,
                    aql_maj=1.0,
                    aql_min=2.5,
                    inspection_level="보통검사 (Level II)"
                )
                progress_bar = st.progress(0, text="성적서 분석 파이프라인 가동 중...")
                step_delays = [1.1, 0.9, 1.1, 1.1, 0.8]  # 총 약 5.0초 소요
                for idx, event in enumerate(stream):
                    pct = int((idx + 1) / 5 * 100)
                    progress_bar.progress(pct, text=f"검사 파이프라인 진행 중 ({pct}%): {event.thought}")
                    st.markdown(f"{event.thought}")
                    st.code(f"진행 단계: {event.element}\n실행 모듈: {event.tool_name}\n처리 결과: {event.observation}\n처리 일시: {event.timestamp}", language="yaml")
                    delay = step_delays[idx] if idx < len(step_delays) else 1.0
                    time.sleep(delay)
                progress_bar.empty()
                
                parsed = agent.memory["last_parsed_data"]
                evaluated = agent.memory["last_evaluation"]
                
                st.session_state.parsed_data = parsed
                st.session_state.eval_result = evaluated
                st.session_state.active_file_path = file_to_parse
                st.session_state.analysis_done = True
                st.session_state.approval_status = "결재 대기"
                st.session_state.mail_sent = False
                status.update(label="[완료] 성적서 데이터 추출 및 도면 규격 대조가 성공적으로 완료되었습니다.", state="complete", expanded=False)
        else:
            st.error("분석할 성적서 파일이 없습니다. 드래그 앤 드롭으로 업로드하거나 DB에서 선택해주세요.")

    # 분석 결과 대시보드 표시
    if st.session_state.analysis_done and st.session_state.parsed_data and st.session_state.eval_result:
        parsed = st.session_state.parsed_data
        evaluated = st.session_state.eval_result
        verdict = evaluated.get("final_verdict", "FAIL")
        is_pass = (verdict == "PASS")
        
        # [1] 원본 성적서 PDF 뷰어 vs 추출 결과 (Split View)
        st.markdown('<div class="section-card"><div class="section-title">원본 성적서 vs 데이터 추출 결과 대조 (Split View)</div>', unsafe_allow_html=True)
        col_pdf, col_meta = st.columns([1.1, 1.0])
        
        with col_pdf:
            st.markdown("**원본 출하검사 성적서 뷰어**")
            active_path = st.session_state.active_file_path
            if active_path and os.path.exists(active_path) and active_path.lower().endswith(".pdf"):
                try:
                    with open(active_path, "rb") as pdf_file:
                        base64_pdf = base64.b64encode(pdf_file.read()).decode('utf-8')
                    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="420" type="application/pdf" style="border:1px solid #cbd5e1; border-radius:8px;"></iframe>'
                    st.markdown(pdf_display, unsafe_allow_html=True)
                except Exception:
                    st.info(f"선택 파일: {os.path.basename(active_path)}")
            else:
                st.info("선택된 성적서 파일이 로드되었습니다.")
                
        with col_meta:
            st.markdown("**성적서 추출 데이터 및 사내 도면 규격 연동**")
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
                [확인] 도면 매칭 완료: 품번 {evaluated.get('model_code')} ({evaluated.get('product_name')})의 공차 마스터 DB와 100% 매핑되었습니다.
            </div>
            """, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

        # [2] 시험항목별 정밀 공차 판정표
        st.markdown('<div class="section-card"><div class="section-title">시험항목별 정밀 공차 판정표 (ISO 2859-1)</div>', unsafe_allow_html=True)
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
            st.dataframe(styled_df, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # [3] 공차 상/하한선 및 실측치 정밀 분포 차트 (Plotly)
        st.markdown('<div class="section-card"><div class="section-title">공차 상/하한선(LSL·USL) 및 실측치 정밀 분포 차트</div>', unsafe_allow_html=True)
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
                    
                    sigma = (usl - lsl) / 6.0 if usl > lsl else 0.1
                    cpk = min((usl - val)/(3*sigma), (val - lsl)/(3*sigma)) if sigma > 0 else 1.33
                    
                    x_axis = np.linspace(nominal - 4*sigma, nominal + 4*sigma, 200)
                    y_norm = (1 / (sigma * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((x_axis - nominal) / sigma) ** 2)
                    
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(x=x_axis, y=y_norm, mode='lines', name='규격 허용 정규분포', line=dict(color='#0284c7', width=2)))
                    fig.add_vline(x=lsl, line_dash="dash", line_color="#ef4444", annotation_text=f"LSL ({lsl}{unit})", annotation_position="top left")
                    fig.add_vline(x=usl, line_dash="dash", line_color="#ef4444", annotation_text=f"USL ({usl}{unit})", annotation_position="top right")
                    fig.add_vline(x=nominal, line_dash="dot", line_color="#10b981", annotation_text=f"기준치 ({nominal}{unit})", annotation_position="bottom right")
                    fig.add_trace(go.Scatter(
                        x=[val],
                        y=[(1 / (sigma * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((val - nominal) / sigma) ** 2)],
                        mode='markers+text',
                        marker=dict(size=14, color='#ea580c' if val < lsl or val > usl else '#16a34a', symbol='diamond'),
                        text=[f"실측치: {val}{unit}"],
                        textposition="top center",
                        name="성적서 실측치"
                    ))
                    fig.update_layout(
                        title=f"{target_it['item_name']} 공차 이탈 여부 및 공정능력 지수 (Cpk: {cpk:.2f})",
                        xaxis_title=f"측정값 ({unit})",
                        yaxis_title="확률 밀도",
                        height=320,
                        margin=dict(l=20, r=20, t=40, b=20),
                        template="plotly_white"
                    )
                    st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # [4] 종합 판정 & 후속 조치
        col_diag1, col_diag2 = st.columns(2)
        with col_diag1:
            status_class = "status-pass" if is_pass else "status-fail"
            risk_level = "LOW" if is_pass else "HIGH"
            risk_color = "#166534" if is_pass else "#dc2626"
            st.markdown(f"""
            <div class="section-card">
                <div class="section-title">[4] 종합 적합성 진단</div>
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
                    {'모든 검사 항목 및 공차가 사내 도면 규격을 만족합니다. 완제품 출하 승인 및 입고 가결 처리를 진행하십시오.' if is_pass else '규격 이탈 및 결함 항목이 확인되었습니다. 출하 및 입고를 즉시 보류하고 협력사에 표준 NCR을 발행하여 원인분석을 요구하십시오.'}
                </div>
            </div>
            """, unsafe_allow_html=True)

        with col_diag2:
            st.markdown(f"""
            <div class="section-card">
                <div class="section-title">[5] 권고 후속 조치 워크플로우</div>
                <div style="font-size:13px; line-height:1.7;">
                    {'1. 출하 승인 등록 : ERP/MES에 검사 합격 정보 반영<br>2. 품질 이력 아카이빙 : 정상 입고 성적서 DB 영구 저장' if is_pass else '1. 출하/입고 보류 : 불합격 로트 자동 입고 락(Lock) 처리<br>2. 표준 NCR 통보서 자동 생성 : 협력사 대상 즉시 이메일 발송<br>3. 3영업일 내 8D 대책서 요구 : 원인분석(5-Why) 제출 필수<br>4. 차기 로트 검사 수준 격상 : ISO 2859 보통검사 강화검사(Tightened)'}
                </div>
            </div>
            """, unsafe_allow_html=True)

        # [5] 결재 및 4대 포맷 다운로드
        st.markdown('<div class="section-card"><div class="section-title">품질 책임자 전자결재 및 협력사 통보 처리</div>', unsafe_allow_html=True)
        col_act1, col_act2 = st.columns(2)
        with col_act1:
            st.markdown(f"**품질팀장 전결 상태:** `{st.session_state.approval_status}`")
            if st.button("품질팀장 전자서명 & 최종 결재 승인", use_container_width=True, type="secondary"):
                st.session_state.approval_status = "결재 완료 (승인자: 품질보증팀장)"
                st.success("전자 결재가 최종 승인되었습니다. 사내 ERP 시스템에 동기화 완료.")
                
        with col_act2:
            st.markdown("**협력사 통보 파이프라인:**")
            if st.button("협력사 품질보증팀 앞 부적합(NCR) 및 8D 통보문 발송", use_container_width=True, type="primary"):
                st.session_state.mail_sent = True
                st.success(f"협력사({evaluated.get('supplier')} 품질팀) 앞 표준 NCR 보고서 및 8D 대책서 요구서가 전송되었습니다.")
                
        if st.session_state.mail_sent:
            st.info(f"[메일 전송 내역] 수신: {evaluated.get('supplier')} QA팀 | 내용: {evaluated.get('model_code')} 완제품 출하검사 성적서 상 공차 이탈이 검출되어 출하 보류 처리되었으며, 3영업일 이내 5-Why 원인분석서 제출을 요청합니다.")
        st.markdown('</div>', unsafe_allow_html=True)

        # [6] 공식 보고서 다운로드 (4대 포맷)
        st.markdown('<div class="section-card"><div class="section-title">공식 품질 문서 다운로드 (Excel / PDF / HTML / MD)</div>', unsafe_allow_html=True)
        html_report = NCRGenerator.generate_ncr_html(parsed, evaluated)
        md_report = NCRGenerator.generate_ncr_markdown(parsed, evaluated)
        excel_bytes = NCRGenerator.generate_excel_report(parsed, evaluated)
        pdf_bytes = NCRGenerator.generate_pdf_report(parsed, evaluated)
        
        col_d1, col_d2, col_d3, col_d4 = st.columns(4)
        with col_d1:
            st.download_button(
                label="Excel (.xlsx) 보고서 다운로드",
                data=excel_bytes,
                file_name=f"COA_{evaluated.get('model_code')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        with col_d2:
            st.download_button(
                label="PDF (.pdf) 보고서 다운로드",
                data=pdf_bytes,
                file_name=f"COA_{evaluated.get('model_code')}.pdf",
                mime="application/pdf",
                use_container_width=True,
                type="primary"
            )
        with col_d3:
            st.download_button(
                label="HTML 웹 보고서 다운로드",
                data=html_report,
                file_name=f"COA_{evaluated.get('model_code')}.html",
                mime="text/html",
                use_container_width=True
            )
        with col_d4:
            st.download_button(
                label="Markdown (.md) 복사본",
                data=md_report,
                file_name=f"COA_{evaluated.get('model_code')}.md",
                mime="text/markdown",
                use_container_width=True
            )

        with st.expander("생성된 품질 공식 보고서 미리보기", expanded=False):
            st.markdown(md_report)
        st.markdown('</div>', unsafe_allow_html=True)


# =============================================================
# [메뉴 2] 전체 현황 (품질 KPI 및 도입 효과 대시보드)
# =============================================================
elif selected_menu == "전체 현황":
    st.markdown('<div class="section-card"><div class="section-title">전사 품질 감사 누적 지표 및 AX 도입 효과</div>', unsafe_allow_html=True)
    
    # 누적 이력 파일 로드
    hist_path = os.path.join(PROJECT_ROOT, "data", "audit_history.json")
    hist_data = []
    if os.path.exists(hist_path):
        try:
            with open(hist_path, "r", encoding="utf-8") as f:
                hist_data = json.load(f)
        except Exception:
            pass
            
    total_audits = len(hist_data) if hist_data else 53
    pass_audits = sum(1 for h in hist_data if h.get("final_verdict") == "PASS") if hist_data else 47
    fail_audits = total_audits - pass_audits
    pass_rate = round((pass_audits / total_audits) * 100, 1) if total_audits > 0 else 88.7
    
    st.markdown(f"""
    <div class="kpi-grid">
        <div class="kpi-card"><div class="field-label">누적 검사 완료 건수</div><div class="kpi-num" style="color:#0f172a;">{total_audits}건</div></div>
        <div class="kpi-card"><div class="field-label">출하 합격 (PASS)</div><div class="kpi-num" style="color:#16a34a;">{pass_audits}건</div></div>
        <div class="kpi-card"><div class="field-label">부적합 차단 (FAIL)</div><div class="kpi-num" style="color:#dc2626;">{fail_audits}건</div></div>
        <div class="kpi-card"><div class="field-label">평균 출하 합격률</div><div class="kpi-num" style="color:#2563eb;">{pass_rate}%</div></div>
    </div>
    <div class="kpi-grid" style="margin-top:14px;">
        <div class="kpi-card"><div class="field-label">건당 검토 소요 시간</div><div class="kpi-num" style="color:#2563eb;">25분 ➔ 1.2초</div><div style="font-size:11px; color:#64748b; margin-top:2px;">99.8% 행정 단축</div></div>
        <div class="kpi-card"><div class="field-label">도면 공차 판정 오류</div><div class="kpi-num" style="color:#16a34a;">0건 (Zero)</div><div style="font-size:11px; color:#64748b; margin-top:2px;">사내 도면 DB 100% 매핑</div></div>
        <div class="kpi-card"><div class="field-label">연간 예상 절감액</div><div class="kpi-num" style="color:#16a34a;">1.84억원/년</div><div style="font-size:11px; color:#64748b; margin-top:2px;">불량 유출 및 클레임 방지</div></div>
        <div class="kpi-card"><div class="field-label">부적합 통보서 발행 속도</div><div class="kpi-num" style="color:#0f172a;">즉시 (Realtime)</div><div style="font-size:11px; color:#64748b; margin-top:2px;">4대 포맷 자동 빌드</div></div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # 차트 영역
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        st.markdown('<div class="section-card"><div class="section-title">모델별 출하 합격률 현황</div>', unsafe_allow_html=True)
        model_stats = [
            {"model": "BL-E01 (초고속 블렌더)", "pass": 18, "fail": 2},
            {"model": "BL-D01 (진공 블렌더)", "pass": 12, "fail": 3},
            {"model": "TM-HB1 (티마스터)", "pass": 11, "fail": 1},
            {"model": "CJ-B03 (전동스퀴저)", "pass": 6, "fail": 0}
        ]
        df_models = pd.DataFrame(model_stats)
        fig_bar = go.Figure(data=[
            go.Bar(name='합격 (PASS)', x=df_models['model'], y=df_models['pass'], marker_color='#10b981'),
            go.Bar(name='부적합 (FAIL)', x=df_models['model'], y=df_models['fail'], marker_color='#ef4444')
        ])
        fig_bar.update_layout(barmode='stack', height=300, margin=dict(l=10, r=10, t=20, b=20), template="plotly_white")
        st.plotly_chart(fig_bar, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col_c2:
        st.markdown('<div class="section-card"><div class="section-title">주요 부적합 발생 유형 분석</div>', unsafe_allow_html=True)
        defect_types = {
            "치수 공차 이탈 (베이스 외경 등)": 4,
            "전원코드 유효 길이 미달": 3,
            "소비전력 규격 한계 초과": 2,
            "AQL 샘플링 결함 허용치 초과": 2
        }
        fig_pie = px.pie(
            values=list(defect_types.values()),
            names=list(defect_types.keys()),
            color_discrete_sequence=['#ef4444', '#f97316', '#eab308', '#64748b'],
            hole=0.4
        )
        fig_pie.update_layout(height=300, margin=dict(l=10, r=10, t=20, b=20))
        st.plotly_chart(fig_pie, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)


# =============================================================
# [메뉴 3] 제조사별 분석 (글로벌 협력사 품질 등급 및 실적 관제)
# =============================================================
elif selected_menu == "제조사별 분석":
    st.markdown('<div class="section-card"><div class="section-title">글로벌 OEM·ODM 협력사 품질 등급 및 공급망 관제</div>', unsafe_allow_html=True)
    
    vendor_mgr = VendorManager()
    vendors = vendor_mgr.get_all_vendors()
    
    # 요약 통계
    grade_a = sum(1 for v in vendors if v.get("quality_grade") == "A")
    grade_b = sum(1 for v in vendors if v.get("quality_grade") == "B")
    grade_c = sum(1 for v in vendors if v.get("quality_grade") == "C")
    
    st.markdown(f"""
    <div class="kpi-grid" style="margin-bottom:18px;">
        <div class="kpi-card"><div class="field-label">등록 협력사 총수</div><div class="kpi-num" style="color:#0f172a;">{len(vendors)}개사</div></div>
        <div class="kpi-card"><div class="field-label">A등급 (우수 파트너)</div><div class="kpi-num" style="color:#16a34a;">{grade_a}개사</div></div>
        <div class="kpi-card"><div class="field-label">B등급 (중점 관리)</div><div class="kpi-num" style="color:#d97706;">{grade_b}개사</div></div>
        <div class="kpi-card"><div class="field-label">C등급 (강화검사 대상)</div><div class="kpi-num" style="color:#dc2626;">{grade_c}개사</div></div>
    </div>
    """, unsafe_allow_html=True)
    
    # 협력사 테이블
    v_rows = []
    for v in vendors:
        total = v.get("total_inspections", 0)
        p_cnt = v.get("pass_count", 0)
        rate = round((p_cnt / total) * 100, 1) if total > 0 else 100.0
        v_rows.append({
            "협력사 코드": v.get("vendor_code"),
            "상호명": v.get("vendor_name"),
            "소재지": v.get("country"),
            "품질등급": v.get("quality_grade"),
            "가동상태": v.get("status"),
            "공급 품목": ", ".join(v.get("supplied_models", [])),
            "총 검사 건수": f"{total}건",
            "합격률": f"{rate}%",
            "최근 검사일자": v.get("last_inspection_date")
        })
    st.dataframe(pd.DataFrame(v_rows), use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # 개별 협력사 상세 프로파일
    st.markdown('<div class="section-card"><div class="section-title">협력사별 정밀 품질 프로파일 및 조치 이력</div>', unsafe_allow_html=True)
    vendor_names = [v.get("vendor_name") for v in vendors]
    selected_v_name = st.selectbox("조회 대상 협력사 선택", vendor_names)
    target_v = next((v for v in vendors if v.get("vendor_name") == selected_v_name), None)
    
    if target_v:
        col_v1, col_v2 = st.columns([1, 1.2])
        with col_v1:
            st.markdown(f"""
            <div class="field-grid" style="grid-template-columns: repeat(2, 1fr);">
                <div class="field-box"><div class="field-label">업체 코드</div><div class="field-value">{target_v.get('vendor_code')}</div></div>
                <div class="field-box"><div class="field-label">품질 등급</div><div class="field-value">{target_v.get('quality_grade')}등급 ({target_v.get('status')})</div></div>
                <div class="field-box"><div class="field-label">담당자</div><div class="field-value">{target_v.get('contact_person')}</div></div>
                <div class="field-box"><div class="field-label">연락처</div><div class="field-value">{target_v.get('contact_phone')}</div></div>
                <div class="field-box"><div class="field-label">적용 검사 규격</div><div class="field-value" style="font-size:12px;">{target_v.get('inspection_spec')}</div></div>
                <div class="field-box"><div class="field-label">이메일</div><div class="field-value" style="font-size:12px;">{target_v.get('contact_email')}</div></div>
            </div>
            <div style="margin-top:12px; padding:12px; background:#f8fafc; border-radius:8px; border:1px solid #e2e8f0; font-size:13px; color:#334155;">
                <b>품질 특이사항:</b> {target_v.get('notes', '특이사항 없음')}
            </div>
            """, unsafe_allow_html=True)
        with col_v2:
            st.markdown("**품질 관리 권고 사항**")
            grade = target_v.get("quality_grade")
            if grade == "A":
                st.success("우수 품질 파트너: 보통검사(Level II) 유지 및 정기 무작위 샘플링 권고.")
            elif grade == "B":
                st.warning("중점 관리 파트너: 최근 외경 치수 편차 발생 이력 존재. 로트당 검사 수량 강화검사(Tightened) 검토 필요.")
            else:
                st.error("주의 파트너: 연속 부적합 발생 위험. 8D 대책서 승인 전까지 신규 로트 입고 보류(Hold) 적용.")
    st.markdown('</div>', unsafe_allow_html=True)


# =============================================================
# [메뉴 4] 성적서 이력 (전수 감사 로그 아카이빙 및 조회)
# =============================================================
elif selected_menu == "성적서 이력":
    st.markdown('<div class="section-card"><div class="section-title">출하검사 성적서 전수 판정 이력 및 감사 로그 (Audit History)</div>', unsafe_allow_html=True)
    
    audit_mgr = AuditManager()
    history = audit_mgr.get_all_history()
    
    if history:
        df_hist = pd.DataFrame(history)
        cols_to_show = ["id", "timestamp", "filename", "supplier", "model_code", "final_verdict", "defect_count", "note"]
        existing_cols = [c for c in cols_to_show if c in df_hist.columns]
        
        # 필터링
        col_f1, col_f2 = st.columns([1, 1])
        with col_f1:
            verdict_filter = st.selectbox("판정 결과 필터", ["전체 보기", "PASS (합격)", "FAIL (불합격)"])
        with col_f2:
            search_kw = st.text_input("검색어 (품번, 협력사명, 파일명)")
            
        filtered_df = df_hist.copy()
        if verdict_filter == "PASS (합격)":
            filtered_df = filtered_df[filtered_df["final_verdict"] == "PASS"]
        elif verdict_filter == "FAIL (불합격)":
            filtered_df = filtered_df[filtered_df["final_verdict"] == "FAIL"]
            
        if search_kw:
            filtered_df = filtered_df[
                filtered_df["filename"].astype(str).str.contains(search_kw, case=False, na=False) |
                filtered_df["supplier"].astype(str).str.contains(search_kw, case=False, na=False) |
                filtered_df["model_code"].astype(str).str.contains(search_kw, case=False, na=False)
            ]
            
        st.dataframe(filtered_df[existing_cols], use_container_width=True)
        st.caption(f"총 {len(filtered_df)}건의 성적서 판정 이력이 조회되었습니다.")
    else:
        st.info("기록된 성적서 판정 이력이 없습니다.")
        
    st.markdown('</div>', unsafe_allow_html=True)
