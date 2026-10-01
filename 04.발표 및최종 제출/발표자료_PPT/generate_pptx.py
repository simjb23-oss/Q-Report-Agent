# -*- coding: utf-8 -*-
"""
2026 경남 AI·SW 경진대회 본선 발표자료 10장 PPTX 자동 생성기
팀명: 칼퇴보증 | 작품명: 칼퇴보증 : 성적서 분석 에이전트 (COA-Guard QA Agent)
"""

import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

def create_deck():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    DARK_NAVY = RGBColor(15, 23, 42)      # #0f172a
    SLATE_NAVY = RGBColor(30, 41, 59)     # #1e293b
    PRIMARY_BLUE = RGBColor(37, 99, 235)   # #2563eb
    LIGHT_BG = RGBColor(248, 250, 252)    # #f8fafc
    CARD_BG = RGBColor(255, 255, 255)
    BORDER_COLOR = RGBColor(226, 232, 240) # #e2e8f0
    TEXT_DARK = RGBColor(15, 23, 42)
    TEXT_MUTED = RGBColor(100, 116, 139)   # #64748b
    ACCENT_GREEN = RGBColor(16, 185, 129)  # #10b981
    ACCENT_RED = RGBColor(239, 68, 68)     # #ef4444
    ACCENT_GOLD = RGBColor(245, 158, 11)   # #f59e0b
    WHITE = RGBColor(255, 255, 255)

    blank_layout = prs.slide_layouts[6]

    def set_bg(slide, color):
        bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
        bg.fill.solid()
        bg.fill.fore_color.rgb = color
        bg.line.fill.background()
        return bg

    def add_header(slide, title, category="2026 경남 AI·SW 경진대회 [일반부 / 03. 제조·피지컬 AI & 업무혁신]"):
        tb = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(11.7), Inches(0.4))
        p0 = tb.text_frame.paragraphs[0]
        p0.text = category
        p0.font.size = Pt(11)
        p0.font.bold = True
        p0.font.color.rgb = PRIMARY_BLUE

        tb2 = slide.shapes.add_textbox(Inches(0.8), Inches(0.75), Inches(11.7), Inches(0.6))
        p1 = tb2.text_frame.paragraphs[0]
        p1.text = title
        p1.font.size = Pt(22)
        p1.font.bold = True
        p1.font.color.rgb = TEXT_DARK

    def add_card(slide, left, top, width, height, bg_color=CARD_BG, border_color=BORDER_COLOR):
        card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
        card.fill.solid()
        card.fill.fore_color.rgb = bg_color
        if border_color:
            card.line.color.rgb = border_color
            card.line.width = Pt(1.5)
        else:
            card.line.fill.background()
        return card

    # ==================== SLIDE 1: COVER ====================
    s1 = prs.slides.add_slide(blank_layout)
    set_bg(s1, DARK_NAVY)

    line = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(1.2), Inches(1.8), Inches(1.8), Inches(0.08))
    line.fill.solid()
    line.fill.fore_color.rgb = PRIMARY_BLUE
    line.line.fill.background()

    tb = s1.shapes.add_textbox(Inches(1.2), Inches(2.1), Inches(11.0), Inches(4.5))
    tf = tb.text_frame
    tf.word_wrap = True

    p = tf.paragraphs[0]
    p.text = "2026 경남 AI·SW 경진대회 [03. 제조·피지컬 AI / 업무혁신]"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = RGBColor(148, 163, 184)
    p.space_after = Pt(14)

    p2 = tf.add_paragraph()
    p2.text = "칼퇴보증 : 성적서 분석 에이전트"
    p2.font.size = Pt(36)
    p2.font.bold = True
    p2.font.color.rgb = WHITE
    p2.space_after = Pt(8)

    p3 = tf.add_paragraph()
    p3.text = "COA-Guard QA Agent : 글로벌 가전 완제품 출하 성적서 다국어 자동 판독 & 표준 NCR 자율 발행"
    p3.font.size = Pt(17)
    p3.font.color.rgb = RGBColor(203, 213, 225)
    p3.space_after = Pt(32)

    p4 = tf.add_paragraph()
    p4.text = "팀명: 칼퇴보증  |  팀장/발표자: 전준보  |  개발완료: 2026. 10. 06"
    p4.font.size = Pt(14)
    p4.font.bold = True
    p4.font.color.rgb = PRIMARY_BLUE

    # ==================== SLIDE 2: PROBLEM ====================
    s2 = prs.slides.add_slide(blank_layout)
    set_bg(s2, LIGHT_BG)
    add_header(s2, "1. 문제 정의 : 경남 수출 가전 제조업의 실제 병목 (As-Is)")

    problems = [
        ("⏱️ 시간 병목 (Time Drain)", "건당 25분 수기 대조", 
         "• 해외 협력사 비정형 PDF/스캔본 성적서\n• 도면집과 일일이 육안 수기 대조 수행\n• 월 100시간 이상 단순 반복 행정 낭비"),
        ("⚠️ 휴먼 에러 (Human Error)", "오판율 3.2%의 치명적 위험", 
         "• 미세 치수 오차(±0.3mm) 판독 착오 위험\n• 단방향 규격 편차 왜곡 및 오판정 발생\n• 부적합품 라인 투입 시 수억 원대 리콜"),
        ("📄 행정 지연 (Delayed Action)", "표준 공문 작성 1~2일 소요", 
         "• 불합격 발생 시 8D/NCR 수작업 작성\n• 다국어(한/영/중) 커뮤니케이션 단절\n• 원인 분석 및 시정 조치 회신 지연")
    ]

    for idx, (title, sub, desc) in enumerate(problems):
        left = Inches(0.8 + idx * 4.0)
        add_card(s2, left, Inches(1.6), Inches(3.7), Inches(5.0))
        tb = s2.shapes.add_textbox(left + Inches(0.3), Inches(1.9), Inches(3.1), Inches(4.4))
        tf = tb.text_frame
        tf.word_wrap = True
        
        p = tf.paragraphs[0]
        p.text = title
        p.font.size = Pt(18)
        p.font.bold = True
        p.font.color.rgb = TEXT_DARK
        p.space_after = Pt(8)
        
        p_sub = tf.add_paragraph()
        p_sub.text = sub
        p_sub.font.size = Pt(14)
        p_sub.font.bold = True
        p_sub.font.color.rgb = ACCENT_RED if idx == 1 else PRIMARY_BLUE
        p_sub.space_after = Pt(14)
        
        p_desc = tf.add_paragraph()
        p_desc.text = desc
        p_desc.font.size = Pt(13)
        p_desc.font.color.rgb = TEXT_MUTED

    # ==================== SLIDE 3: SOLUTION ====================
    s3 = prs.slides.add_slide(blank_layout)
    set_bg(s3, LIGHT_BG)
    add_header(s3, "2. 해결 방안 : 자율 실행형 AI Agent (To-Be)")

    add_card(s3, Inches(0.8), Inches(1.6), Inches(5.6), Inches(5.0))
    tb = s3.shapes.add_textbox(Inches(1.1), Inches(1.9), Inches(5.0), Inches(4.4))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "❌ 기존 방식 & 단순 챗봇 (수동적 질의응답)"
    p.font.size = Pt(18)
    p.font.bold = True
    p.font.color.rgb = ACCENT_RED
    p.space_after = Pt(16)
    p2 = tf.add_paragraph()
    p2.text = "• 챗봇에 일일이 텍스트 복사-붙여넣기 질문\n• \"이 치수 맞아?\" 말로만 대답하고 끝남\n• 사내 도면 DB와 실시간 수학적 정합성 검증 부재\n• 결과 보고서 및 협력사 공문은 여전히 사람이 작성\n• 결론: 실무 공정 자동화가 아닌 단순 텍스트 도구에 불과"
    p2.font.size = Pt(13)
    p2.font.color.rgb = TEXT_MUTED

    add_card(s3, Inches(6.8), Inches(1.6), Inches(5.7), Inches(5.0), bg_color=CARD_BG, border_color=PRIMARY_BLUE)
    tb = s3.shapes.add_textbox(Inches(7.1), Inches(1.9), Inches(5.1), Inches(4.4))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "✅ 칼퇴보증 QA Agent (엔드투엔드 자율 완결)"
    p.font.size = Pt(18)
    p.font.bold = True
    p.font.color.rgb = PRIMARY_BLUE
    p.space_after = Pt(16)
    p2 = tf.add_paragraph()
    p2.text = "• 원클릭 PDF 업로드 즉시 1.2초 내 전수 감사 완결\n• 다국어(한/영/중) 지능형 파서 & 3단 무중단 폴백 엔진\n• 사내 도면 한계공차(LSL/USL) 및 Cpk 수학적 정밀 추론\n• 합격 시 [입고 승인서], 불합격 시 [표준 NCR/8D] 4-포맷 자율 발행\n• 협력업체 마스터 실적 및 품질 등급 실시간 자동 동기화"
    p2.font.size = Pt(13)
    p2.font.color.rgb = TEXT_DARK

    # ==================== SLIDE 4: ARCHITECTURE (6 ELEMENTS) ====================
    s4 = prs.slides.add_slide(blank_layout)
    set_bg(s4, LIGHT_BG)
    add_header(s4, "3. 시스템 아키텍처 : 경진대회 공인 Agent 6요소 100% 충족")

    elements = [
        ("🎯 1. Goal (목표 이해)", "출하성적서 규격 일치율 100% 무결점 감사 및 자율 행정 조치 완결"),
        ("📋 2. Planning (작업 계획)", "파싱 ➔ 도면 DB 공차 매핑 ➔ 한계선 추론 ➔ 행정 공문 빌드 4단계 자율 수행"),
        ("🧠 3. Reasoning (상황 추론)", "도면 상하한(LSL/USL) 대조, 단방향 공차 자동 보정, Cpk 연산, ISO 2859-1 판정"),
        ("🛠️ 4. Tool Use (도구 연동)", "PyMuPDF 파서, 사내 QC DB, 협력사 관리 DB, CJK 4-포맷 문서 생성기"),
        ("💾 5. Memory / State (기억)", "st.session_state 세션 기억, audit_history 영구 저장, vendors.json 실적 동기화"),
        ("🔄 6. Feedback (자기 보정)", "공차 초과 시 출하보류(Lock) & 8D 대책서 전이 / API 실패 시 100% 로컬 폴백")
    ]

    for idx, (title, desc) in enumerate(elements):
        row = idx // 2
        col = idx % 2
        left = Inches(0.8 + col * 6.0)
        top = Inches(1.6 + row * 1.7)
        add_card(s4, left, top, Inches(5.7), Inches(1.5))
        
        tb = s4.shapes.add_textbox(left + Inches(0.2), top + Inches(0.15), Inches(5.3), Inches(1.2))
        tf = tb.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = title
        p.font.size = Pt(15)
        p.font.bold = True
        p.font.color.rgb = PRIMARY_BLUE
        p.space_after = Pt(4)
        
        p2 = tf.add_paragraph()
        p2.text = desc
        p2.font.size = Pt(12)
        p2.font.color.rgb = TEXT_DARK

    # ==================== SLIDE 5: FEATURE 1 (PARSER) ====================
    s5 = prs.slides.add_slide(blank_layout)
    set_bg(s5, LIGHT_BG)
    add_header(s5, "4. 핵심 기능 ① : 다국어 지능형 파서 & 3단 무중단 폴백 (Split-View)")

    add_card(s5, Inches(0.8), Inches(1.6), Inches(5.6), Inches(5.0))
    tb = s5.shapes.add_textbox(Inches(1.1), Inches(1.9), Inches(5.0), Inches(4.4))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "🌐 한/영/중 3개국어 자동 인식 파서"
    p.font.size = Pt(18)
    p.font.bold = True
    p.font.color.rgb = PRIMARY_BLUE
    p.space_after = Pt(14)
    p2 = tf.add_paragraph()
    p2.text = "• 중국 저장성 협력사(余姚市菲尔浦) 한자 성적서 완벽 지원\n• 영문 수출용 성적서 & 국내 협력사 국문 성적서 자동 식별\n• ISO 2859-1 로트 크기, 샘플링 수량, 결함수(Ac/Re) 자동 추출\n• 검사원이 원본 PDF와 추출값을 1초 만에 확인하는 Split-View"
    p2.font.size = Pt(13)
    p2.font.color.rgb = TEXT_DARK

    add_card(s5, Inches(6.8), Inches(1.6), Inches(5.7), Inches(5.0))
    tb = s5.shapes.add_textbox(Inches(7.1), Inches(1.9), Inches(5.1), Inches(4.4))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "🛡️ 3단 무중단 하이브리드 폴백 엔진"
    p.font.size = Pt(18)
    p.font.bold = True
    p.font.color.rgb = ACCENT_GREEN
    p.space_after = Pt(14)
    p2 = tf.add_paragraph()
    p2.text = "• 1단계: PyMuPDF 초고속 벡터 텍스트 스트림 파싱 (0.05초)\n• 2단계: pypdf 정규식 기반 텍스트 추출 (보조 폴백)\n• 3단계: 로컬 룰베이스 엔진 (인터넷 차단 시에도 100% 작동)\n• 외부 LLM API 장애나 오프라인 사내 폐쇄망에서도 무중단 가동 보장"
    p2.font.size = Pt(13)
    p2.font.color.rgb = TEXT_DARK

    # ==================== SLIDE 6: FEATURE 2 (EVALUATOR) ====================
    s6 = prs.slides.add_slide(blank_layout)
    set_bg(s6, LIGHT_BG)
    add_header(s6, "5. 핵심 기능 ② : 제조 품질 공학 공차 추론 엔진 (LSL/USL & Cpk)")

    add_card(s6, Inches(0.8), Inches(1.6), Inches(5.6), Inches(5.0))
    tb = s6.shapes.add_textbox(Inches(1.1), Inches(1.9), Inches(5.0), Inches(4.4))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "📐 단방향 공차 자동 보정 & 편차(Delta) 정밀 추론"
    p.font.size = Pt(18)
    p.font.bold = True
    p.font.color.rgb = PRIMARY_BLUE
    p.space_after = Pt(14)
    p2 = tf.add_paragraph()
    p2.text = "• 양방향 규격: 기준치(Nominal) 중심 상하한 편차 정밀 계산\n• 단방향 규격 자동 처리: 전원코드 인장강도(60N 이상) 등\n• 단방향 공차에서 Delta가 0으로 왜곡되는 오류를 원천 해결\n• 허용 한계선의 90% 이상 근접 시 WARNING 알림 자동 발동"
    p2.font.size = Pt(13)
    p2.font.color.rgb = TEXT_DARK

    add_card(s6, Inches(6.8), Inches(1.6), Inches(5.7), Inches(5.0))
    tb = s6.shapes.add_textbox(Inches(7.1), Inches(1.9), Inches(5.1), Inches(4.4))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "📊 Plotly 동적 시각화 & 공정능력지수(Cpk)"
    p.font.size = Pt(18)
    p.font.bold = True
    p.font.color.rgb = PRIMARY_BLUE
    p.space_after = Pt(14)
    p2 = tf.add_paragraph()
    p2.text = "• 정규분포 곡선 위에 LSL, Nominal, USL 한계선 투영\n• 성적서 실측치를 다이아몬드 마커로 실시간 위치 매핑\n• Cpk(공정능력지수) 산출을 통한 잠재 품질 산포 분석\n• 복잡한 수치표 대신 직관적인 제조 공학 그래프 제공"
    p2.font.size = Pt(13)
    p2.font.color.rgb = TEXT_DARK

    # ==================== SLIDE 7: FEATURE 3 (REPORTING & VENDOR) ====================
    s7 = prs.slides.add_slide(blank_layout)
    set_bg(s7, LIGHT_BG)
    add_header(s7, "6. 핵심 기능 ③ : 4-포맷 자율 리포팅 & 협력업체 마스터 관제소")

    add_card(s7, Inches(0.8), Inches(1.6), Inches(5.6), Inches(5.0))
    tb = s7.shapes.add_textbox(Inches(1.1), Inches(1.9), Inches(5.0), Inches(4.4))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "📄 한글 CJK 벡터 폰트 임베딩 4-포맷 공문 자율 빌드"
    p.font.size = Pt(17)
    p.font.bold = True
    p.font.color.rgb = PRIMARY_BLUE
    p.space_after = Pt(14)
    p2 = tf.add_paragraph()
    p2.text = "• 합격 시: [출하검사 합격 인증 및 입고 승인서] 발행\n• 불합격 시: [표준 부적합 통보서 (NCR/8D)] 자율 생성\n• PyMuPDF CJK 글꼴 임베딩으로 PDF 한글 깨짐 원천 방지\n• Excel(.xlsx), PDF(.pdf), HTML(.html), Markdown(.md) 4대 포맷 즉시 다운로드"
    p2.font.size = Pt(13)
    p2.font.color.rgb = TEXT_DARK

    add_card(s7, Inches(6.8), Inches(1.6), Inches(5.7), Inches(5.0))
    tb = s7.shapes.add_textbox(Inches(7.1), Inches(1.9), Inches(5.1), Inches(4.4))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "🏭 협력업체 마스터 관제소 (Vendor Master)"
    p.font.size = Pt(17)
    p.font.bold = True
    p.font.color.rgb = ACCENT_GOLD
    p.space_after = Pt(14)
    p2 = tf.add_paragraph()
    p2.text = "• 신규 협력사 등록(Onboarding): 상호, 국가, 담당자 영구 DB 저장\n• 품질 등급(A/B/C) 및 거래 상태(정상/중점관리/보류) 실시간 변경\n• 성적서 판정 시 협력사별 누적 검사 건수 및 합격률 자동 갱신\n• 단발성 검사를 넘어 지속 가능한 공급망 품질 관리 실현"
    p2.font.size = Pt(13)
    p2.font.color.rgb = TEXT_DARK

    # ==================== SLIDE 8: ROI ====================
    s8 = prs.slides.add_slide(blank_layout)
    set_bg(s8, LIGHT_BG)
    add_header(s8, "7. 정량적 성과 (ROI) : 도입 전후 비교 (Before vs After)")

    kpis = [
        ("성적서 검토 시간", "25분 ➔ 1.2초", "99.8% 단축", ACCENT_GREEN),
        ("공차 판정 오류율", "3.2% ➔ 0.0%", "Zero Human Error", PRIMARY_BLUE),
        ("부적합 공문 작성", "1~2일 ➔ 즉시 완성", "원클릭 10초 완결", PRIMARY_BLUE),
        ("연간 비용 절감액", "인건비 + 결함 방지", "총 1.84억원 절감", ACCENT_GOLD)
    ]

    for idx, (title, change, highlight, color) in enumerate(kpis):
        left = Inches(0.8 + idx * 3.0)
        add_card(s8, left, Inches(1.6), Inches(2.7), Inches(2.3))
        tb = s8.shapes.add_textbox(left + Inches(0.15), Inches(1.8), Inches(2.4), Inches(1.9))
        tf = tb.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = title
        p.font.size = Pt(13)
        p.font.color.rgb = TEXT_MUTED
        p.space_after = Pt(4)
        p2 = tf.add_paragraph()
        p2.text = change
        p2.font.size = Pt(15)
        p2.font.bold = True
        p2.font.color.rgb = TEXT_DARK
        p2.space_after = Pt(4)
        p3 = tf.add_paragraph()
        p3.text = highlight
        p3.font.size = Pt(14)
        p3.font.bold = True
        p3.font.color.rgb = color

    # Bottom summary box
    add_card(s8, Inches(0.8), Inches(4.2), Inches(11.7), Inches(2.5), bg_color=CARD_BG)
    tb = s8.shapes.add_textbox(Inches(1.1), Inches(4.4), Inches(11.1), Inches(2.1))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "💰 경남 중견 가전 제조업체(연간 출하 성적서 2,400건 기준) 경제적 효과 산출 근거"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = TEXT_DARK
    p.space_after = Pt(8)
    p2 = tf.add_paragraph()
    p2.text = "1. 연간 절감 인건비: 연간 1,000시간 품질 검사 행정 공수 절감 = 약 5,400만 원\n2. 결함 유출 방지 효과: 연 2~3회 조립 라인 결함 유입 및 사후 리콜 조기 차단 = 약 1억 3,000만 원\n3. 총 연간 경제적 효과: 연간 1억 8,400만 원 순 절감 달성 (초기 투자비 대비 ROI 회수 기간 1개월 이내)"
    p2.font.size = Pt(13)
    p2.font.color.rgb = TEXT_MUTED

    # ==================== SLIDE 9: VERIFICATION & FEEDBACK ====================
    s9 = prs.slides.add_slide(blank_layout)
    set_bg(s9, LIGHT_BG)
    add_header(s9, "8. 검증 증빙 : 대표 Test Case 5종 100% 통과 & 실사용자 검증 (+1점 가점)")

    add_card(s9, Inches(0.8), Inches(1.6), Inches(6.0), Inches(5.0))
    tb = s9.shapes.add_textbox(Inches(1.0), Inches(1.8), Inches(5.6), Inches(4.6))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "🧪 5대 대표 테스트케이스 100% 통과 (Pass)"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = PRIMARY_BLUE
    p.space_after = Pt(10)
    p2 = tf.add_paragraph()
    p2.text = "• TC-01 (정상 규격): BL-E01 초고속 블렌더 ➔ PASS, 승인서 발급 완료\n• TC-02 (공차 초과): BL-D01 진공 블렌더 베이스 외경 +0.4mm 이탈 ➔ FAIL, 즉시 NCR 발행\n• TC-03 (단방향 규격): TM-HB1 인장강도 60N 이상 ➔ 왜곡 없는 Delta(+3.5N) 산출\n• TC-04 (중국 협력사): CJ-B03 한자 표기 실물 PDF ➔ [ZH] 자동 감지 및 결함수 파싱\n• TC-05 (오프라인 폴백): 네트워크 단절 모의 ➔ 로컬 룰베이스 100% 무중단 완주"
    p2.font.size = Pt(12)
    p2.font.color.rgb = TEXT_DARK

    add_card(s9, Inches(7.1), Inches(1.6), Inches(5.4), Inches(5.0))
    tb = s9.shapes.add_textbox(Inches(7.3), Inches(1.8), Inches(5.0), Inches(4.6))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "👥 현장 실사용자 3명 현장 검증 확보 (+1점)"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = ACCENT_GREEN
    p.space_after = Pt(10)
    p2 = tf.add_paragraph()
    p2.text = "1. 김진석 파트장 ((주)크리스탈 일렉트릭 IQC 수입검사):\n   \"1초 만에 인장강도 편차를 짚고 즉시 승인서까지 발행되는 것에 감탄. 현업에 바로 도입하고 싶음\"\n\n2. 박성민 선임연구원 (경남 가전제조 혁신지원센터):\n   \"0.4mm 초과를 놓치지 않고 공급사 발송용 8D NCR을 뽑아줌. 제조 행정 워크플로우를 완벽히 이해한 솔루션\"\n\n3. 장웨이 팀장 (HOTOEM 선전 공장 품질보증부):\n   \"중국어 표기 성적서를 번역기 없이 자동 감지. 글로벌 공급망과 국내 본사 간 언어 장벽 완벽 해소\""
    p2.font.size = Pt(11)
    p2.font.color.rgb = TEXT_DARK

    # ==================== SLIDE 10: CONCLUSION & ROADMAP ====================
    s10 = prs.slides.add_slide(blank_layout)
    set_bg(s10, DARK_NAVY)

    tb = s10.shapes.add_textbox(Inches(1.2), Inches(1.2), Inches(11.0), Inches(5.5))
    tf = tb.text_frame
    tf.word_wrap = True

    p = tf.paragraphs[0]
    p.text = "9. 보안 안전성 & 향후 발전 계획 (M.AX 로드맵)"
    p.font.size = Pt(24)
    p.font.bold = True
    p.font.color.rgb = WHITE
    p.space_after = Pt(20)

    p2 = tf.add_paragraph()
    p2.text = "🔒 철저한 보안성 & 환경 이식성\n• API Key 소스 하드코딩 0건 (.env 보안 격리 완비)\n• 심사위원 원클릭 자동 설치/실행 런처(COA_프로그램_실행.bat) 제공\n• 외부 네트워크 단절 시에도 100% 로컬 오프라인 가동 보장"
    p2.font.size = Pt(14)
    p2.font.color.rgb = RGBColor(203, 213, 225)
    p2.space_after = Pt(18)

    p3 = tf.add_paragraph()
    p3.text = "🚀 경남 제조 산업(M.AX) 수평 전개 로드맵\n• 1단계: 가전 완제품 성적서 ➔ 모터, PCB, 사출 단품 원자재 성적서 확장\n• 2단계: 사내 SAP / 더존 ERP 및 MES 생산관리 시스템 REST Webhook 직결\n• 3단계: 창원·사천·거제 조선·방산·항공우주 초정밀 부품 성적서 도메인 수평 전개"
    p3.font.size = Pt(14)
    p3.font.color.rgb = RGBColor(203, 213, 225)
    p3.space_after = Pt(28)

    p4 = tf.add_paragraph()
    p4.text = "\"말하는 AI에서, 일하는 제조 AX로! 경남 제조업의 든든한 품질 지킴이가 되겠습니다.\""
    p4.font.size = Pt(17)
    p4.font.bold = True
    p4.font.color.rgb = PRIMARY_BLUE
    p4.space_after = Pt(10)

    p5 = tf.add_paragraph()
    p5.text = "경청해 주셔서 감사합니다.  |  팀명: 칼퇴보증 (질의응답 Q&A)"
    p5.font.size = Pt(14)
    p5.font.color.rgb = RGBColor(148, 163, 184)

    output_path = r"z:\junbo\20.대외활동\2026_AX공모전\04.발표 및최종 제출\발표자료_PPT\COA-Guard_발표자료_10장.pptx"
    prs.save(output_path)
    print(f"Presentation generated successfully: {output_path}")

if __name__ == "__main__":
    create_deck()
