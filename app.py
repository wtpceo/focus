# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, jsonify, send_file
from services.pdf_generator import generate_proposal, generate_estimate
from services.email_sender import send_email
from services.kakao_sender import send_kakao_alimtalk
import os
from datetime import datetime

app = Flask(__name__)

# 기간 할인율
DISCOUNT_OPTIONS = {
    "none": {"label": "할인 없음", "rate": 0},
    "5": {"label": "5% 할인", "rate": 0.05},
    "10": {"label": "10% 할인", "rate": 0.10},
    "15": {"label": "15% 할인", "rate": 0.15},
}


@app.route("/")
def index():
    """메인 페이지 - 입력 폼"""
    return render_template("index.html", discount_options=DISCOUNT_OPTIONS)


@app.route("/preview", methods=["POST"])
def preview():
    """미리보기 생성"""
    data = request.json

    # 아파트 목록
    apartments = data.get("apartments", [])
    discount_key = data.get("discount", "none")
    months = int(data.get("months", 3))

    # 총 월 견적 계산
    total_monthly = sum(apt.get("monthly_total", 0) for apt in apartments)

    # 할인 적용
    discount_rate = DISCOUNT_OPTIONS.get(discount_key, {}).get("rate", 0)
    discount_amount = int(total_monthly * discount_rate)
    monthly_final = total_monthly - discount_amount

    # 총 계약 금액
    final_total = monthly_final * months

    return jsonify({
        "customer": data.get("customer", {}),
        "apartments": apartments,
        "total_monthly": total_monthly,
        "discount_label": DISCOUNT_OPTIONS.get(discount_key, {}).get("label", "할인 없음"),
        "discount_rate": discount_rate,
        "discount_amount": discount_amount,
        "monthly_final": monthly_final,
        "months": months,
        "final_total": final_total,
        "manager": data.get("manager", {}),
        "doc_types": data.get("doc_types", ["proposal"])
    })


@app.route("/generate", methods=["POST"])
def generate():
    """PDF 생성"""
    data = request.json
    doc_types = data.get("doc_types", ["proposal"])

    # 아파트 목록
    apartments = data.get("apartments", [])
    discount_key = data.get("discount", "none")
    months = int(data.get("months", 3))

    # 총 월 견적 계산
    total_monthly = sum(apt.get("monthly_total", 0) for apt in apartments)

    # 할인 적용
    discount_rate = DISCOUNT_OPTIONS.get(discount_key, {}).get("rate", 0)
    discount_amount = int(total_monthly * discount_rate)
    monthly_final = total_monthly - discount_amount

    # 총 계약 금액
    final_total = monthly_final * months

    doc_data = {
        "customer": data.get("customer", {}),
        "apartments": apartments,
        "total_monthly": total_monthly,
        "discount_label": DISCOUNT_OPTIONS.get(discount_key, {}).get("label", "할인 없음"),
        "discount_rate": discount_rate,
        "discount_amount": discount_amount,
        "monthly_final": monthly_final,
        "months": months,
        "final_total": final_total,
        "manager": data.get("manager", {}),
        "date": datetime.now().strftime("%Y년 %m월 %d일")
    }

    # PDF 생성 (선택된 문서 유형별로)
    pdf_paths = []

    if "estimate" in doc_types:
        pdf_path = generate_estimate(doc_data)
        pdf_paths.append(pdf_path)

    return jsonify({"pdf_paths": pdf_paths, "success": True})


# 포커스미디어 제안서 PDF 경로 (고정)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROPOSAL_PDF_PATH = os.path.join(BASE_DIR, "포커스미디어_동네상권정보_위즈더플래닝.pdf")


@app.route("/send", methods=["POST"])
def send():
    """이메일 및 카카오톡 발송"""
    data = request.json
    pdf_paths = data.get("pdf_paths", [])
    customer = data.get("customer", {})
    send_methods = data.get("send_methods", [])
    doc_types = data.get("doc_types", [])

    results = {"email": None, "kakao": None}

    # 제안서 선택 시 포커스미디어 제안서 PDF 추가
    if "proposal" in doc_types and os.path.exists(PROPOSAL_PDF_PATH):
        pdf_paths.insert(0, PROPOSAL_PDF_PATH)

    # 문서 유형 텍스트 생성
    doc_type_names = []
    if "proposal" in doc_types:
        doc_type_names.append("제안서")
    if "estimate" in doc_types:
        doc_type_names.append("견적서")
    doc_type_text = " 및 ".join(doc_type_names) if doc_type_names else "문서"

    if "email" in send_methods and customer.get("email"):
        results["email"] = send_email(
            to_email=customer["email"],
            to_name=customer.get("name", "고객"),
            subject=f"[{customer.get('company', '')}] {doc_type_text} 송부드립니다",
            pdf_paths=pdf_paths
        )

    if "kakao" in send_methods and customer.get("phone"):
        results["kakao"] = send_kakao_alimtalk(
            phone=customer["phone"],
            customer_name=customer.get("name", "고객"),
            doc_type=doc_type_text
        )

    return jsonify(results)


@app.route("/download/<path:filename>")
def download(filename):
    """PDF 다운로드"""
    return send_file(filename, as_attachment=True)


if __name__ == "__main__":
    os.makedirs("output", exist_ok=True)
    app.run(debug=True, port=5000)
