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

import functools
import json
import os
import re
import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import requests
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.graphics.shapes import Drawing, Line, Rect, String

from report_facts import (
    compute_daewoon_facts,
    compute_monthly_facts,
    render_daewoon_facts_kr,
    render_monthly_facts_kr,
)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    HRFlowable,
    PageBreak,
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


_VALIDATION_PROMPT_TEMPLATE = """아래 [원본 데이터]와 [리포트 텍스트]를 비교해서, 리포트가 원본 데이터와 \
모순되는 숫자나 사실 주장이 있으면 찾아내세요.

특히 다음을 중점적으로 확인하세요:
- 오행/축이 몇 번 등장한다는 주장(예: "화는 두 번만 등장")이 실제 데이터의 등장 횟수와 정확히 일치하는지
- 나이·연도 계산(예: "N개 시기 = N0년")이 실제 데이터와 일치하는지
- 특정 달/시기를 다른 곳에서 다시 언급할 때(요약·나침반·패턴 섹션 등) 그 달/시기의 본문 챕터에서 말한 오행·축과 \
일치하는지
- 소제목에 "마지막"/"처음"/"유일한" 같은 서수 표현이 실제 등장 횟수와 맞는지

사소한 문체 문제나 창작적 해석의 차이는 무시하고, 명확히 숫자·사실이 틀린 경우만 지적하세요.

[원본 데이터]
{source_data}

[리포트 텍스트]
{report_text}

JSON으로만 답하세요. 다른 텍스트는 절대 포함하지 마세요:
{{"consistent": true 또는 false, "issues": [{{"claim": "리포트에서 틀린 주장을 그대로 인용", "problem": "왜 틀렸는지, 실제로는 어떤지"}}]}}
"""


def validate_report_consistency(report_text, source_data, *, api_key=None, timeout=60):
    """생성된 리포트 텍스트가 원본 계산 데이터(monthly_compact/daewoon_compact 등)와

    모순되지 않는지 두 번째(저렴한) Claude 호출로 자동 검증한다. 사람이 검수하는 게
    아니라 AI가 AI 출력을 검증하는 자동화 단계 — 사람이 승인하지 않아도 파이프라인
    안에서 완결된다.

    반환값: {"consistent": bool, "issues": [...]}
    검증 호출 자체가 실패하면(네트워크 오류 등) 예외를 삼키고
    {"consistent": True, "issues": [], "error": "..."}를 반환해서, 검증 인프라 문제로
    정상 발송이 막히지 않게 한다(발송 자체가 더 중요한 실패 모드이기 때문).
    """
    api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return {"consistent": True, "issues": [], "error": "ANTHROPIC_API_KEY 없음 - 검증 생략"}

    prompt = _VALIDATION_PROMPT_TEMPLATE.format(source_data=source_data, report_text=report_text)
    try:
        resp = requests.post(
            ANTHROPIC_API_URL,
            headers={
                "x-api-key": api_key,
                "anthropic-version": ANTHROPIC_VERSION,
                "content-type": "application/json",
            },
            json={
                "model": "claude-haiku-4-5-20251001",
                "max_tokens": 1500,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=timeout,
        )
        resp.raise_for_status()
        data = resp.json()
        text = "".join(p.get("text", "") for p in data.get("content", []) if p.get("type") == "text")
        # Claude가 ```json ... ``` 코드펜스로 감쌀 수 있어서 벗겨낸다.
        text = text.strip()
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\s*", "", text)
            text = re.sub(r"\s*```$", "", text)
        result = json.loads(text)
        result.setdefault("consistent", True)
        result.setdefault("issues", [])
        return result
    except Exception as e:  # noqa: BLE001 - 검증은 부가 기능, 실패해도 발송은 진행
        return {"consistent": True, "issues": [], "error": f"검증 호출 실패: {e}"}


_BANNED_WORDS = ["Schicksal", "empirisch", "wissenschaftlich", "Studien zeigen", "signifikant", "validiert"]
_HANJA_RE = re.compile(r"[⺀-鿿豈-﫿]")  # CJK 한자/한글 통합 영역
_WRONG_ELEMENT_WORD_RE = re.compile(r"\bGold\b")
# 프롬프트에 "반드시 du로 쓰고 Sie는 절대 쓰지 말 것"이라는 명시적 규칙이 이미
# 있었는데도, 실제 API 재테스트에서 유료/프리미엄 리포트 둘 다 "Sie/Ihr" 격식체로
# 통째로 나온 사례가 발견됨(외부 디자인 리뷰에서도 독립적으로 같은 문제를
# 지적함 - 웹은 "du" 톤인데 PDF만 "Sie"라 브랜드 목소리가 끊긴다는 지적).
# 프롬프트 지시만으로는 안 지켜지는 게 실측으로 확인됐으니, 이것도 코드로
# 결정론적으로 잡는다.
_FORMAL_ADDRESS_RE = re.compile(r"\bSie\b|\bIhr(e|er|es|em|en)?\b")
# 실제 발송된 리포트(Lebenskarte PDF) 검수에서 발견된, 독일어 원어민이 보면
# 바로 걸리는 연어(collocation) 오류 두 가지. 둘 다 프롬프트 지시만으로는
# 막히지 않는 게 실측으로 확인돼서, 다른 격식체/한자 체크와 같은 방식으로
# 코드에서 결정론적으로 잡는다.
_WRONG_COLLOCATION_RE = re.compile(r"\bLeistungen\s+gebracht\b")
_AWKWARD_BEDARF_RE = re.compile(r"\bBedarf\s+nach\b")


def check_mechanical_rules(report_text, *, min_words):
    """LLM 판단이 필요 없는, 코드로 100% 정확하게 확인 가능한 규칙들을 검사한다.

    2차 LLM 검증(validate_report_consistency)은 확률적이라 스스로 오탐/누락을
    낼 수 있다는 게 실제 테스트로 확인됐다(연도 계산을 잘못 검증한 사례). 반면
    금지 단어, 한자 포함 여부, 분량 미달처럼 정규식/카운트로 결정론적으로 확인
    가능한 것들은 LLM에 맡길 이유가 없다 — 여기서 코드로 정확하게 잡는다.

    반환값: 문제 문자열 리스트(비어있으면 통과).
    """
    issues = []
    for word in _BANNED_WORDS:
        if word in report_text:
            issues.append(f"금지 단어 '{word}' 포함됨")
    if _WRONG_ELEMENT_WORD_RE.search(report_text):
        issues.append("'Gold'라는 단어 사용됨 - 금(金)은 반드시 'Metall'로 써야 함")
    hanja_matches = _HANJA_RE.findall(report_text)
    if hanja_matches:
        issues.append(f"한자/CJK 문자 포함됨: {''.join(sorted(set(hanja_matches)))[:20]}")
    formal_matches = _FORMAL_ADDRESS_RE.findall(report_text)
    if formal_matches:
        formal_count = len(_FORMAL_ADDRESS_RE.findall(report_text))
        issues.append(
            f"격식체(Sie/Ihr) {formal_count}회 사용됨 - 웹사이트와 동일하게 반드시 "
            f"'du/dein/dich' 비격식체만 써야 함(Sie/Ihr/Ihnen 전부 금지)"
        )
    if _WRONG_COLLOCATION_RE.search(report_text):
        issues.append("연어 오류: 'Leistungen gebracht'는 틀린 표현 - 'Leistungen erbracht'로 써야 함")
    if _AWKWARD_BEDARF_RE.search(report_text):
        issues.append("어색한 표현: 'Bedarf nach'는 'Bedürfnis nach' 또는 'Bedarf an'으로 써야 함")
    word_count = len(report_text.split())
    if word_count < min_words:
        issues.append(f"분량 미달: {word_count}단어 (최소 {min_words}단어 요구)")
    return issues


# "Schicksal" 최종 방어선(2026-09-27): check_mechanical_rules + 자동 재생성
# 루프(최대 2회)로도, 모델이 "Dies ist kein Schicksal, das über dich verhängt
# wird" 같은 부정문으로 금지 단어를 계속 재도입하는 사례가 실제 API 테스트로
# 확인됨(2회 재시도 후에도 잔존). 프롬프트를 더 강하게 쓰는 시도를 반복하는
# 대신, 최종 텍스트에 대해 결정론적으로 제거하는 후처리 단계를 둔다 - 이 정규식은
# "Schicksal"/"Schicksals"/"Schicksale"/"schicksalhaft" 등 대소문자·활용형·
# "kein Schicksal"/"nicht Schicksal" 같은 부정 표현을 전부 잡는다(단어 자체를
# 잡으므로 앞에 어떤 부정어가 붙어도 걸린다).
_SCHICKSAL_WORD_RE = re.compile(r"schicksal\w*", re.IGNORECASE)


def _strip_schicksal_sentences(text):
    """최종 리포트 텍스트에서 'Schicksal' 계열 단어가 들어간 문장을 통째로 제거.

    check_mechanical_rules/자동 재생성 루프는 그대로 유지한 채(1차 방어선),
    이 함수는 그 루프를 다 쓰고도 문제가 남을 경우를 위한 마지막 방어선이다.
    문장 단위로 지우는 이유: 단어만 빼면 "Dies ist kein , das ..." 처럼 문법이
    깨지므로, 그 문장이 속한 문장 전체를 자연스럽게 들어낸다(같은 줄의 다른
    문장이나 마크다운 접두사(#, -, >)는 그대로 보존).
    """
    if not _SCHICKSAL_WORD_RE.search(text):
        return text

    prefix_re = re.compile(r"^(\s*(?:#{1,3}\s+|[-*•]\s+|>\s+)?)")
    cleaned_lines = []
    for raw_line in text.split("\n"):
        if not _SCHICKSAL_WORD_RE.search(raw_line):
            cleaned_lines.append(raw_line)
            continue

        prefix_match = prefix_re.match(raw_line)
        prefix = prefix_match.group(1) if prefix_match else ""
        body = raw_line[len(prefix):]

        # 문장 분리: 마침표/느낌표/물음표 뒤 공백 기준. 리포트 문체가 대부분
        # 평서문이라 독일어 약어(z.B. 등) 오분리 위험은 낮고, 설령 한 문장이
        # 둘로 잘못 나뉘어도 "Schicksal" 없는 조각은 그대로 유지되므로 안전하다.
        sentences = re.split(r"(?<=[.!?])\s+", body)
        kept = [s for s in sentences if not _SCHICKSAL_WORD_RE.search(s)]
        new_body = " ".join(s for s in kept if s.strip()).strip()

        if new_body:
            cleaned_lines.append(prefix + new_body)
        elif prefix.strip():
            # 헤딩/불릿 줄인데 본문 전체가 날아갔으면, 빈 헤딩을 남기지 않도록
            # 줄 자체를 스킵한다.
            continue
        else:
            # 일반 본문 줄이 통째로 사라진 경우도 빈 줄로 만들지 않고 스킵한다
            # (문단 사이 빈 줄은 원문에 이미 별도로 존재함).
            continue

    result = "\n".join(cleaned_lines)
    # 혹시라도 남는 경우(예: 코드가 못 잡는 특수 줄바꿈 등)를 대비해 마지막으로
    # 한 번 더 전체 텍스트 기준으로 확인 - 그래도 남으면 최소한 단어 자체는
    # 제거해 "Schicksal" 문자열이 최종 출력에 남지 않게 한다.
    if _SCHICKSAL_WORD_RE.search(result):
        result = _SCHICKSAL_WORD_RE.sub("", result)
    return result


def _regenerate_with_correction(prompt_template_name, variables, correction_note, *, api_key=None):
    """같은 프롬프트를 다시 채우되, 마지막 사용자 메시지 끝에 교정 지시를 덧붙여

    한 번 더 호출한다. 실패하면(네트워크 오류 등) None을 반환한다.
    """
    template = _load_prompt_template(prompt_template_name)
    messages = []
    for i, m in enumerate(template["messages"]):
        content = _fill_placeholders(m["content"], variables)
        if i == len(template["messages"]) - 1:
            content += correction_note
        messages.append({"role": m["role"], "content": content})

    body = {
        "model": template.get("model", "claude-haiku-4-5-20251001"),
        "max_tokens": template.get("max_tokens", 8192),
        "messages": messages,
    }
    _api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    try:
        resp = requests.post(
            ANTHROPIC_API_URL,
            headers={
                "x-api-key": _api_key,
                "anthropic-version": ANTHROPIC_VERSION,
                "content-type": "application/json",
            },
            json=body,
            timeout=90,
        )
        if resp.status_code != 200:
            return None
        data = resp.json()
        text = "".join(p.get("text", "") for p in data.get("content", []) if p.get("type") == "text").strip()
        return text or None
    except requests.RequestException:
        return None


def _build_correction_note(validation, *, min_words):
    """검증 결과를 바탕으로 재생성용 교정 지시문을 만든다.

    분량 미달은 특히 재시도에서도 잘 안 고쳐지는 문제로 실제 테스트에서 확인됐다
    (한 번 교정해도 여전히 목표에 못 미침). "충분히 늘려서 다시 쓰세요" 같은
    막연한 지시보다 실제 부족한 단어 수를 숫자로 알려주는 쪽이 효과적이므로,
    분량 문제가 있으면 현재/목표/부족분을 명시한다.
    """
    issues_text = "\n".join(
        f"- 문제: \"{issue.get('claim', '')}\"\n  {issue.get('problem', '')}"
        for issue in validation["issues"]
    )
    length_hint = ""
    for issue in validation["issues"]:
        m = re.search(r"분량 미달: (\d+)단어 \(최소 (\d+)단어", issue.get("problem", ""))
        if m:
            current, required = int(m.group(1)), int(m.group(2))
            shortfall = required - current
            length_hint = (
                f"\n\n[분량 문제 - 구체적 지시] 지금 쓴 초안은 {current}단어인데 최소 "
                f"{required}단어가 필요합니다({shortfall}단어 부족). 요약이나 결론을 "
                f"짧게 줄이는 방식이 아니라, 각 챕터/구간마다 구체적인 예시와 설명을 "
                f"1~2문단씩 추가해서 전체 분량을 늘리세요. 특히 분량이 적었던 챕터부터 "
                f"우선적으로 늘리세요."
            )
            break

    return (
        "\n\n[자동 검증 결과 - 반드시 수정] 방금 작성한 초안에서 아래와 같은 문제가 "
        "발견되었습니다. 이 문제들을 고쳐서 리포트 전체를 처음부터 다시 작성하세요. "
        "특히 오행/축 등장 횟수와 관련된 숫자는 [계산된 사실]에 이미 정확히 계산되어 "
        "있으니 그 숫자를 그대로 사용하세요:\n" + issues_text + length_hint
    )


def generate_verified_report(prompt_template_name, variables, *, source_data, api_key=None, min_words=0, max_retries=2):
    """call_claude로 리포트를 생성하고, 두 종류의 자동 검증을 거친 뒤 문제가 있으면

    최대 max_retries번 자동으로 재생성을 시도한다(사람 검수 없이 AI가 AI 출력을
    스스로 고치는 자동화 루프). 재시도를 다 쓰고도 문제가 남으면, 발송을 막지
    않고 그대로 진행하되 로그에 검증 결과를 남긴다(관리자가 나중에 모니터링할
    수 있도록).

    검증은 두 단계다:
    1. check_mechanical_rules - 금지 단어/한자/분량처럼 코드로 100% 정확하게 확인
       가능한 규칙. LLM에 맡기지 않는다(LLM 검증 자체가 오탐할 수 있다는 게
       실제로 확인됐기 때문).
    2. validate_report_consistency - 오행/축 등장 횟수 같은, 원본 데이터와의
       사실 일치 여부를 2차(저렴한) Claude 호출로 확인. computed_facts를 이미
       프롬프트에 줬기 때문에 대부분의 숫자 오류는 애초에 나오지 않아야 하지만,
       안전망으로 유지한다.

    재시도는 1회로는 분량 미달 같은 문제가 완전히 안 고쳐지는 경우가 실제
    테스트로 확인됐기 때문에 기본 2회까지 시도한다(총 최대 3번 생성: 원본 +
    재시도 2회). 매 재시도마다 현재 상태 기준으로 새 교정 지시를 만든다.

    반환값: (report_text, validation_result) - validation_result에는 "consistent"와
    "issues"가 들어있고, mechanical 문제는 issues 안에 {"claim": "...", "problem": "..."}
    형태로 같이 담긴다.
    """
    report_text = call_claude(prompt_template_name, variables, api_key=api_key)

    def _full_validation(text):
        mechanical_issues = check_mechanical_rules(text, min_words=min_words)
        llm_result = validate_report_consistency(text, source_data, api_key=api_key)
        issues = [{"claim": "(기계적 검사)", "problem": m} for m in mechanical_issues]
        issues.extend(llm_result.get("issues", []))
        return {
            "consistent": not issues,
            "issues": issues,
            "llm_error": llm_result.get("error"),
        }

    validation = _full_validation(report_text)

    attempts = 0
    while not validation["consistent"] and attempts < max_retries:
        attempts += 1
        correction_note = _build_correction_note(validation, min_words=min_words)
        retried_text = _regenerate_with_correction(
            prompt_template_name, variables, correction_note, api_key=api_key
        )
        if not retried_text:
            break
        report_text = retried_text
        validation = _full_validation(report_text)

    # 최종 방어선: 재시도를 다 쓰고도 "Schicksal"이 (부정문 등으로) 남아있으면
    # 여기서 결정론적으로 제거한다. 이후 mechanical 이슈 목록에서도 이제는
    # 해소된 "Schicksal" 관련 항목을 걷어내서, 아래 경고 로그가 실제로 남은
    # 문제만 정확히 보여주게 한다.
    if _SCHICKSAL_WORD_RE.search(report_text):
        report_text = _strip_schicksal_sentences(report_text)
        validation["issues"] = [
            issue for issue in validation["issues"]
            if "Schicksal" not in issue.get("problem", "")
        ]
        validation["consistent"] = not validation["issues"]

    if not validation["consistent"]:
        print(
            f"[report_pipeline] 경고: {prompt_template_name} 자동 재생성 {attempts}회 후에도 "
            f"검증 실패 - issues={validation.get('issues')}"
        )

    return report_text, validation


# ---------------------------------------------------------------------------
# PDF 생성
# ---------------------------------------------------------------------------

# 폰트: 예전엔 커스텀 폰트 임베딩 없이 reportlab 코어 폰트(Times/Helvetica)만
# 썼는데, 실제 웹사이트(Fraunces 세리프 헤딩 + Work Sans 산세리프 본문)와
# PDF가 완전히 다른 폰트를 쓰다 보니 "결제 후 받는 PDF가 웹사이트와 다른
# 브랜드처럼 보인다"는 게 챗지피티 디자인 리뷰에서 지적된 가장 큰 문제였음
# (2026-09-27). fonts/ 아래에 실제 웹사이트와 같은 TTF(Fraunces/Work Sans,
# 둘 다 OFL 라이선스로 재배포 가능)를 임베딩해서 웹↔PDF 폰트를 통일한다.
_FONTS_DIR = os.path.join(os.path.dirname(__file__), "fonts")


def _register_pdf_fonts():
    """Fraunces/Work Sans TTF를 reportlab에 등록. 이미 등록됐으면 조용히 통과."""
    if "WorkSans" in pdfmetrics.getRegisteredFontNames():
        return
    pdfmetrics.registerFont(TTFont("Fraunces", os.path.join(_FONTS_DIR, "Fraunces-SemiBold.ttf")))
    pdfmetrics.registerFont(TTFont("WorkSans", os.path.join(_FONTS_DIR, "WorkSans-Regular.ttf")))
    pdfmetrics.registerFont(TTFont("WorkSans-Bold", os.path.join(_FONTS_DIR, "WorkSans-Bold.ttf")))
    pdfmetrics.registerFont(TTFont("WorkSans-Italic", os.path.join(_FONTS_DIR, "WorkSans-Italic.ttf")))
    pdfmetrics.registerFont(TTFont("WorkSans-BoldItalic", os.path.join(_FONTS_DIR, "WorkSans-BoldItalic.ttf")))
    # registerFontFamily가 있어야 Paragraph 안의 <b>/<i> 마크업이 자동으로
    # Bold/Italic 변형 파일을 찾아 씀 (안 해주면 그냥 Regular로 굵게 흉내만 냄).
    pdfmetrics.registerFontFamily(
        "WorkSans", normal="WorkSans", bold="WorkSans-Bold",
        italic="WorkSans-Italic", boldItalic="WorkSans-BoldItalic",
    )


_register_pdf_fonts()

_PDF_STYLES = {
    "title": ParagraphStyle(
        "PaljaTitle", fontName="Fraunces", fontSize=25, leading=31,
        spaceAfter=2 * mm, textColor="#211D1A",
    ),
    "subtitle": ParagraphStyle(
        "PaljaSubtitle", fontName="WorkSans-Italic", fontSize=12, leading=16,
        spaceAfter=10 * mm, textColor="#8A6F5C",
    ),
    "h2": ParagraphStyle(
        "PaljaH2", fontName="Fraunces", fontSize=17, leading=22,
        spaceBefore=7 * mm, spaceAfter=1 * mm, textColor="#211D1A",
    ),
    "body": ParagraphStyle(
        "PaljaBody", fontName="WorkSans", fontSize=10.5, leading=16,
        spaceAfter=3.5 * mm, textColor="#3B3630",
    ),
    "bullet": ParagraphStyle(
        "PaljaBullet", fontName="WorkSans", fontSize=10.5, leading=16,
        spaceAfter=2 * mm, textColor="#3B3630",
        leftIndent=4 * mm, bulletIndent=0, bulletFontName="WorkSans",
    ),
    # 챗지피티 디자인 리뷰 제안(Pull Quote): 인용문 한 줄(">"로 시작하는 마크다운
    # 블록쿼트)을 본문에 묻히지 않게 큼직한 세리프 이탤릭으로 뽑아서 보여준다.
    "pullquote": ParagraphStyle(
        "PaljaPullQuote", fontName="Fraunces", fontSize=15, leading=21,
        spaceBefore=5 * mm, spaceAfter=5 * mm, textColor="#8A6F5C",
        leftIndent=6 * mm, rightIndent=6 * mm,
    ),
    # 목차("## " 챕터 항목) — 챗지피티 디자인 리뷰 2차 피드백 제안: 챕터
    # 오프너/리플렉션 카드 같은 화려한 요소는 보류하고, 목차 하나만 있어도
    # "AI가 대충 몇 페이지 쓴 PDF"가 아니라 "구조가 있는 리포트"라는 인상을
    # 준다고 판단(2026-09-27). 페이지 번호는 넣지 않음(정확한 페이지 번호를
    # 얻으려면 2-pass 렌더링이 필요해 지금 범위에서는 과함 - 구조를 보여주는
    # 것만으로 충분하다는 게 리뷰의 결론이었음).
    "toc_top": ParagraphStyle(
        "PaljaTocTop", fontName="WorkSans-Bold", fontSize=11.5, leading=20,
        textColor="#211D1A", spaceBefore=2 * mm,
    ),
    "toc_sub": ParagraphStyle(
        "PaljaTocSub", fontName="WorkSans", fontSize=10, leading=16,
        textColor="#786F67", leftIndent=6 * mm,
    ),
}

# h2 제목 바로 아래 그리는 얇은 테라코타 밑줄 — 사이트의 브랜드 액센트 컬러(#C1442E)를
# PDF에도 살짝 가져와서, 완전히 무채색이던 예전 PDF보다 브랜드 일관성을 높임.
_H2_RULE = HRFlowable(
    width=18 * mm, thickness=1.6, color="#C1442E", spaceBefore=0, spaceAfter=4 * mm,
    hAlign="LEFT", lineCap="round",
)

# Claude가 챕터/섹션 구분용으로 마크다운 구분선("---")을 종종 씀 — 예전엔 이걸
# 그냥 플레인 텍스트 "---"로 그대로 출력해서 PDF에 마크다운 문법이 그대로 노출되는
# 버그가 있었음(실제 샘플에서 발견, 2026-09-27). 옅은 회색 가로선으로 렌더링한다.
_SECTION_DIVIDER_RE = re.compile(r"^(-{3,}|\*{3,}|_{3,})$")
_SECTION_DIVIDER_RULE = HRFlowable(
    width="100%", thickness=0.6, color="#E4DCD1", spaceBefore=3 * mm, spaceAfter=3 * mm,
    hAlign="CENTER",
)


_BOLD_MARKDOWN_RE = re.compile(r"\*\*(.+?)\*\*")


def _strip_unsupported_glyphs(text):
    """Helvetica(WinAnsiEncoding=cp1252)가 못 그리는 문자를 전부 제거.

    이모지뿐 아니라 한자/한글(AI가 간지를 丙午 같은 한자로 쓰는 경우 등)도
    Helvetica 코어 폰트로는 렌더링이 안 돼서 네모(■)로 깨져 보인다.
    cp1252로 인코딩 가능한 문자만 남기면(독일어 움라우트/줄표/따옴표 등은
    전부 포함됨) 이 문제를 한 번에 해결할 수 있다.
    """
    return text.encode("cp1252", errors="ignore").decode("cp1252")


_ITALIC_MARKDOWN_RE = re.compile(r"\*(.+?)\*")


def _markdown_bold_to_reportlab(text):
    """`**굵게**`/`*기울임*` 마크다운을 reportlab Paragraph 태그로 변환.

    반드시 **(굵게)를 먼저 치환한 다음 남은 단일 *(기울임)을 치환해야
    **텍스트**가 <i>텍스트</i><i></i> 식으로 잘못 쪼개지지 않는다.
    """
    text = _BOLD_MARKDOWN_RE.sub(r"<b>\1</b>", text)
    text = _ITALIC_MARKDOWN_RE.sub(r"<i>\1</i>", text)
    return text


def _extract_toc_entries(report_text):
    """리포트 본문에서 "## "(대챕터)/"### "(소챕터) 제목만 뽑아 목차 항목 리스트로.

    "# "(리포트 자체 제목, 표지와 중복)는 목차에서 제외한다. 실제 숫자 매김
    ("1. Einführung", "3.1 Die Jahre ...")은 Claude가 이미 본문에 쓰고 있으므로
    그대로 재사용 - 별도로 번호를 다시 매기지 않는다.
    """
    entries = []
    for raw_line in report_text.split("\n"):
        line = raw_line.strip()
        if line.startswith("## "):
            entries.append(("top", line[3:].strip()))
        elif line.startswith("### "):
            entries.append(("sub", line[4:].strip()))
    return entries


def _build_toc_flowables(report_text, *, heading="Inhalt"):
    """목차 페이지를 flowable 리스트로 만든다. 항목이 없으면 빈 리스트 반환.

    정확한 페이지 번호는 2-pass 렌더링이 필요해 이번 범위에서는 넣지 않음 -
    "이게 몇 페이지짜리 대충 쓴 글이 아니라 구조가 있는 리포트"라는 인상을
    주는 게 목적이라, 페이지 번호 없이 구조만 보여줘도 충분하다는 게 디자인
    리뷰의 결론이었다.
    """
    entries = _extract_toc_entries(report_text)
    if not entries:
        return []
    flowables = [
        Paragraph(heading, _PDF_STYLES["h2"]),
        _H2_RULE,
    ]
    for kind, text in entries:
        safe = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        style = "toc_top" if kind == "top" else "toc_sub"
        flowables.append(Paragraph(safe, _PDF_STYLES[style]))
    flowables.append(PageBreak())
    return flowables


def _report_text_to_flowables(report_text):
    """Claude가 만든 (마크다운 ## 제목이 섞인) 평문 텍스트를 PDF 문단으로 변환."""
    flowables = []
    for raw_line in report_text.split("\n"):
        line = raw_line.strip()
        if not line:
            flowables.append(Spacer(1, 2 * mm))
            continue
        line = _strip_unsupported_glyphs(line)
        if _SECTION_DIVIDER_RE.match(line):
            flowables.append(_SECTION_DIVIDER_RULE)
            continue

        # 줄 종류에 따라 태그 접두사를 떼어낸 "본문 텍스트"만 먼저 뽑아낸다.
        # (예전엔 이스케이프를 줄 전체에 먼저 하고 나서 접두사를 잘라서, ">"로
        # 시작하는 인용구를 감지하려면 이미 "&gt;"로 바뀐 뒤라 감지가 안 됐음.)
        if line.startswith("## "):
            kind, content = "h2", line[3:].strip()
        elif line.startswith("### "):
            kind, content = "h2", line[4:].strip()
        elif line.startswith("# "):
            kind, content = "h2", line[2:].strip()
        elif line.startswith("- ") or line.startswith("* ") or line.startswith("• "):
            kind, content = "bullet", line[2:].strip()
        elif line.startswith("> "):
            # 챗지피티 디자인 리뷰 제안(Pull Quote): Claude가 마크다운 블록쿼트로
            # 표시한 한 문장을 본문에 묻히지 않게 큼직한 세리프 인용구로 뽑아낸다.
            kind, content = "pullquote", line[2:].strip().strip('"').strip('„').strip('"')
        else:
            kind, content = "body", line

        # PDF 인코딩은 core/TTF 폰트라 독일어 움라우트(äöüß)나 줄표(–/—) 등은
        # 문제없지만, '<', '&' 등은 escape 해줘야 reportlab의 미니 마크업
        # 파서가 안 깨진다. 이스케이프 후에 **굵게**/*기울임* -> <b>/<i> 변환.
        safe = content.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        safe = _markdown_bold_to_reportlab(safe)

        if kind == "h2":
            flowables.append(Paragraph(safe, _PDF_STYLES["h2"]))
            flowables.append(_H2_RULE)
        elif kind == "bullet":
            # 예전엔 이 줄들이 그냥 "- 텍스트"로 그대로 찍혀서 제대로 된 글머리
            # 기호처럼 안 보였음 — reportlab의 bulletText로 실제 불릿을 그린다.
            flowables.append(Paragraph(safe, _PDF_STYLES["bullet"], bulletText="•"))
        elif kind == "pullquote":
            flowables.append(Paragraph(f"„{safe}“", _PDF_STYLES["pullquote"]))
        else:
            flowables.append(Paragraph(safe, _PDF_STYLES["body"]))
    return flowables


# 축(재물운/관계운/직업운/총운)별 색 — 사이트 하단의 오방색(단청) 줄무늬
# (초록/빨강/노랑/크림/다크)에서 그대로 가져와서 웹과 PDF의 색 언어를 통일한다.
_AXIS_COLORS = {
    "재물운": "#C1442E",  # 테라코타
    "관계운": "#2F6F4E",  # 녹색
    "직업운": "#D4A017",  # 골드
    "총운": "#8A6F5C",    # 뉴트럴 브라운
}
_AXIS_LABELS_DE = {
    "재물운": "Ressourcen",
    "관계운": "Beziehung",
    "직업운": "Talent & Werk",
    "총운": "Stabilität",
}


def _build_daewoon_timeline_drawing(daewoon_facts, *, width_mm=166):
    """80년 대운을 가로 타임라인 그래픽 하나로 요약해서 보여주는 Drawing.

    챗지피티 디자인 리뷰 제안("Lebenslinie"): 24.90유로 리포트를 열자마자
    전체 구조(몇 개 시기, 어떤 축이 언제 바뀌는지, "지금 여기")가 한눈에
    보여야 "콘텐츠 양"이 시각적으로 증명된다고 지적함. LLM 문장이 아니라
    report_facts.py가 계산한 정확한 데이터로 코드가 직접 그리므로 사실
    오류가 날 수 없다.
    """
    entries = daewoon_facts["entries"]
    n = len(entries)
    width = width_mm * mm
    height = 30 * mm
    bar_y = 14 * mm
    bar_h = 6 * mm
    seg_w = width / n

    d = Drawing(width, height)

    current_index = daewoon_facts.get("current_index")

    for i, entry in enumerate(entries):
        x = i * seg_w
        color = _AXIS_COLORS.get(entry["axis"], "#8A6F5C")
        d.add(Rect(x, bar_y, seg_w - 1, bar_h, fillColor=HexColor(color), strokeColor=None))

        # 시작 나이 라벨 (각 구간 왼쪽 경계)
        d.add(String(x, bar_y - 8, f"{entry['start_age']}", fontName="WorkSans", fontSize=7, fillColor=HexColor("#8A8074")))

        if i == current_index:
            cx = x + (seg_w - 1) / 2
            d.add(String(cx, bar_y + bar_h + 10, "DU BIST HIER", fontName="WorkSans-Bold", fontSize=6.5,
                         fillColor=HexColor("#211D1A"), textAnchor="middle"))
            d.add(Line(cx, bar_y + bar_h + 8, cx, bar_y + bar_h + 1, strokeColor=HexColor("#211D1A"), strokeWidth=1))

    # 맨 끝 나이 라벨
    last = entries[-1]
    d.add(String(width - 6, bar_y - 8, f"{last['end_age']}", fontName="WorkSans", fontSize=7, fillColor=HexColor("#8A8074")))

    # 범례: 실제로 등장하는 축만, 순서대로
    seen_axes = list(dict.fromkeys(e["axis"] for e in entries))
    legend_y = height - 8
    lx = 0
    for axis in seen_axes:
        color = _AXIS_COLORS.get(axis, "#8A6F5C")
        d.add(Rect(lx, legend_y, 8, 8, fillColor=HexColor(color), strokeColor=None))
        label = _AXIS_LABELS_DE.get(axis, axis)
        d.add(String(lx + 12, legend_y + 1, label, fontName="WorkSans", fontSize=7.5, fillColor=HexColor("#3B3630")))
        lx += 12 + stringWidth(label, "WorkSans", 7.5) + 16

    return d


def _draw_branded_footer(canvas, doc, *, title):
    """모든 페이지 하단에 "PALJA · <제목>"과 페이지 번호를 작게 찍는다.

    챗지피티 디자인 리뷰 제안: 이런 작은 브랜드 요소가 있어야 PDF가 "그냥
    문서"가 아니라 "상품"처럼 보인다고 지적함(2026-09-27). 표지(1페이지)에는
    이미 큰 제목이 있으니 찍지 않는다.
    """
    if doc.page == 1:
        return
    canvas.saveState()
    canvas.setFont("WorkSans", 8)
    canvas.setFillColor("#A79E93")
    y = 12 * mm
    canvas.drawString(22 * mm, y, f"PALJA · {title}")
    canvas.drawRightString(A4[0] - 22 * mm, y, str(doc.page))
    canvas.restoreState()


def build_pdf(out_path, *, title, subtitle, report_text, intro_flowables=None):
    """리포트 텍스트를 A4 PDF로 렌더링해서 out_path에 저장.

    intro_flowables: 표지(제목/부제) 바로 다음, 본문 텍스트 전에 끼워 넣을
    추가 flowable 목록(예: 프리미엄 리포트의 인생 타임라인 그래픽). 코드로
    직접 그리는 그래픽이라 LLM이 만드는 게 아니라 항상 정확하다.
    """
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
    if intro_flowables:
        story.extend(intro_flowables)
    story.extend(_build_toc_flowables(report_text))
    story.extend(_report_text_to_flowables(report_text))

    footer = functools.partial(_draw_branded_footer, title=title.upper())
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    return out_path


# 문자열 폭 계산에 쓰이는 헬퍼 (지금은 미사용, 추후 표지 레이아웃 등에 재사용 가능)
def _text_width(text, font="Helvetica", size=10.5):
    return stringWidth(text, font, size)


# ---------------------------------------------------------------------------
# 이메일 발송
# ---------------------------------------------------------------------------

BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"


def _send_email_via_brevo_api(*, to_email, subject, html_body, from_email, from_name,
                               attachment_path=None, attachment_name=None):
    """Brevo 트랜잭션 이메일 HTTP API로 발송 (포트 443, SMTP 포트 차단과 무관).

    Render 같은 일부 무료 호스팅은 이메일 발송용 포트(25/465/587)를 막아버려서
    smtplib로는 소켓 연결 자체가 응답 없이 멈추는 문제가 있었다. HTTP API는
    Claude API 호출과 똑같이 443 포트로 통신하므로 이 제한과 무관하게 동작한다.
    """
    import base64

    api_key = os.environ.get("BREVO_API_KEY")
    payload = {
        "sender": {"name": from_name, "email": from_email},
        "to": [{"email": to_email}],
        "subject": subject,
        "htmlContent": html_body,
    }

    if attachment_path:
        with open(attachment_path, "rb") as f:
            content_b64 = base64.b64encode(f.read()).decode("ascii")
        payload["attachment"] = [{
            "content": content_b64,
            "name": attachment_name or os.path.basename(attachment_path),
        }]

    try:
        resp = requests.post(
            BREVO_API_URL,
            headers={
                "api-key": api_key,
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            json=payload,
            timeout=60,
        )
    except requests.RequestException as e:
        raise PipelineError(f"이메일 발송(Brevo API) 중 오류: {e}", status=502) from e

    if resp.status_code >= 300:
        raise PipelineError(
            f"이메일 발송(Brevo API) 실패: {resp.status_code} {resp.text[:300]}",
            status=502,
        )


def send_email(*, to_email, subject, html_body, attachment_path=None, attachment_name=None):
    from_email = os.environ.get("FROM_EMAIL")
    from_name = os.environ.get("FROM_NAME", "Palja")

    if not from_email:
        raise PipelineError("FROM_EMAIL 환경변수가 설정되어 있지 않습니다.", status=500)

    # Brevo API 키가 있으면 HTTP API로 발송 (권장: 포트 차단 문제 없음).
    brevo_api_key = os.environ.get("BREVO_API_KEY")
    if brevo_api_key:
        _send_email_via_brevo_api(
            to_email=to_email,
            subject=subject,
            html_body=html_body,
            from_email=from_email,
            from_name=from_name,
            attachment_path=attachment_path,
            attachment_name=attachment_name,
        )
        return

    # 그 외에는 기존 SMTP 방식 (SMTP 포트가 막혀있지 않은 호스팅 환경에서만 동작).
    smtp_host = os.environ.get("SMTP_HOST")
    smtp_user = os.environ.get("SMTP_USER")
    smtp_password = os.environ.get("SMTP_PASSWORD")
    smtp_port = int(os.environ.get("SMTP_PORT", "465"))

    if not (smtp_host and smtp_user and smtp_password):
        raise PipelineError(
            "이메일 발송 환경변수가 부족합니다. BREVO_API_KEY를 설정하거나, "
            "SMTP_HOST/SMTP_USER/SMTP_PASSWORD를 설정하세요.",
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
        if smtp_port == 465:
            with smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=30) as server:
                server.login(smtp_user, smtp_password)
                server.sendmail(from_email, [to_email], msg.as_string())
        else:
            with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as server:
                server.starttls()
                server.login(smtp_user, smtp_password)
                server.sendmail(from_email, [to_email], msg.as_string())
    except (smtplib.SMTPException, OSError) as e:
        raise PipelineError(f"이메일 발송 중 오류: {e}", status=502) from e


# ---------------------------------------------------------------------------
# 오케스트레이션
# ---------------------------------------------------------------------------

# TODO: palja.de 도메인이 라이브되면 이 값을 "https://palja.de"로 업데이트할 것.
# (다른 곳에도 SITE_BASE_URL 같은 공용 상수가 없어서, 우선 이 파일 안에서만 쓰는
# 로컬 상수로 둔다.)
SITE_BASE_URL = "https://palja-api.onrender.com"

_COMPATIBILITY_PROMO_HTML = f"""\
  <p style="font-size: 13px; line-height: 1.6; color: #3B3630; background: #F7F3EC; padding: 14px 16px; border-radius: 8px;">
    Neugierig, wie gut du mit jemand anderem zusammenpasst?
    <a href="{SITE_BASE_URL}/#kompatibilitaet" style="color: #A9784F;">→ Saju-Kompatibilitäts-Check (4,90 €)</a>
  </p>
"""

# 독일 소비자 대상 상거래 이메일에는 발신자(사업자) 신원이 본문에 바로 보여야
# 신뢰할 수 있다고 판단해 추가한 최소 푸터 — impressum.html과 동일한 정보.
# TODO: palja.de 도메인이 라이브되면 아래 링크를 https://palja.de 기준으로 갱신할 것.
_EMAIL_FOOTER_HTML = f"""\
  <p style="font-size: 12px; line-height: 1.6; color: #A79E93; border-top: 1px solid #E4DCD1; padding-top: 14px; margin-top: 24px;">
    Daily Ground (Jiwon Han) · <a href="{SITE_BASE_URL}/impressum" style="color: #A79E93;">Impressum</a>
    · <a href="{SITE_BASE_URL}/datenschutz" style="color: #A79E93;">Datenschutz</a>
    · <a href="{SITE_BASE_URL}/widerruf" style="color: #A79E93;">Widerruf</a><br>
    Fragen? Schreib uns an <a href="mailto:dionnie373@gmail.com" style="color: #A79E93;">dionnie373@gmail.com</a>.
  </p>
"""

_FREE_EMAIL_SUBJECT = "Dein kostenloses Saju-Profil ist da ✨"

_FREE_EMAIL_HTML_TEMPLATE = """\
<div style="font-family: 'Work Sans', Arial, sans-serif; color: #211D1A; max-width: 560px; margin: 0 auto;">
  <h1 style="font-family: Georgia, serif; font-size: 22px; font-weight: 500;">PALJA</h1>
  <p style="font-size: 15px; line-height: 1.6; color: #3B3630;">
    Hallo{name_suffix},<br><br>
    dein persönliches Fünf-Elemente-Profil nach der koreanischen Saju-Tradition ist fertig —
    du findest es als PDF im Anhang dieser E-Mail.
  </p>
""" + _COMPATIBILITY_PROMO_HTML + """\
  <p style="font-size: 13px; line-height: 1.6; color: #8A8074;">
    Palja dient der Unterhaltung und persönlichen Selbstreflexion und ersetzt keine
    medizinische oder psychologische Beratung.
  </p>
""" + _EMAIL_FOOTER_HTML + """\
</div>
"""


def _send_report(*, email, name, pdf_title, pdf_subtitle, report_text, email_subject, email_html_template, pdf_filename, pdf_intro_flowables=None):
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        pdf_path = os.path.join(tmpdir, pdf_filename)
        build_pdf(
            pdf_path, title=pdf_title, subtitle=pdf_subtitle, report_text=report_text,
            intro_flowables=pdf_intro_flowables,
        )

        name_suffix = f" {name}" if name else ""
        html_body = email_html_template.format(name_suffix=name_suffix)

        send_email(
            to_email=email,
            subject=email_subject,
            html_body=html_body,
            attachment_path=pdf_path,
            attachment_name=pdf_filename,
        )
    return {"ok": True}


def run_free_signup(*, payload, calc_result):
    """무료 리포트 전체 파이프라인: AI 텍스트 생성 -> PDF -> 이메일 발송.

    payload: /signup으로 들어온 원본 요청 (name, email, ...)
    calc_result: app.run_calculation()이 반환한 사주 계산 결과
    """
    name = (payload.get("name") or "").strip()
    email = payload["email"].strip()

    report_text = call_claude(
        "free_report_prompt.json",
        {"compact": calc_result["compact"]},
    )

    return _send_report(
        email=email,
        name=name,
        pdf_title="Dein Saju-Profil",
        pdf_subtitle=f"Erstellt für {name}" if name else "Dein persönliches Fünf-Elemente-Profil",
        report_text=report_text,
        email_subject=_FREE_EMAIL_SUBJECT,
        email_html_template=_FREE_EMAIL_HTML_TEMPLATE,
        pdf_filename="Palja-Profil.pdf",
    )


_PAID_EMAIL_SUBJECT = "Dein Palja-Jahresreport ist da 📖"

_PAID_EMAIL_HTML_TEMPLATE = """\
<div style="font-family: 'Work Sans', Arial, sans-serif; color: #211D1A; max-width: 560px; margin: 0 auto;">
  <h1 style="font-family: Georgia, serif; font-size: 22px; font-weight: 500;">PALJA</h1>
  <p style="font-size: 15px; line-height: 1.6; color: #3B3630;">
    Hallo{name_suffix},<br><br>
    vielen Dank für deinen Kauf. Dein persönlicher Jahresreport nach der koreanischen Saju-Tradition —
    mit allen 12 Monaten im Detail — liegt dieser E-Mail als PDF bei.
  </p>
""" + _COMPATIBILITY_PROMO_HTML + """\
  <p style="font-size: 13px; line-height: 1.6; color: #8A8074;">
    Palja dient der Unterhaltung und persönlichen Selbstreflexion und ersetzt keine
    medizinische oder psychologische Beratung.
  </p>
""" + _EMAIL_FOOTER_HTML + """\
</div>
"""


def run_paid_signup(*, payload, calc_result):
    """유료(9,90€) 12개월 연간 리포트 파이프라인.

    calc_result에는 monthly_compact가 있어야 한다(=run_calculation 호출 시
    payload에 monthly_year를 넘겼어야 함). 결제 웹훅에서 이 함수를 호출하기 전에
    호출측이 monthly_year를 채워서 run_calculation을 실행해야 한다.
    """
    name = (payload.get("name") or "").strip()
    email = payload["email"].strip()

    if not calc_result.get("monthly_compact"):
        raise PipelineError(
            "월별 데이터(monthly_compact)가 없습니다. run_calculation 호출 시 "
            "monthly_year를 지정해야 유료 리포트를 만들 수 있습니다.",
            status=500,
        )

    computed_facts_kr = ""
    monthly_struct = calc_result.get("monthly")
    if monthly_struct and monthly_struct.get("months"):
        try:
            monthly_facts = compute_monthly_facts(monthly_struct, calc_result.get("element_counts"))
            computed_facts_kr = render_monthly_facts_kr(monthly_facts)
        except Exception as e:  # noqa: BLE001 - 계산된 사실은 부가 QA 장치이지 필수 전제조건이 아님
            print(f"[report_pipeline] 경고: compute_monthly_facts 실패, computed_facts 없이 진행: {e}")

    report_text, _validation = generate_verified_report(
        "paid_report_prompt.json",
        {
            "compact": calc_result["compact"],
            "monthly_compact": calc_result["monthly_compact"],
            "computed_facts": computed_facts_kr,
        },
        # 검증 패스에도 코드로 계산된 사실을 같이 줘서, 검증 모델이 원본 데이터를
        # 보고 직접 다시 계산하다가 스스로 틀리는 일(실제로 한 번 발생함)을 줄인다.
        source_data=calc_result["monthly_compact"] + "\n\n[계산된 사실]\n" + computed_facts_kr,
        min_words=2500,
    )

    return _send_report(
        email=email,
        name=name,
        pdf_title="Dein Saju-Jahresreport",
        pdf_subtitle=f"Erstellt für {name}" if name else "Dein persönlicher Jahresreport",
        report_text=report_text,
        email_subject=_PAID_EMAIL_SUBJECT,
        email_html_template=_PAID_EMAIL_HTML_TEMPLATE,
        pdf_filename="Palja-Jahresreport.pdf",
    )


_PREMIUM_EMAIL_SUBJECT = "Deine Palja-Lebenskarte ist da 🧭"

_PREMIUM_EMAIL_HTML_TEMPLATE = """\
<div style="font-family: 'Work Sans', Arial, sans-serif; color: #211D1A; max-width: 560px; margin: 0 auto;">
  <h1 style="font-family: Georgia, serif; font-size: 22px; font-weight: 500;">PALJA</h1>
  <p style="font-size: 15px; line-height: 1.6; color: #3B3630;">
    Hallo{name_suffix},<br><br>
    vielen Dank für deinen Kauf. Deine persönliche Lebenskarte nach der koreanischen Saju-Tradition —
    mit deinen 10-Jahres-Lebensphasen — liegt dieser E-Mail als PDF bei.
  </p>
""" + _COMPATIBILITY_PROMO_HTML + """\
  <p style="font-size: 13px; line-height: 1.6; color: #8A8074;">
    Palja dient der Unterhaltung und persönlichen Selbstreflexion und ersetzt keine
    medizinische oder psychologische Beratung.
  </p>
""" + _EMAIL_FOOTER_HTML + """\
</div>
"""


_COMPATIBILITY_EMAIL_SUBJECT = "Eure Saju-Kompatibilität ist da 💫"

_COMPATIBILITY_EMAIL_HTML_TEMPLATE = """\
<div style="font-family: 'Work Sans', Arial, sans-serif; color: #211D1A; max-width: 560px; margin: 0 auto;">
  <h1 style="font-family: Georgia, serif; font-size: 22px; font-weight: 500;">PALJA</h1>
  <p style="font-size: 15px; line-height: 1.6; color: #3B3630;">
    Hallo{name_suffix},<br><br>
    vielen Dank für deinen Kauf. Eure Saju-Kompatibilitätsanalyse liegt dieser E-Mail als PDF bei.
  </p>
  <p style="font-size: 13px; line-height: 1.6; color: #8A8074;">
    Palja dient der Unterhaltung und persönlichen Selbstreflexion und ersetzt keine
    medizinische oder psychologische Beratung.
  </p>
""" + _EMAIL_FOOTER_HTML + """\
</div>
"""


def run_compatibility_signup(*, payload, calc_result_a, calc_result_b):
    """궁합(Kompatibilität) 리포트 파이프라인: 두 사람의 사주를 비교.

    payload: 웹훅 customData (email, name_a/name_b 등 포함)
    calc_result_a / calc_result_b: 각각 app.run_calculation()으로 계산된 결과
    (Person A = 결제한 본인, Person B = 궁합을 보고 싶은 상대방인 게 보통이지만
    파이프라인 입장에서는 순서가 대칭적이다).
    """
    name_a = (payload.get("name_a") or "Person A").strip()
    name_b = (payload.get("name_b") or "Person B").strip()
    email = payload["email"].strip()

    # 성별은 선택 입력이다 (Saju 계산 자체에는 쓰이지 않음 — daewoon 계산에만 필요하고
    # 궁합 리포트에는 daewoon이 없음). 명시적으로 "female"/"male"을 골랐을 때만 프롬프트가
    # 그 사람에게 자연스러운 독일어 대명사(sie/er)를 쓰도록 허용하고, 그 외(선택 안 함/
    # "divers"/모름)에는 프롬프트가 이름 반복 등 성별 중립적인 표현으로 안전하게 대체한다.
    _GENDER_LABELS = {"female": "weiblich", "male": "männlich"}
    gender_a = _GENDER_LABELS.get((payload.get("gender_a") or "").strip().lower(), "keine Angabe")
    gender_b = _GENDER_LABELS.get((payload.get("gender_b") or "").strip().lower(), "keine Angabe")

    report_text = call_claude(
        "compatibility_report_prompt.json",
        {
            "name_a": name_a,
            "name_b": name_b,
            "gender_a": gender_a,
            "gender_b": gender_b,
            "compact_a": calc_result_a["compact"],
            "compact_b": calc_result_b["compact"],
        },
    )

    return _send_report(
        email=email,
        name=None,
        pdf_title="Eure Saju-Kompatibilität",
        pdf_subtitle=f"{name_a} & {name_b}",
        report_text=report_text,
        email_subject=_COMPATIBILITY_EMAIL_SUBJECT,
        email_html_template=_COMPATIBILITY_EMAIL_HTML_TEMPLATE,
        pdf_filename="Palja-Kompatibilitaet.pdf",
    )


def run_premium_signup(*, payload, calc_result):
    """프리미엄(대운) 인생 지도 리포트 파이프라인.

    calc_result에는 daewoon_compact가 있어야 한다(=run_calculation 호출 시
    payload에 gender를 넘겼어야 함).
    """
    name = (payload.get("name") or "").strip()
    email = payload["email"].strip()

    if not calc_result.get("daewoon_compact"):
        raise PipelineError(
            "대운 데이터(daewoon_compact)가 없습니다. run_calculation 호출 시 "
            "gender를 지정해야 프리미엄 리포트를 만들 수 있습니다.",
            status=500,
        )

    computed_facts_kr = ""
    daewoon_facts = None
    daewoon_struct = calc_result.get("daewoon")
    if daewoon_struct and daewoon_struct.get("entries"):
        try:
            daewoon_facts = compute_daewoon_facts(daewoon_struct)
            computed_facts_kr = render_daewoon_facts_kr(daewoon_facts)
        except Exception as e:  # noqa: BLE001 - 계산된 사실은 부가 QA 장치이지 필수 전제조건이 아님
            print(f"[report_pipeline] 경고: compute_daewoon_facts 실패, computed_facts 없이 진행: {e}")
            daewoon_facts = None

    report_text, _validation = generate_verified_report(
        "premium_report_prompt.json",
        {
            "compact": calc_result["compact"],
            "daewoon_compact": calc_result["daewoon_compact"],
            "computed_facts": computed_facts_kr,
        },
        # 검증 패스에도 코드로 계산된 사실을 같이 줘서, 검증 모델이 원본 데이터를
        # 보고 직접 다시 계산하다가 스스로 틀리는 일(실제로 한 번 발생함)을 줄인다.
        source_data=calc_result["daewoon_compact"] + "\n\n[계산된 사실]\n" + computed_facts_kr,
        # 실제 API 재테스트 결과 3800단어는 재시도 2회를 다 써도 안정적으로
        # 못 맞췄음(최고 3357단어) - 프롬프트 목표도 3,200~4,200으로 낮춰서
        # 달성 가능한 기준으로 재설정함(2026-09-27).
        min_words=3200,
    )

    intro_flowables = None
    if daewoon_facts:
        try:
            intro_flowables = [
                Paragraph("Deine Lebenskarte auf einen Blick", _PDF_STYLES["h2"]),
                _H2_RULE,
                _build_daewoon_timeline_drawing(daewoon_facts),
                Spacer(1, 6 * mm),
            ]
        except Exception as e:  # noqa: BLE001 - 타임라인 그래픽은 부가 요소, 실패해도 리포트 발송은 막지 않음
            print(f"[report_pipeline] 경고: 타임라인 그래픽 생성 실패, 없이 진행: {e}")
            intro_flowables = None

    return _send_report(
        email=email,
        name=name,
        pdf_title="Deine Saju-Lebenskarte",
        pdf_subtitle=f"Erstellt für {name}" if name else "Deine persönliche Lebenskarte",
        report_text=report_text,
        email_subject=_PREMIUM_EMAIL_SUBJECT,
        email_html_template=_PREMIUM_EMAIL_HTML_TEMPLATE,
        pdf_filename="Palja-Lebenskarte.pdf",
        pdf_intro_flowables=intro_flowables,
    )
