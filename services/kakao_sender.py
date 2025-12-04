# -*- coding: utf-8 -*-
"""
카카오톡 알림톡 발송 서비스 (솔라피 API)

솔라피(Solapi) API를 사용한 알림톡 발송
- 솔라피 콘솔: https://console.solapi.com/
- API 가이드: https://developers.solapi.dev/

사전 준비:
1. 솔라피 회원가입
2. API Key 발급 (모든 IP 허용 선택)
3. 카카오 비즈니스 채널 연동
4. 알림톡 템플릿 등록 및 검수 승인 (1~2일 소요)
"""
import os
import hmac
import hashlib
import time
import uuid
import requests
from dotenv import load_dotenv

load_dotenv()

# 솔라피 API 설정
SOLAPI_API_KEY = os.getenv("SOLAPI_API_KEY", "")
SOLAPI_API_SECRET = os.getenv("SOLAPI_API_SECRET", "")
SOLAPI_PF_ID = os.getenv("SOLAPI_PF_ID", "")  # 카카오 비즈니스 채널 연동 후 발급되는 ID
SOLAPI_TEMPLATE_ID_PROPOSAL = os.getenv("SOLAPI_TEMPLATE_ID_PROPOSAL", "")  # 제안서 템플릿
SOLAPI_TEMPLATE_ID_ESTIMATE = os.getenv("SOLAPI_TEMPLATE_ID_ESTIMATE", "")  # 견적서 템플릿
SOLAPI_SENDER_PHONE = os.getenv("SOLAPI_SENDER_PHONE", "")  # 발신번호 (대체발송용)

# 솔라피 API 엔드포인트
SOLAPI_API_URL = "https://api.solapi.com/messages/v4/send"

# 서비스 URL (Vercel 도메인으로 변경)
SERVICE_URL = os.getenv("SERVICE_URL", "http://localhost:5000")


def get_auth_header():
    """
    솔라피 API 인증 헤더 생성 (HMAC-SHA256)
    """
    date = time.strftime('%Y-%m-%dT%H:%M:%S%z')
    salt = str(uuid.uuid4())

    signature = hmac.new(
        SOLAPI_API_SECRET.encode('utf-8'),
        (date + salt).encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

    return f"HMAC-SHA256 apiKey={SOLAPI_API_KEY}, date={date}, salt={salt}, signature={signature}"


def send_kakao_alimtalk(phone, customer_name, doc_type, download_url=None):
    """
    카카오톡 알림톡 발송 (솔라피 API)

    Args:
        phone: 수신자 전화번호 (예: 010-1234-5678 또는 01012345678)
        customer_name: 수신자 이름
        doc_type: 문서 유형 (제안서/견적서/제안서 및 견적서)
        download_url: 문서 다운로드 URL (선택)

    Returns:
        dict: {"success": bool, "error": str or None}
    """
    if not SOLAPI_API_KEY or not SOLAPI_API_SECRET:
        return {
            "success": False,
            "error": "솔라피 API 키가 설정되지 않았습니다. 환경변수를 확인해주세요."
        }

    if not SOLAPI_PF_ID:
        return {
            "success": False,
            "error": "솔라피 카카오 채널 설정이 완료되지 않았습니다."
        }

    # 문서 유형에 따라 템플릿 선택
    if "제안서" in doc_type and "견적서" in doc_type:
        # 둘 다 포함된 경우 제안서 템플릿 사용 (또는 견적서 템플릿)
        template_id = SOLAPI_TEMPLATE_ID_PROPOSAL
        template_doc_type = "제안서"
    elif "견적서" in doc_type:
        template_id = SOLAPI_TEMPLATE_ID_ESTIMATE
        template_doc_type = "견적서"
    else:
        template_id = SOLAPI_TEMPLATE_ID_PROPOSAL
        template_doc_type = "제안서"

    if not template_id:
        return {
            "success": False,
            "error": f"{template_doc_type} 템플릿 설정이 완료되지 않았습니다."
        }

    # 전화번호 정제 (하이픈, 공백 제거)
    phone = phone.replace("-", "").replace(" ", "")

    # 국제번호 형식이면 국내 형식으로 변환
    if phone.startswith("82"):
        phone = "0" + phone[2:]

    try:
        # 템플릿 메시지 생성 (변수 치환된 최종 메시지)
        template_text = get_template_message(customer_name, template_doc_type, download_url or SERVICE_URL)

        # 솔라피 API 요청 데이터 (단건 발송)
        payload = {
            "message": {
                "to": phone,
                "from": SOLAPI_SENDER_PHONE,
                "kakaoOptions": {
                    "pfId": SOLAPI_PF_ID,
                    "templateId": template_id,
                    "variables": {
                        "#{고객명}": customer_name,
                        "#{URL}": download_url or SERVICE_URL
                    },
                    "disableSms": False
                }
            }
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": get_auth_header()
        }

        response = requests.post(
            SOLAPI_API_URL,
            headers=headers,
            json=payload,
            timeout=30
        )

        result = response.json()

        # 응답 확인
        if response.status_code == 200:
            # 단건 발송 응답 처리
            group_id = result.get("groupId")
            message_id = result.get("messageId")

            if group_id or message_id:
                return {
                    "success": True,
                    "error": None,
                    "groupId": group_id,
                    "messageId": message_id
                }
            else:
                return {"success": False, "error": f"발송 실패: {result}"}
        else:
            error_msg = result.get("errorMessage", result.get("message", "API 오류"))
            return {"success": False, "error": f"API 오류 ({response.status_code}): {error_msg}"}

    except requests.Timeout:
        return {"success": False, "error": "API 요청 시간 초과"}
    except requests.RequestException as e:
        return {"success": False, "error": f"API 호출 실패: {str(e)}"}
    except Exception as e:
        return {"success": False, "error": f"발송 실패: {str(e)}"}


def get_template_message(customer_name, doc_type, download_url):
    """
    알림톡 템플릿 메시지 생성

    참고: 실제 알림톡 발송 시에는 카카오에 등록/승인된 템플릿을 사용해야 합니다.
    아래는 템플릿 예시입니다. 실제 템플릿과 동일하게 맞춰주세요.

    템플릿 변수:
    - #{고객명}: 고객 이름
    - #{문서종류}: 제안서/견적서
    - #{URL}: 문서 확인 링크
    """
    return f"""[위플] {doc_type} 안내

안녕하세요, {customer_name}님.
요청하신 {doc_type}를 발송해 드렸습니다.

▶ 문서 확인하기
{download_url}

문의사항이 있으시면 연락 주세요.
감사합니다."""
