# -*- coding: utf-8 -*-
"""
카카오톡 알림톡 발송 서비스

알림톡 발송을 위해서는 카카오 비즈니스 채널과 알림톡 API 연동이 필요합니다.
실제 사용 시에는 아래 중 하나를 선택하여 연동하세요:

1. 카카오 비즈메시지 직접 연동
   - https://business.kakao.com/

2. 알림톡 대행사 API 사용 (권장 - 더 간편함)
   - NHN Cloud (https://www.toast.com/kr/service/notification/kakaotalk_bizmessage)
   - 솔라피 (https://solapi.com/)
   - 알리고 (https://smartsms.aligo.in/)
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

# 알림톡 설정 (예: 솔라피 기준)
KAKAO_API_KEY = os.getenv("KAKAO_API_KEY", "")
KAKAO_API_SECRET = os.getenv("KAKAO_API_SECRET", "")
KAKAO_SENDER_KEY = os.getenv("KAKAO_SENDER_KEY", "")  # 카카오 비즈니스 채널 발신프로필 키
KAKAO_TEMPLATE_CODE = os.getenv("KAKAO_TEMPLATE_CODE", "")  # 승인된 템플릿 코드

# 문서 다운로드 URL (실제 서비스 도메인으로 변경 필요)
SERVICE_URL = os.getenv("SERVICE_URL", "http://localhost:5000")


def send_kakao_alimtalk(phone, customer_name, doc_type, download_url=None):
    """
    카카오톡 알림톡 발송

    Args:
        phone: 수신자 전화번호 (예: 010-1234-5678 또는 01012345678)
        customer_name: 수신자 이름
        doc_type: 문서 유형 (제안서/견적서)
        download_url: 문서 다운로드 URL (선택)

    Returns:
        dict: {"success": bool, "error": str or None}
    """
    if not KAKAO_API_KEY or not KAKAO_SENDER_KEY:
        # API 키가 없으면 시뮬레이션 모드
        return {
            "success": False,
            "error": "카카오 알림톡 설정이 완료되지 않았습니다. .env 파일을 확인해주세요."
        }

    # 전화번호 정제 (하이픈 제거)
    phone = phone.replace("-", "").replace(" ", "")

    # 국제 형식으로 변환
    if phone.startswith("010"):
        phone = "82" + phone[1:]

    try:
        # 실제 알림톡 API 호출 예시 (솔라피 기준)
        # 각 서비스마다 API 형식이 다르므로 선택한 서비스의 문서를 참고하세요
        """
        response = requests.post(
            "https://api.solapi.com/messages/v4/send",
            headers={
                "Authorization": f"Bearer {KAKAO_API_KEY}"
            },
            json={
                "message": {
                    "to": phone,
                    "from": KAKAO_SENDER_KEY,
                    "kakaoOptions": {
                        "pfId": KAKAO_SENDER_KEY,
                        "templateId": KAKAO_TEMPLATE_CODE,
                        "variables": {
                            "#{고객명}": customer_name,
                            "#{문서종류}": doc_type,
                            "#{URL}": download_url or SERVICE_URL
                        }
                    }
                }
            }
        )

        if response.status_code == 200:
            return {"success": True, "error": None}
        else:
            return {"success": False, "error": response.json().get("message", "알 수 없는 오류")}
        """

        # 현재는 시뮬레이션 모드
        print(f"[알림톡 시뮬레이션] 수신: {phone}, 고객명: {customer_name}, 문서: {doc_type}")
        return {
            "success": True,
            "error": None,
            "note": "시뮬레이션 모드 - 실제 발송되지 않음"
        }

    except requests.RequestException as e:
        return {"success": False, "error": f"API 호출 실패: {str(e)}"}
    except Exception as e:
        return {"success": False, "error": f"발송 실패: {str(e)}"}


def get_template_message(customer_name, doc_type, download_url):
    """
    알림톡 템플릿 메시지 생성

    참고: 실제 알림톡 발송 시에는 카카오에 등록/승인된 템플릿을 사용해야 합니다.
    아래는 템플릿 예시입니다.
    """
    return f"""
[위플] {doc_type} 안내

안녕하세요, {customer_name}님.
요청하신 {doc_type}를 발송해 드렸습니다.

▶ 문서 확인하기
{download_url}

문의사항이 있으시면 연락 주세요.
감사합니다.
    """.strip()
