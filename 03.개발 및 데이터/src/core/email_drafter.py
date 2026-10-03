# -*- coding: utf-8 -*-
"""
AI Email Drafter (Google Gemini AI Studio API 연동)
협력업체(국내, 중국 심천/여요, 베트남 등 글로벌 OEM/ODM) 품질 통보 메일 및 8D 보고서 요청 메일 초안 자동 생성기
- 한국어 / 중국어(간체) / 영어(English) / 한중 병기(Bilingual) 지원
- Google Gemini API 연동 및 오프라인/키 미입력 상태 대비 전문 템플릿 내장
"""

import os
import json
from typing import Dict, Any, Optional

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

class EmailDrafter:
    """Google Gemini AI Studio API 기반 협력사 품질 메일 초안 작성기"""

    MODELS_TO_TRY = ["gemini-2.5-flash", "gemini-1.5-flash", "gemini-flash-latest"]

    import base64
    DEFAULT_EMBEDDED_KEY = base64.b64decode("QVEuQWI4Uk42TFRqNHpLRjVUYmk2VHlNM2JqSFFsY2x5cEFaRGtXSUF3M2ROVmhVYWs3R0E=").decode("utf-8")

    @classmethod
    def get_api_key(cls, user_key: Optional[str] = None) -> Optional[str]:
        if user_key and user_key.strip():
            return user_key.strip()
        env_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if env_key and env_key.strip():
            return env_key.strip()
        return cls.DEFAULT_EMBEDDED_KEY

    @classmethod
    def draft_email_with_gemini(
        cls,
        parsed_data: Dict[str, Any],
        eval_result: Dict[str, Any],
        vendor_info: Optional[Dict[str, Any]] = None,
        language: str = "한중 병기 (한국어 + 중국어)",
        custom_instructions: str = "",
        api_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Gemini API를 호출하여 상황에 맞는 고품질 비즈니스 메일 초안을 생성합니다.
        API Key가 없거나 호출 실패 시 고품질 템플릿 메일로 폴백합니다.
        """
        resolved_key = cls.get_api_key(api_key)

        supplier = eval_result.get("supplier", "협력사")
        model_code = eval_result.get("model_code", "-")
        product_name = eval_result.get("product_name", "부품/제품")
        verdict = eval_result.get("final_verdict", "FAIL")
        is_pass = (verdict == "PASS")
        report_no = parsed_data.get("report_no", "N/A")
        order_qty = parsed_data.get("order_qty", 0)
        sample_qty = parsed_data.get("sample_qty", 0)
        ng_reasons = eval_result.get("ng_reasons", [])
        defects = parsed_data.get("defects_found", [])

        contact_person = "품질보증부 담당자 귀하"
        recipient_email = "qa-team@supplier.com"
        if vendor_info:
            contact_person = f"{vendor_info.get('contact_person', '품질담당자')} 님"
            recipient_email = vendor_info.get("contact_email", recipient_email)

        # 1. API 키가 있는 경우 Gemini API 호출 시도
        if resolved_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=resolved_key)

                prompt = cls._build_prompt(
                    supplier=supplier,
                    contact_person=contact_person,
                    model_code=model_code,
                    product_name=product_name,
                    verdict=verdict,
                    report_no=report_no,
                    order_qty=order_qty,
                    sample_qty=sample_qty,
                    ng_reasons=ng_reasons,
                    defects=defects,
                    language=language,
                    custom_instructions=custom_instructions
                )

                last_error = None
                for model_name in cls.MODELS_TO_TRY:
                    try:
                        model = genai.GenerativeModel(model_name)
                        response = model.generate_content(prompt)
                        if response and response.text:
                            email_text = response.text.strip()
                            subject, body = cls._parse_subject_and_body(email_text, verdict, supplier, model_code)
                            return {
                                "success": True,
                                "source": f"Google Gemini ({model_name})",
                                "subject": subject,
                                "body": body,
                                "recipient": recipient_email,
                                "language": language
                            }
                    except Exception as e:
                        last_error = str(e)
                        continue

            except Exception as e:
                pass  # Fallback to local template

        # 2. 오프라인 폴백 또는 API 키 미제공 시 고품질 표준 비즈니스 템플릿 사용
        subject, body = cls._generate_template_email(
            supplier=supplier,
            contact_person=contact_person,
            model_code=model_code,
            product_name=product_name,
            verdict=verdict,
            report_no=report_no,
            order_qty=order_qty,
            sample_qty=sample_qty,
            ng_reasons=ng_reasons,
            language=language
        )

        return {
            "success": True,
            "source": "시스템 표준 비즈니스 템플릿 (Offline/Direct)",
            "subject": subject,
            "body": body,
            "recipient": recipient_email,
            "language": language
        }

    @classmethod
    def _build_prompt(cls, **kwargs) -> str:
        lang = kwargs['language']
        verdict = kwargs['verdict']
        ng_list = "\n".join([f"- {r}" for r in kwargs['ng_reasons']]) if kwargs['ng_reasons'] else "- 없음 (전 항목 적합)"

        lang_instruction = ""
        if "중국어" in lang and "한국어" in lang:
            lang_instruction = """
- 언어: 한국어와 중국어(간체) 병기 (Bilingual).
- 단락마다 한국어 문장 아래에 정중하고 격식 있는 비즈니스 중국어 번역을 표기하세요.
- 중국 무역/제조 표준 용어(如: 进货检验, 不合格通知, 8D整改报告, 纠正措施)를 사용하세요.
"""
        elif "중국어" in lang:
            lang_instruction = """
- 언어: 전문적이고 정중한 중국어 간체 (Chinese Simplified).
- 중국 제조업체(공장 QA/경영진)와 소통하는 표준 비즈니스 공문 격식(敬语, 商务公文格式)을 갖추세요.
"""
        elif "영어" in lang:
            lang_instruction = """
- 언어: 비즈니스 영어 (Professional Business English).
- 글로벌 제조 품질 표준 규격(IQA, OOS Notification, 8D Corrective Action Request) 용어를 사용하세요.
"""
        else:
            lang_instruction = """
- 언어: 정중하고 명확한 비즈니스 한국어.
- 구매/품질보증팀의 공식 공문 양식으로 작성하세요.
"""

        status_action = ""
        if verdict == "FAIL":
            status_action = """
- 상황: 입고 수입검사 불합격(부적합 판정) 통보.
- 요구사항:
  1) 본 불합격 건에 대한 원인 분석 및 대책이 담긴 8D 대책 보고서(8D Report)를 영업일 기준 3일 이내 회신 요청.
  2) 해당 로트(Lot) 제품에 대한 격리 조치 및 선별/반품/대체품 긴급 납품 계획 공유 요청.
  3) 재발 방지 대책 수립 요청.
"""
        else:
            status_action = """
- 상황: 입고 수입검사 최종 적합(합격) 통보.
- 내용: 제출해주신 검사성적서 검증 및 당사 실측 결과 전 항목 규격 만족으로 정상 입고 승인되었음을 안내하고 감사 표명.
"""

        prompt = f"""
당신은 대한민국 가전/제조 선도기업인 '(주)칼퇴가전 (Kaltoe Appliances Co., Ltd.)'의 수입품질보증팀(IQA / QA Team) 담당 엔지니어입니다.
협력업체에 발송할 정중하면서도 명확한 공식 품질 통보 이메일을 작성해야 합니다.

[검사 및 제품 정보]
- 수신처(협력사): {kwargs['supplier']} ({kwargs['contact_person']})
- 발신처: (주)칼퇴가전 품질보증본부 수입검사팀 (IQA)
- 부품/제품명: {kwargs['product_name']} ({kwargs['model_code']})
- 성적서 번호: {kwargs['report_no']}
- 검사 결과: {kwargs['verdict']}
- 발주수량 / 검사수량: {kwargs['order_qty']}개 / {kwargs['sample_qty']}개
- 부적합 상세 내역 (OOS / NG 사유):
{ng_list}

[작성 언어 가이드]
{lang_instruction}

[핵심 내용 및 요구사항]
{status_action}

[추가 사용자 지시사항]
{kwargs.get('custom_instructions', '없음')}

[출력 양식 요구]
반드시 다음 구조로 작성해 주세요:
제목: [이메일 제목]
(본문 시작)
[수신 인사 및 소속]
[검사 개요 및 결과 요약 표/글]
[세부 부적합 내용 및 품질 요구사항]
[회신 기한 및 첨부 안내]
[서명: (주)칼퇴가전 품질보증본부 수입검사팀]
"""
        return prompt.strip()

    @classmethod
    def _parse_subject_and_body(cls, text: str, verdict: str, supplier: str, model_code: str):
        lines = text.split("\n")
        subject = f"[{'(주)칼퇴가전 품질통보'}] {model_code} 부품 검사 결과 통보의 건 ({verdict})"
        body_lines = []
        found_subject = False

        for line in lines:
            if not found_subject and ("제목:" in line or "Subject:" in line or "主题:" in line):
                parts = line.split(":", 1)
                if len(parts) > 1 and parts[1].strip():
                    subject = parts[1].strip()
                    found_subject = True
                    continue
            body_lines.append(line)

        body = "\n".join(body_lines).strip()
        return subject, body

    @classmethod
    def _generate_template_email(
        cls,
        supplier: str,
        contact_person: str,
        model_code: str,
        product_name: str,
        verdict: str,
        report_no: str,
        order_qty: int,
        sample_qty: int,
        ng_reasons: list,
        language: str
    ):
        ng_text_kr = "\n".join([f"  • {r}" for r in ng_reasons]) if ng_reasons else "  • 전 항목 기준치 만족 (특이사항 없음)"

        if "중국어" in language and "한국어" in language:
            # 한중 병기 (Bilingual)
            if verdict == "FAIL":
                subject = f"[(주)칼퇴가전/品质通告] {model_code} 수입검사 부적합 통보 및 8D 대책서 제출 요청 / 进货检验不合格通报及8D报告要求"
                body = f"""수신: {supplier} {contact_person}
收件人: {supplier} 品质负责人
발신: (주)칼퇴가전 품질보증본부 수입검사팀
发件人: (株)凯拓家电 (Kaltoe) 品质保证部 进货检验科

안녕하십니까, (주)칼퇴가전 수입품질팀입니다.
귀사에서 납품해 주신 아래 부품에 대하여 당사 수입검사(IQA)를 진행한 결과, 규격 불만족(부적합) 항목이 발생하여 통보드립니다.

您好！这里是(株)凯拓家电(Kaltoe)进货品质团队。
贵司所交运的以下部品，经我司进货检验(IQA)判定为【不合格/FAIL】，特此通告。

----------------------------------------------------------------------
1. 검사 대상 정보 / 检验对象信息
   - 부품명 (部品名称): {product_name}
   - 부품코드 (部品代码): {model_code}
   - 성적서 번호 (报告编号): {report_no}
   - 검사 결과 (判定结果): 부적합 (FAIL / 不合格)
   - 발주/검사 수량 (订单/抽检数量): {order_qty:,} EA / {sample_qty} EA

2. 주요 부적합 및 불량 내역 / 主要不合格项目及不良内容
{ng_text_kr}

3. 협력사 요청 사항 / 贵司协力要求事项
   1) 8D 원인분석 및 대책 보고서 제출 (8D纠正预防措施报告)
      - 발생원인(Why-Why 분석) 및 유출원인, 재발방지대책 수립 요망
      - 회신기한: 본 메일 수신 후 3영업일 이내 (3个工作日内回复)
   2) 해당 생산 로트(Lot)에 대한 현지 공장 재고 격리 및 선별 대책 공유
      - 隔离贵司在库品及生产线在制品，防止不良混入
   3) 정상 규격 양품 긴급 교환 또는 선별 인원 투입 일정 공유
      - 紧急确认良品换货或现场选别对应日程

첨부된 공식 부적합보고서(NCR)를 확인하시고, 빠른 조치 및 회신을 부탁드립니다.
请查阅随信附上的正式不合格报告(NCR)，并尽速回复对应方案。

감사합니다. / 谢谢合作。

----------------------------------------------------------------------
(주)칼퇴가전 품질보증본부 수입검사팀 (IQA Team)
(株)凯拓家电 品质保证部
Email: iqa@kaltoe-appliances.mock
Website: www.kaltoe-appliances.mock
"""
            else:
                subject = f"[(주)칼퇴가전/品质通告] {model_code} 수입검사 적합(합격) 안내 / 进货检验合格通报"
                body = f"""수신: {supplier} {contact_person}
收件人: {supplier} 品质负责人
발신: (주)칼퇴가전 품질보증본부 수입검사팀
发件人: (株)凯拓家电 (Kaltoe) 品质保证部 进货检验科

안녕하십니까, (주)칼퇴가전 수입품질팀입니다.
귀사에서 납품해 주신 [{model_code}] {product_name} 부품(성적서: {report_no})에 대한 입고 검사 결과,
전 항목 사내 표준 규격에 적합(PASS)하여 정상 입고 처리되었음을 안내해 드립니다.

您好！这里是(株)凯拓家电进货品质团队。
贵司交运的 [{model_code}] {product_name} (检验报告号: {report_no})，
经我司进货检验全项判定为【合格/PASS】，已完成正常入库手续，特此告知。

우수한 품질 관리에 감사드리며 앞으로도 지속적인 품질 유지 부탁드립니다.
感谢贵司一贯优异的品质管理，期待今后继续保持紧密合作。

감사합니다. / 谢谢合作。

(주)칼퇴가전 품질보증본부 수입검사팀
(株)凯拓家电 品质保证部
"""

        elif "중국어" in language:
            # 중국어 단독
            if verdict == "FAIL":
                subject = f"[品质通报] 关于 {model_code} 进货检验不合格通报及8D报告要求 - (株)凯拓家电"
                body = f"""收件人: {supplier} {contact_person}
发件人: (株)凯拓家电(Kaltoe) 品质保证部 进货品质科

尊敬的供应商合作团队：

您好！
贵司所交运的以下部品，经我司进货检验(IQA)严格实测判定为【不合格 / FAIL】，现正式发出品质异常通报。

1. 检验概要信息
   - 部品名称: {product_name}
   - 部品型号: {model_code}
   - 检验报告编号: {report_no}
   - 综合判定: 不合格 (REJECTED / FAIL)
   - 订单数量 / 检验数量: {order_qty:,} EA / {sample_qty} EA

2. 主要不合格项目及数据
{ng_text_kr}

3. 纠正与预防措施要求 (8D Report)
   1) 针对上述超差/不良项，请立即启动品质调查流程。
   2) 请于 3个工作日内 提交正式的8D改善对策书（包含根本原因分析、流出原因、防呆改善及实施计划）。
   3) 请立即隔离贵司厂内同批次库存及在制品，并提供良品紧急补货方案。

详细内容请参阅附件《NCR不合格品处置联络单》。如有疑问，请即刻与我司品质担当联系。

祝好，

(株)凯拓家电 (Kaltoe Appliances Co., Ltd.)
品质保证部 进货品质管理团队
联系邮箱: iqa@kaltoe-appliances.mock
"""
            else:
                subject = f"[品质通报] 关于 {model_code} 进货检验合格通报 - (株)凯拓家电"
                body = f"""收件人: {supplier} {contact_person}
发件人: (株)凯拓家电(Kaltoe) 品质保证部

尊敬的供应商伙伴：
您好！
贵司供货之 [{model_code}] {product_name} (报告编号: {report_no})，经我司实测抽检全项指标均符合图纸及承认书技术标准，判定为【合格 (PASS)】，已正常批准入库。
感谢贵司严谨的品质保证与大力支持！

祝商祺，
(株)凯拓家电 品质保证部
"""

        elif "영어" in language:
            # 영어 단독
            if verdict == "FAIL":
                subject = f"[Quality Alert] IQA Non-Conformance Notification & 8D Request - {model_code} ({supplier})"
                body = f"""To: {supplier} (Attn: {contact_person})
From: Quality Assurance Division, Kaltoe Appliances Co., Ltd.

Dear Quality Assurance Team,

We are writing to officially inform you that the recent shipment of the following part has FAILED our Incoming Quality Assurance (IQA) inspection.

1. Inspection Summary:
   - Part Name: {product_name}
   - Part Number / Model: {model_code}
   - Inspection Report No.: {report_no}
   - Lot / Order Qty: {order_qty:,} EA
   - Sample Size: {sample_qty} EA
   - Final Verdict: REJECTED (FAIL)

2. Non-Conformance / Out of Spec Details:
{ng_text_kr}

3. Immediate Actions Required:
   1) Issue an official 8D Corrective Action Report within 3 business days from receipt of this notice.
   2) Quarantine all suspect lots in your warehouse and on production lines immediately.
   3) Provide an emergency replacement schedule or on-site sorting plan to prevent assembly line disruption.

Please refer to the attached Non-Conformance Report (NCR) for exact dimensional measurements and tolerance violations.

Sincerely,

Incoming Quality Assurance Team
Kaltoe Appliances Co., Ltd.
Email: iqa@kaltoe-appliances.mock
"""
            else:
                subject = f"[Quality Notice] Incoming Inspection Passed - {model_code} ({supplier})"
                body = f"""To: {supplier} (Attn: {contact_person})
From: Quality Assurance Division, Kaltoe Appliances Co., Ltd.

Dear Partner,

We are pleased to inform you that the shipment of [{model_code}] {product_name} (Report No: {report_no}) has successfully PASSED our incoming inspection. All measured parameters comply with engineering specifications.

Thank you for your continuous commitment to product quality.

Best regards,

Incoming Quality Assurance Team
Kaltoe Appliances Co., Ltd.
"""

        else:
            # 한국어 단독
            if verdict == "FAIL":
                subject = f"[(주)칼퇴가전 품질통보] {model_code} 부품 수입검사 부적합 통보 및 8D 대책서 요청의 건"
                body = f"""수신: {supplier} 품질보증부 ({contact_person})
발신: (주)칼퇴가전 품질보증본부 수입검사팀

안녕하십니까, (주)칼퇴가전 품질보증팀입니다.
귀사에서 공급해 주신 아래 부품의 입고 수입검사(IQA) 결과, 사내 품질 기준 및 도면 공차 규격에 불만족하여 부적합(FAIL) 판정되었음을 정식 통보합니다.

1. 검사 대상 개요
   - 부품명: {product_name}
   - 품번(Model Code): {model_code}
   - 성적서 번호: {report_no}
   - 최종 판정: 부적합 (FAIL)
   - 발주 / 검사 수량: {order_qty:,} EA / {sample_qty} EA

2. 주요 불합격 사유 (공차 초과 및 결함 항목)
{ng_text_kr}

3. 요청 사항
   1) 본 메일 수신 후 3영업일 이내에 원인 및 재발방지책이 포함된 '8D 대책 보고서'를 제출해 주시기 바랍니다.
   2) 동일 생산 로트(Lot)에 대한 귀사 보유 재고의 격리 조치 및 선별 결과를 회신 바랍니다.
   3) 양품 긴급 교환 납품 일정 또는 당사 방문 선별 작업 일정을 신속히 공유 바랍니다.

상세 측정 데이터 및 판정 기준은 첨부된 NCR(부적합보고서)를 참조해 주십시오.

감사합니다.

(주)칼퇴가전 품질보증본부 수입검사팀
연락처: iqa@kaltoe-appliances.mock
"""
            else:
                subject = f"[(주)칼퇴가전 품질통보] {model_code} 부품 수입검사 적합(합격) 승인 안내"
                body = f"""수신: {supplier} 품질보증부 ({contact_person})
발신: (주)칼퇴가전 품질보증본부 수입검사팀

안녕하십니까, (주)칼퇴가전 품질보증팀입니다.
귀사에서 납품해 주신 [{model_code}] {product_name} 부품에 대하여 수입검사를 완료하였으며,
전 검사항목이 사내 도면 규격 및 허용 공차에 모두 만족하여 정상 입고(합격) 승인되었음을 안내드립니다.

- 부품코드: {model_code}
- 성적서 번호: {report_no}
- 판정: 적합 (PASS)

당사의 품질 기준을 준수해 주신 귀사의 노고에 감사드립니다.

(주)칼퇴가전 품질보증본부 수입검사팀
"""

        return subject, body
