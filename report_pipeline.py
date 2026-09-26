"""report_pipeline: 무료 리포트 자동화 파이프라인.

흐름: 신청 폼 데이터 -> (app.py가 이미 계산한) 사주 결과 -> Claude API로
독일어 리포트 텍스트 생성 -> PDF 생성 -> 이메일 발송.

필요한 환경변수:
  ANTHROPIC_API_KEY   Claude API 키 (필수)
  SMTP_HOST           이메일 발송 서버 (필수, 예: smtp.sendgrid.net)
  SMTP_PORT           기본 465 (SSL)
  SMTP_USER           SMTP 로그인 계정
  SMTP_PASSWORD       SMTP 로그인 비밀번호/API 키
  FROM_EMAIL          발신자 이메일 주소 (필수)
  FROM_NAME           발신자 표시 이름 (기본 "Palja")

이 모듈은 앤트로픽 파이썬 SDK 없이, requests로 Messages API를 직접 호출한다
(현재 개발 샌드박스의 패키지 미러에 anthropic SDK가 없어서이기도 하고,
의존성을 하나 줄여서 배포 환경에 상관없이 동작하게 하기 위함이기도 하다).
"""

from __future__ import annotations

import json
import os
import re
import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import requests
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
)

PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "prompts")
ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"


class PipelineError(Exception):
    """파이프라인 어느 단계에서든 실패하면 이걸 던진다(.status는 HTTP 상태 코드)."""

    def __init__(self, message, status=500):
        super().__init__(message)
        self.status = status


def _load_prompt_template(name):
    path = os.path.join(PROMPTS_DIR, name)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _fill_placeholders(text, variables):
    def repl(match):
        key = match.group(1).strip()
        return str(variables.get(key, ""))

    return re.sub(r"\{\{\s*([\w.]+)\s*\}\}", repl, text)


def call_claude(prompt_template_name, variables, *, api_key=None, timeout=90):
    """prompts/*.json 템플릿을 불러와 변수({{compact}} 등)를 채운 뒤 Claude를 호출.

    성공 시 생성된 독일어 리포트 텍스트(str)를 반환한다.
    """
    api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise PipelineError(
            "ANTHROPIC_API_KEY 환경변수가 설정되어 있지 않습니다. "
            "Claude API 콘솔에서 발급받은 키를 서버 환경변수로 등록해야 합니다.",
            status=500,
        )

    template = _load_prompt_template(prompt_template_name)
    messages = []
    for m in template["messages"]:
        content = _fill_placeholders(m["content"], variables)
        messages.append({"role": m["role"], "content": content})

    body = {
        "model": template.get("model", "claude-haiku-4-5-20251001"),
        "max_tokens": template.get("max_tokens", 8192),
        "messages": messages,
    }

    try:
        resp = requests.post(
            ANTHROPIC_API_URL,
            headers={
                "x-api-key": api_key,
                "anthropic-version": ANTHROPIC_VERSION,
                "content-type": "application/json",
            },
            json=body,
            timeout=timeout,
        )
    except requests.RequestException as e:
        raise PipelineError(f"Claude API 호출 중 네트워크 오류: {e}") from e

    if resp.status_code != 200:
        raise PipelineError(
            f"Claude API 오류 (status {resp.status_code}): {resp.text[:500]}",
            status=502,
        )

    data = resp.json()
    parts = data.get("content", [])
    text = "".join(p.get("text", "") for p in parts if p.get("type") == "text")
    if not text.strip():
        raise PipelineError("Claude가 빈 응답을 반환했습니다.", status=502)
    return text.strip()


# ---------------------------------------------------------------------------
# PDF 생성
# ---------------------------------------------------------------------------

_PDF_STYLES = {
    "title": ParagraphStyle(
        "PaljaTitle", fontName="Helvetica-Bold", fontSize=22, leading=28,
        spaceAfter=4 * mm, textColor="#211D1A",
    ),
    "subtitle": ParagraphStyle(
        "PaljaSubtitle", fontName="Helvetica", fontSize=11, leading=15,
        spaceAfter=10 * mm, textColor="#6B625A",
    ),
    "h2": ParagraphStyle(
        "PaljaH2", fontName="Helvetica-Bold", fontSize=15, leading=20,
        spaceBefore=6 * mm, spaceAfter=3 * mm, textColor="#211D1A",
    ),
    "body": ParagraphStyle(
        "PaljaBody", fontName="Helvetica", fontSize=10.5, leading=16,
        spaceAfter=3.5 * mm, textColor="#3B3630",
    ),
}


def _report_text_to_flowables(report_text):
    """Claude가 만든 (마크다운 ## 제목이 섞인) 평문 텍스트를 PDF 문단으로 변환."""
    flowables = []
    for raw_line in report_text.split("\n"):
        line = raw_line.strip()
        if not line:
            flowables.append(Spacer(1, 2 * mm))
            continue
        # PDF 인코딩은 Helvetica 코어 폰트(Latin-1)라 독일어 움라우트(äöüß)는 문제없지만
        # '<', '&' 등은 escape 해줘야 reportlab의 미니 마크업 파서가 안 깨진다.
        safe = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        if line.startswith("## "):
            flowables.append(Paragraph(safe[3:].strip(), _PDF_STYLES["h2"]))
        elif line.startswith("### "):
            flowables.append(Paragraph(safe[4:].strip(), _PDF_STYLES["h2"]))
        elif line.startswith("# "):
            flowables.append(Paragraph(safe[2:].strip(), _PDF_STYLES["h2"]))
        else:
            flowables.append(Paragraph(safe, _PDF_STYLES["body"]))
    return flowables


def build_pdf(out_path, *, title, subtitle, report_text):
    """리포트 텍스트를 A4 PDF로 렌더링해서 out_path에 저장."""
    doc = SimpleDocTemplate(
        out_path, pagesize=A4,
        leftMargin=22 * mm, rightMargin=22 * mm,
        topMargin=24 * mm, bottomMargin=20 * mm,
        title=title,
    )
    story = [
        Paragraph(title, _PDF_STYLES["title"]),
        Paragraph(subtitle, _PDF_STYLES["subtitle"]),
    ]
    story.extend(_report_text_to_flowables(report_text))
    doc.build(story)
    return out_path


# 문자열 폭 계산에 쓰이는 헬퍼 (지금은 미사용, 추후 표지 레이아웃 등에 재사용 가능)
def _text_width(text, font="Helvetica", size=10.5):
    return stringWidth(text, font, size)


# ---------------------------------------------------------------------------
# 이메일 발송
# ---------------------------------------------------------------------------

def send_email(*, to_email, subject, html_body, attachment_path=None, attachment_name=None):
    smtp_host = os.environ.get("SMTP_HOST")
    smtp_user = os.environ.get("SMTP_USER")
    smtp_password = os.environ.get("SMTP_PASSWORD")
    from_email = os.environ.get("FROM_EMAIL")
    from_name = os.environ.get("FROM_NAME", "Palja")
    smtp_port = int(os.environ.get("SMTP_PORT", "465"))

    if not (smtp_host and smtp_user and smtp_password and from_email):
        raise PipelineError(
            "이메일 발송 환경변수(SMTP_HOST/SMTP_USER/SMTP_PASSWORD/FROM_EMAIL)가 "
            "설정되어 있지 않습니다.",
            status=500,
        )

    msg = MIMEMultipart()
    msg["Subject"] = subject
    msg["From"] = f"{from_name} <{from_email}>"
    msg["To"] = to_email
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    if attachment_path:
        with open(attachment_path, "rb") as f:
            part = MIMEApplication(f.read(), _subtype="pdf")
        part.add_header(
            "Content-Disposition", "attachment",
            filename=attachment_name or os.path.basename(attachment_path),
        )
        msg.attach(part)

    try:
        with smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=30) as server:
            server.login(smtp_user, smtp_password)
            server.sendmail(from_email, [to_email], msg.as_string())
    except (smtplib.SMTPException, OSError) as e:
        raise PipelineError(f"이메일 발송 중 오류: {e}", status=502) from e


# ---------------------------------------------------------------------------
# 오케스트레이션
# ---------------------------------------------------------------------------

_FREE_EMAIL_SUBJECT = "Dein kostenloses Saju-Profil ist da ✨"

_FREE_EMAIL_HTML_TEMPLATE = """\
<div style="font-family: 'Work Sans', Arial, sans-serif; color: #211D1A; max-width: 560px; margin: 0 auto;">
  <h1 style="font-family: Georgia, serif; font-size: 22px; font-weight: 500;">PALJA</h1>
  <p style="font-size: 15px; line-height: 1.6; color: #3B3630;">
    Hallo{name_suffix},<br><br>
    dein persönliches Fünf-Elemente-Profil nach der koreanischen Saju-Tradition ist fertig —
    du findest es als PDF im Anhang dieser E-Mail.
  </p>
  <p style="font-size: 13px; line-height: 1.6; color: #8A8074;">
    Palja dient der Unterhaltung und persönlichen Selbstreflexion und ersetzt keine
    medizinische oder psychologische Beratung.
  </p>
</div>
"""


def run_free_signup(*, payload, calc_result):
    """무료 리포트 전체 파이프라인: AI 텍스트 생성 -> PDF -> 이메일 발송.

    payload: /signup으로 들어온 원본 요청 (name, email, ...)
    calc_result: app.run_calculation()이 반환한 사주 계산 결과
    """
    name = (payload.get("name") or "").strip()
    email = payload["email"].strip()

    report_text = call_claude(
        "free_report_prompt.json",
        {"4.data.compact": calc_result["compact"], "compact": calc_result["compact"]},
    )

    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        pdf_path = os.path.join(tmpdir, "palja-profil.pdf")
        build_pdf(
            pdf_path,
            title="Dein Saju-Profil",
            subtitle=f"Erstellt für {name}" if name else "Dein persönliches Fünf-Elemente-Profil",
            report_text=report_text,
        )

        name_suffix = f" {name}" if name else ""
        html_body = _FREE_EMAIL_HTML_TEMPLATE.format(name_suffix=name_suffix)

        send_email(
            to_email=email,
            subject=_FREE_EMAIL_SUBJECT,
            html_body=html_body,
            attachment_path=pdf_path,
            attachment_name="Palja-Profil.pdf",
        )

    return {"ok": True}
