# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, jsonify, send_file, make_response
from services.pdf_generator import generate_proposal, generate_estimate
from services.email_sender import send_email
from services.kakao_sender import send_kakao_alimtalk
import os
import json
import base64
import hashlib
import zlib
from datetime import datetime
from io import BytesIO

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
        # 알림톡용 문서 데이터 생성 (프론트에서 계산된 값 그대로 사용)
        doc_data = {
            "customer": customer,
            "apartments": data.get("apartments", []),
            "total_monthly": data.get("total_monthly", 0),
            "discount_label": data.get("discount_label", "할인 없음"),
            "discount_rate": data.get("discount_rate", 0),
            "discount_amount": data.get("discount_amount", 0),
            "monthly_final": data.get("monthly_final", 0),
            "months": data.get("months", 3),
            "final_total": data.get("final_total", 0),
            "manager": data.get("manager", {})
        }

        # 문서 다운로드 URL 생성
        doc_id = encode_doc_data(doc_data, doc_types)
        download_url = f"{SERVICE_URL}/view/{doc_id}"

        results["kakao"] = send_kakao_alimtalk(
            phone=customer["phone"],
            customer_name=customer.get("name", "고객"),
            doc_type=doc_type_text,
            download_url=download_url
        )
        results["download_url"] = download_url

    return jsonify(results)


@app.route("/download/<path:filename>")
def download(filename):
    """PDF 다운로드"""
    return send_file(filename, as_attachment=True)


# 서비스 URL (환경변수에서 가져오기)
SERVICE_URL = os.getenv("SERVICE_URL", "http://localhost:5000")


def encode_doc_data(doc_data, doc_types):
    """문서 데이터를 압축 후 URL-safe Base64로 인코딩"""
    payload = {
        "d": doc_data,  # 키 이름 축약
        "t": doc_types
    }
    json_str = json.dumps(payload, ensure_ascii=False, separators=(',', ':'))
    # zlib으로 압축
    compressed = zlib.compress(json_str.encode('utf-8'), level=9)
    encoded = base64.urlsafe_b64encode(compressed).decode('utf-8')
    return encoded.rstrip('=')


def decode_doc_data(encoded):
    """압축된 Base64 데이터 디코딩"""
    # 패딩 복원
    padding = 4 - len(encoded) % 4
    if padding != 4:
        encoded += '=' * padding
    # Base64 디코딩 후 압축 해제
    compressed = base64.urlsafe_b64decode(encoded.encode('utf-8'))
    json_str = zlib.decompress(compressed).decode('utf-8')
    payload = json.loads(json_str)
    # 키 이름 복원
    return {"data": payload.get("d", {}), "types": payload.get("t", [])}


def generate_doc_id(doc_data):
    """문서 데이터로 짧은 ID 생성"""
    json_str = json.dumps(doc_data, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(json_str.encode()).hexdigest()[:12]


@app.route("/view/<doc_id>")
def view_document(doc_id):
    """문서 보기 페이지 - 다운로드 링크 제공"""
    # doc_id는 encoded data
    try:
        payload = decode_doc_data(doc_id)
        doc_data = payload.get("data", {})
        doc_types = payload.get("types", [])

        customer = doc_data.get("customer", {})

        return render_template(
            "view_document.html",
            customer=customer,
            doc_types=doc_types,
            doc_id=doc_id
        )
    except Exception as e:
        return f"문서를 찾을 수 없습니다: {str(e)}", 404


@app.route("/pdf/<doc_id>/<doc_type>")
def generate_pdf_realtime(doc_id, doc_type):
    """실시간 PDF 생성 및 다운로드"""
    try:
        payload = decode_doc_data(doc_id)
        doc_data = payload.get("data", {})

        # 날짜 추가
        doc_data["date"] = datetime.now().strftime("%Y년 %m월 %d일")

        if doc_type == "estimate":
            pdf_path = generate_estimate(doc_data)
            filename = f"견적서_{doc_data.get('customer', {}).get('company', 'document')}.pdf"
        elif doc_type == "proposal":
            # 제안서는 고정 PDF 파일 반환
            if os.path.exists(PROPOSAL_PDF_PATH):
                return send_file(
                    PROPOSAL_PDF_PATH,
                    mimetype='application/pdf',
                    as_attachment=True,
                    download_name="포커스미디어_제안서.pdf"
                )
            else:
                return "제안서 파일을 찾을 수 없습니다.", 404
        else:
            return "잘못된 문서 유형입니다.", 400

        # 생성된 PDF 파일 전송
        return send_file(
            pdf_path,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        return f"PDF 생성 실패: {str(e)}", 500


def get_document_url(doc_data, doc_types):
    """알림톡용 문서 URL 생성"""
    doc_id = encode_doc_data(doc_data, doc_types)
    return f"{SERVICE_URL}/view/{doc_id}"


if __name__ == "__main__":
    os.makedirs("output", exist_ok=True)
    app.run(debug=True, port=5000)
