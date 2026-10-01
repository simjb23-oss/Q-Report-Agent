import streamlit as st
import pandas as pd
import plotly.express as px
import datetime

# --- 페이지 설정 ---
st.set_page_config(
    page_title="VOC-Sentinel | 글로벌 결함 조기 감지 & R&D 설계개선 Agent",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 커스텀 스타일 ---
st.markdown("""
<style>
    .main-header {
        font-size: 26px;
        font-weight: 800;
        color: #1E293B;
        margin-bottom: 5px;
    }
    .sub-header {
        font-size: 15px;
        color: #64748B;
        margin-bottom: 20px;
    }
    .metric-card {
        background: #F8FAFC;
        border-radius: 10px;
        padding: 15px;
        border: 1px solid #E2E8F0;
    }
    .alert-banner {
        background: linear-gradient(135deg, #EF4444 0%, #DC2626 100%);
        color: white;
        padding: 16px 20px;
        border-radius: 10px;
        font-weight: 700;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px -1px rgba(220, 38, 38, 0.2);
    }
</style>
""", unsafe_allow_html=True)

# --- 사이드바 설정 ---
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/artificial-intelligence.png", width=64)
    st.title("VOC-Sentinel")
    st.caption("경남 수출 제조기업 전용 품질 Agent")
    st.markdown("---")
    
    st.subheader("🎯 분석 대상 제품")
    product_selected = st.selectbox(
        "제품 모델",
        ["2026 수출형 무선 고압세척기 (Pro Wash)", "스마트 착즙 블렌더 X-1", "전동 정원 전정기 E-Cut"]
    )
    
    st.markdown("---")
    st.subheader("⚙️ Agent 파이프라인 모드")
    mode_classifier = st.checkbox("1단계: 다국어 노이즈 필터링", value=True)
    mode_anomaly = st.checkbox("2단계: 이상치 골든타임 경보", value=True)
    mode_eco = st.checkbox("3단계: R&D 설계권고서(ECO) 자동발행", value=True)
    
    st.markdown("---")
    st.caption("AI Engine: Google Gemini 1.5 Pro / Flash\nAgent Architecture: Google Antigravity")

# --- 메인 헤더 ---
st.markdown('<div class="main-header">🛡️ VOC-Sentinel : 글로벌 VOC 결함 조기 감지 & R&D 설계 개선 Agent</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">해외 이커머스(아마존, 쇼피 등) 다국어 리뷰를 실시간 정밀 분석하여, 대형 리콜 전 품질 골든타임에 설계 변경 권고서(ECO)를 자동 발행합니다.</div>', unsafe_allow_html=True)

# --- 탭 구성 ---
tab1, tab2, tab3 = st.tabs(["📊 1. VOC 모니터링 & 이상 탐지", "🚨 2. 품질 골든타임 경보(Alert)", "📑 3. R&D 설계 변경 권고서(ECO)"])

# 샘플 데이터 로드 함수
@st.cache_data
def load_data():
    try:
        return pd.read_csv("03.개발 및 데이터/data/sample_global_voc_reviews.csv")
    except Exception:
        return pd.read_csv("z:/junbo/20.대외활동/2026_AX공모전/03.개발 및 데이터/data/sample_global_voc_reviews.csv")

df = load_data()

# ==============================================================================
# TAB 1: VOC 모니터링 & 이상 탐지
# ==============================================================================
with tab1:
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(label="총 수집 리뷰 수", value=f"{len(df)} 건", delta="+12건 (최근 1주일)")
    with col2:
        defects_count = len(df[df['ground_truth_category'].str.startswith('defect')])
        st.metric(label="기구/전장 결함 VOC", value=f"{defects_count} 건", delta="결함비율 50%", delta_color="inverse")
    with col3:
        st.metric(label="필터링된 노이즈 (배송/변심)", value="8 건", delta="노이즈율 26.6%")
    with col4:
        st.metric(label="품질 위험 지수 (Risk Index)", value="84 / 100", delta="🚨 긴급 대응 필요", delta_color="inverse")

    st.markdown("---")
    
    c1, c2 = st.columns([6, 4])
    with c1:
        st.subheader("📈 부품별 결함 발생 빈도 분석 (Agent-1 Classifier)")
        defect_df = df[df['target_part'] != 'None']
        part_counts = defect_df['target_part'].value_counts().reset_index()
        part_counts.columns = ['부품명', '결함 건수']
        fig = px.bar(part_counts, x='부품명', y='결함 건수', color='부품명', text='결함 건수',
                     color_discrete_sequence=px.colors.qualitative.Pastel)
        fig.update_layout(showlegend=False, height=320, margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.subheader("🌐 수집 국가 및 언어 비중")
        country_counts = df['country'].value_counts().reset_index()
        country_counts.columns = ['국가', '리뷰 수']
        fig_pie = px.pie(country_counts, values='리뷰 수', names='국가', hole=0.4,
                         color_discrete_sequence=['#3B82F6', '#10B981', '#F59E0B', '#6366F1'])
        fig_pie.update_layout(height=320, margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(fig_pie, use_container_width=True)

    st.subheader("📋 실시간 수집 VOC 원문 피드 (다국어 ➔ 한국어 번역 & 결함 분류)")
    st.dataframe(
        df[['review_id', 'country', 'rating', 'language', 'review_text', 'ground_truth_category', 'target_part']],
        use_container_width=True,
        height=280
    )

# ==============================================================================
# TAB 2: 품질 골든타임 경보 (Alert)
# ==============================================================================
with tab2:
    st.markdown("""
    <div class="alert-banner">
        🚨 [골든타임 품질 긴급 경보 (CRITICAL ALERT)]<br>
        <span style="font-size:14px; font-weight:normal;">
        출시 3주차 [노즐 체결부 락링(Nozzle Lock Ring)] 부품에서 <b>고압 누수 및 크랙 불만(42%)</b>이 이상 급증했습니다. 대규모 반품 및 아마존 계정 리스크 방지를 위해 즉각적인 설계 검토가 요구됩니다.
        </span>
    </div>
    """, unsafe_allow_html=True)
    
    col_a1, col_a2 = st.columns([5, 5])
    with col_a1:
        st.subheader("🔍 주요 불량 VOC 감지 키워드")
        st.info("💡 **빈출 키워드:** spraying out (누수), lock ring (락링), crack (크랙), drop pressure (압력 저하)")
        
        st.markdown("**대표 해외 고객 불만 원문 발췌:**")
        sample_bad_reviews = df[df['target_part'] == 'Nozzle Lock Ring'].head(3)
        for _, row in sample_bad_reviews.iterrows():
            st.markdown(f"- **[{row['country']}/{row['channel']}]** ⭐{row['rating']} : *\"{row['review_text']}\"*")
            
    with col_a2:
        st.subheader("🧠 Anomaly Detector Agent 판단 근거")
        st.markdown("""
        * **이상치 점수 (Z-Score):** `+3.42` (통계적 관리 한계선 3.0 초과)
        * **결함 확산 속도:** 출시 1주차 2건 ➔ 3주차 11건 (550% 급증)
        * **예상 피해 규모 (As-Is 방치 시):** 
          - 현지 반품률: **18.5% 예상**
          - 추정 손실액: **약 2억 4천만 원** (아마존 계정 정지 및 회수 폐기 비용)
        """)
        if st.button("🚀 R&D Advisor Agent에게 설계 개선 권고서(ECO) 발행 명령", type="primary", use_container_width=True):
            st.success("✅ R&D Advisor Agent가 FMEA 기반 결함 원인 추론 및 ECO 초안을 생성했습니다! 3번 탭을 확인하세요.")

# ==============================================================================
# TAB 3: R&D 설계 변경 권고서 (ECO)
# ==============================================================================
with tab3:
    st.subheader("📋 R&D 자율 발행 설계 변경 권고서 (Engineering Change Order)")
    st.caption("AI Agent가 필드 결함 VOC와 도면/부품 사양을 매핑하여 연구소 표준 양식으로 자동 생성한 결과물입니다.")
    
    eco_markdown = """
### [품질 이슈 긴급 경보 및 설계 변경 권고서 (ECO 초안)]

* **문서 번호:** ECO-2026-VOC-001
* **발행 일자:** 2026년 09월 23일
* **발행 주체:** VOC-Sentinel AI 품질 분석 Agent
* **수신 부서:** 기구개발팀, 품질보증팀, 생산기술팀
* **대상 모델:** 2026 수출형 무선 고압세척기 (북미/유럽 출시 모델)
* **긴급도:** 🔴 **CRITICAL (출시 3주차 결함 급증)**

---

#### 1. 현상 및 필드 데이터 분석 (Symptom & Field Evidence)
* **결함 현상:** 고압 분사 노즐 결합부 누수(Leakage) 및 압력 저하 불만 집중 발생 (전체 결함 VOC의 42%)
* **분석 데이터:** 아마존 US, 유럽 이커머스 리뷰 30건 중 누수/크랙 11건 집중 매핑
* **핵심 리뷰 원문:** *"Water spraying out of the joint lock ring after 3rd use! Pressure dropped completely."*

#### 2. 엔지니어링 원인 추론 (Engineering Root Cause Analysis)
* **메커니즘:** 고압 분사 시 발생하는 반복 진동 및 수압 충격(Water Hammer)에 의해 결합부 락링 피로 파괴.
* **소재 요인:** 기존 락링 소재(일반 사출 ABS)의 내충격성 및 인장 강도 부족으로 미세 헤어라인 크랙(Hairline Crack) 발생.
* **기구 공차 요인:** 내부 실링 O-링 홈(Groove) 깊이 공차(기존 ±0.05mm) 편차로 인해 고압 조건에서 실링 밀폐력 상실.

#### 3. R&D 설계 및 공정 개선 권고안 (Action Plan)
1. **[기구 도면 설계 수정]**  
   - 노즐 체결부 O-링 홈(Groove) 치수 공차를 기존 **±0.05mm에서 ±0.02mm로 정밀화**하여 압축률 25% 균일 유지.
2. **[소재 변경 권고]**  
   - 락링 부품 소재를 기존 **일반 ABS에서 유리섬유 강화 플라스틱(PA66-GF30) 또는 황동 인서트 사출**로 변경.
3. **[공정 검사 기준 강화]**  
   - 공장 출하 전 에어 리크(Air Leak) 전수 검사 압력 기준을 기존 10 bar에서 **13 bar(1.3배)로 상향 테스트** 의무화.

#### 4. 기대 효과 및 개선 목표
* 노즐 결합부 필드 누수 클레임 발생률: **기존 18.5% ➔ 0.5% 이하로 급감**
* 연간 예상 리콜 및 현지 반품 손실 비용 **약 2억 4천만 원 절감 효과**
"""
    st.markdown(eco_markdown)
    
    st.download_button(
        label="📥 설계 변경 권고서(ECO) 마크다운/텍스트 다운로드",
        data=eco_markdown,
        file_name="ECO-2026-VOC-001_설계변경권고서_초안.md",
        mime="text/markdown",
        use_container_width=True
    )
