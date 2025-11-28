# -*- coding: utf-8 -*-
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os
from datetime import datetime

# 한글 폰트 설정 (맥OS 기본 폰트 사용, Vercel에서는 Noto Sans 사용)
FONT_PATHS = [
    "/System/Library/Fonts/Supplemental/AppleGothic.ttf",  # macOS
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",  # Linux
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "fonts", "NotoSansKR-Regular.otf"),  # 프로젝트 내 폰트
]

DEFAULT_FONT = 'Helvetica'
for font_path in FONT_PATHS:
    if os.path.exists(font_path):
        try:
            pdfmetrics.registerFont(TTFont('KoreanFont', font_path))
            DEFAULT_FONT = 'KoreanFont'
            break
        except:
            continue

# 출력 디렉토리 (Vercel에서는 /tmp 사용)
OUTPUT_DIR = "/tmp" if os.environ.get("VERCEL") else "output"

# 회사 정보 (고정)
COMPANY_INFO = {
    "name": "(주)위즈더플래닝",
    "business_number": "668-81-00391",
    "phone": "1670-0704",
    "address": "서울시 금천구 디지털로 178 A동 2518호, 19호"
}

# 색상
PRIMARY_COLOR = colors.HexColor('#4a6cf7')
SECONDARY_COLOR = colors.HexColor('#6366f1')
TEXT_COLOR = colors.HexColor('#333333')
GRAY_COLOR = colors.HexColor('#666666')
LIGHT_GRAY = colors.HexColor('#f5f5f5')
BORDER_COLOR = colors.HexColor('#dddddd')


def get_styles():
    """스타일 정의"""
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name='KoreanTitle',
        fontName=DEFAULT_FONT,
        fontSize=28,
        alignment=1,
        spaceAfter=5,
        textColor=TEXT_COLOR,
        leading=34,
    ))

    styles.add(ParagraphStyle(
        name='KoreanSubtitle',
        fontName=DEFAULT_FONT,
        fontSize=12,
        alignment=1,
        spaceAfter=20,
        textColor=GRAY_COLOR,
    ))

    styles.add(ParagraphStyle(
        name='KoreanNormal',
        fontName=DEFAULT_FONT,
        fontSize=10,
        leading=16,
        textColor=TEXT_COLOR,
    ))

    styles.add(ParagraphStyle(
        name='KoreanHeading',
        fontName=DEFAULT_FONT,
        fontSize=13,
        spaceBefore=15,
        spaceAfter=10,
        textColor=PRIMARY_COLOR,
        leading=18,
    ))

    styles.add(ParagraphStyle(
        name='CompanyName',
        fontName=DEFAULT_FONT,
        fontSize=18,
        textColor=TEXT_COLOR,
        leading=22,
    ))

    styles.add(ParagraphStyle(
        name='CustomerName',
        fontName=DEFAULT_FONT,
        fontSize=16,
        textColor=TEXT_COLOR,
        leading=20,
    ))

    styles.add(ParagraphStyle(
        name='Greeting',
        fontName=DEFAULT_FONT,
        fontSize=11,
        leading=18,
        textColor=TEXT_COLOR,
        spaceBefore=10,
        spaceAfter=10,
    ))

    styles.add(ParagraphStyle(
        name='SmallText',
        fontName=DEFAULT_FONT,
        fontSize=9,
        leading=14,
        textColor=GRAY_COLOR,
    ))

    return styles


def generate_proposal(data):
    """제안서 PDF 생성"""
    return _generate_document(data, "proposal")


def generate_estimate(data):
    """견적서 PDF 생성"""
    return _generate_document(data, "estimate")


def _generate_document(data, doc_type):
    """공통 문서 생성 로직"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 파일명 생성
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    customer = data.get("customer", {})
    company = customer.get("company", "고객")
    company_safe = "".join(c for c in company if c.isalnum() or c in (' ', '_')).strip()
    doc_name = "제안서" if doc_type == "proposal" else "견적서"
    filename = f"{doc_name}_{company_safe}_{timestamp}.pdf"
    filepath = os.path.join(OUTPUT_DIR, filename)

    # PDF 생성
    doc = SimpleDocTemplate(
        filepath,
        pagesize=A4,
        rightMargin=20*mm,
        leftMargin=20*mm,
        topMargin=15*mm,
        bottomMargin=15*mm
    )

    styles = get_styles()
    elements = []

    # ===== 헤더 =====
    title = "제 안 서" if doc_type == "proposal" else "견 적 서"
    elements.append(Paragraph(title, styles['KoreanTitle']))
    elements.append(Paragraph(data.get("date", ""), styles['KoreanSubtitle']))

    # 구분선
    elements.append(HRFlowable(
        width="100%",
        thickness=2,
        color=PRIMARY_COLOR,
        spaceBefore=5,
        spaceAfter=20
    ))

    # ===== 수신자 정보 =====
    recipient_data = [
        [
            Paragraph("<b>수 신</b>", styles['SmallText']),
            Paragraph(f"<b>{customer.get('company', '-')}</b>", styles['CustomerName'])
        ],
        [
            "",
            Paragraph(f"{customer.get('name', '-')} 님 귀하", styles['KoreanNormal'])
        ]
    ]

    recipient_table = Table(recipient_data, colWidths=[25*mm, 145*mm])
    recipient_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), DEFAULT_FONT),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    elements.append(recipient_table)
    elements.append(Spacer(1, 10*mm))

    # ===== 인사말 =====
    greeting_text = f"""
    안녕하세요, <b>{COMPANY_INFO['name']}</b>입니다.<br/>
    귀사의 무궁한 발전을 기원하며, 아래와 같이 {'제안' if doc_type == 'proposal' else '견적'}드립니다.
    """
    elements.append(Paragraph(greeting_text, styles['Greeting']))
    elements.append(Spacer(1, 8*mm))

    # ===== 광고 내역 =====
    elements.append(Paragraph("■ 포커스미디어 광고 내역", styles['KoreanHeading']))

    apartments = data.get("apartments", [])

    # 각 아파트를 카드 형태로 표시
    for idx, apt in enumerate(apartments, 1):
        # 아파트명 헤더
        apt_header_data = [[
            Paragraph(f"<b>{idx}. {apt.get('apartment_name', '-')}</b>", styles['KoreanNormal'])
        ]]
        apt_header_table = Table(apt_header_data, colWidths=[170*mm])
        apt_header_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), DEFAULT_FONT),
            ('BACKGROUND', (0, 0), (-1, -1), PRIMARY_COLOR),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ]))
        elements.append(apt_header_table)

        # 아파트 상세 정보 (모니터 대수, 대당 단가, 월 견적)
        apt_detail_data = [[
            Paragraph("<b>모니터 대수</b>", styles['SmallText']),
            Paragraph("<b>대당 단가</b>", styles['SmallText']),
            Paragraph("<b>월 견적</b>", styles['SmallText'])
        ], [
            Paragraph(f"{apt.get('monitor_count', 0)}대", styles['KoreanNormal']),
            Paragraph(f"{apt.get('unit_price', 0):,}원", styles['KoreanNormal']),
            Paragraph(f"<b>{apt.get('monthly_total', 0):,}원</b>", styles['KoreanNormal'])
        ]]
        apt_detail_table = Table(apt_detail_data, colWidths=[56.67*mm, 56.67*mm, 56.66*mm])
        apt_detail_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), DEFAULT_FONT),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('BACKGROUND', (0, 0), (-1, 0), LIGHT_GRAY),
            ('BACKGROUND', (2, 1), (2, 1), colors.HexColor('#e8f0ff')),
            ('TEXTCOLOR', (2, 1), (2, 1), PRIMARY_COLOR),
            ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ]))
        elements.append(apt_detail_table)
        elements.append(Spacer(1, 3*mm))

    elements.append(Spacer(1, 2*mm))

    # ===== 금액 요약 =====
    total_monthly = data.get("total_monthly", 0)
    discount_rate = data.get("discount_rate", 0)
    discount_amount = data.get("discount_amount", 0)
    monthly_final = data.get("monthly_final", 0)
    months = data.get("months", 3)
    final_total = data.get("final_total", 0)

    summary_data = [
        ["총 월 견적", f'{total_monthly:,}원']
    ]

    if discount_rate > 0:
        summary_data.append([data.get("discount_label", "할인"), f'-{discount_amount:,}원'])

    summary_data.append(["월 최종 금액", f'{monthly_final:,}원'])
    summary_data.append([f"총 계약 금액 ({months}개월)", f'{final_total:,}원'])

    summary_table = Table(summary_data, colWidths=[100*mm, 70*mm])

    summary_styles = [
        ('FONTNAME', (0, 0), (-1, -1), DEFAULT_FONT),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('BACKGROUND', (0, 0), (-1, -1), LIGHT_GRAY),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        # 마지막 행 (총 계약 금액) 강조
        ('FONTSIZE', (-1, -1), (-1, -1), 13),
        ('TEXTCOLOR', (-1, -1), (-1, -1), PRIMARY_COLOR),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#e8f0ff')),
    ]

    # 할인 행이 있으면 빨간색으로 표시
    if discount_rate > 0:
        summary_styles.append(('TEXTCOLOR', (1, 1), (1, 1), colors.HexColor('#e53935')))

    summary_table.setStyle(TableStyle(summary_styles))
    elements.append(summary_table)

    # 부가세 안내
    elements.append(Spacer(1, 2*mm))
    elements.append(Paragraph("※ 부가세 별도", styles['SmallText']))
    elements.append(Spacer(1, 10*mm))

    # ===== 안내사항 =====
    elements.append(Paragraph("■ 안내사항", styles['KoreanHeading']))

    notes = [
        f"본 {doc_name}의 유효기간은 발행일로부터 30일입니다.",
        "세부 사항은 협의 후 조정될 수 있습니다.",
        "문의사항이 있으시면 아래 담당자에게 연락 부탁드립니다."
    ]

    for note in notes:
        elements.append(Paragraph(f"• {note}", styles['KoreanNormal']))

    elements.append(Spacer(1, 15*mm))

    # ===== 구분선 =====
    elements.append(HRFlowable(
        width="100%",
        thickness=1,
        color=BORDER_COLOR,
        spaceBefore=5,
        spaceAfter=15
    ))

    # ===== 발신자 정보 =====
    manager = data.get("manager", {})

    sender_left = f"""
    <b>{COMPANY_INFO['name']}</b><br/>
    사업자번호: {COMPANY_INFO['business_number']}<br/>
    주소: {COMPANY_INFO['address']}<br/>
    대표전화: {COMPANY_INFO['phone']}
    """

    sender_right = ""
    if manager.get("name"):
        sender_right = f"""
        <b>담당자</b><br/>
        {manager.get('name', '')} {manager.get('position', '')}<br/>
        Tel: {manager.get('phone', '-')}<br/>
        Email: {manager.get('email', '-')}
        """

    if sender_right:
        sender_data = [[
            Paragraph(sender_left, styles['SmallText']),
            Paragraph(sender_right, styles['SmallText'])
        ]]
        sender_table = Table(sender_data, colWidths=[100*mm, 70*mm])
    else:
        sender_data = [[Paragraph(sender_left, styles['SmallText'])]]
        sender_table = Table(sender_data, colWidths=[170*mm])

    sender_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), DEFAULT_FONT),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    elements.append(sender_table)

    # PDF 빌드
    doc.build(elements)

    return filepath
