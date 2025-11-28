# -*- coding: utf-8 -*-
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import os
from dotenv import load_dotenv

load_dotenv()

# 이메일 설정 (환경변수에서 로드)
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USE_SSL = os.getenv("SMTP_USE_SSL", "false").lower() == "true"
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SENDER_NAME = os.getenv("SENDER_NAME", "위플")
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "")


def send_email(to_email, to_name, subject, pdf_paths=None, body=None):
    """
    이메일 발송

    Args:
        to_email: 수신자 이메일
        to_name: 수신자 이름
        subject: 제목
        pdf_paths: 첨부할 PDF 파일 경로 리스트
        body: 본문 (없으면 기본 템플릿 사용)

    Returns:
        dict: {"success": bool, "error": str or None}
    """
    if not SMTP_USERNAME or not SMTP_PASSWORD:
        return {
            "success": False,
            "error": "이메일 설정이 완료되지 않았습니다. .env 파일을 확인해주세요."
        }

    # pdf_paths가 문자열이면 리스트로 변환
    if isinstance(pdf_paths, str):
        pdf_paths = [pdf_paths]
    elif pdf_paths is None:
        pdf_paths = []

    try:
        # 메시지 생성
        msg = MIMEMultipart()
        msg['From'] = f"{SENDER_NAME} <{SENDER_EMAIL or SMTP_USERNAME}>"
        msg['To'] = to_email
        msg['Subject'] = subject

        # 본문
        if body is None:
            body = f"""
안녕하세요, {to_name}님.

요청하신 문서를 첨부파일로 보내드립니다.
확인 부탁드리며, 문의사항이 있으시면 연락 주세요.

감사합니다.

---
{SENDER_NAME}
            """.strip()

        msg.attach(MIMEText(body, 'plain', 'utf-8'))

        # PDF 첨부 (여러 개 가능)
        for pdf_path in pdf_paths:
            if pdf_path and os.path.exists(pdf_path):
                with open(pdf_path, 'rb') as f:
                    pdf_attachment = MIMEApplication(f.read(), _subtype='pdf')
                    pdf_filename = os.path.basename(pdf_path)
                    pdf_attachment.add_header(
                        'Content-Disposition',
                        'attachment',
                        filename=('utf-8', '', pdf_filename)
                    )
                    msg.attach(pdf_attachment)

        # 발송 (SSL 또는 TLS 사용)
        if SMTP_USE_SSL:
            # SSL 연결 (포트 465)
            with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
                server.login(SMTP_USERNAME, SMTP_PASSWORD)
                server.send_message(msg)
        else:
            # TLS 연결 (포트 587)
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()
                server.login(SMTP_USERNAME, SMTP_PASSWORD)
                server.send_message(msg)

        return {"success": True, "error": None}

    except smtplib.SMTPAuthenticationError as e:
        return {
            "success": False,
            "error": f"이메일 인증 실패: {str(e)}. 사용자: {SMTP_USERNAME}"
        }
    except smtplib.SMTPException as e:
        return {"success": False, "error": f"SMTP 오류: {str(e)}"}
    except Exception as e:
        return {"success": False, "error": f"발송 실패: {str(e)}"}
