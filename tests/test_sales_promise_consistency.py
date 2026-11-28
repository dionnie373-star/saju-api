"""판매 문구가 실제 상품(프롬프트)이 제공하지 않는 것을 약속하지 않는지 확인한다.

연간 리포트(paid)는 성찰 질문이 없는 운세 톤이다(2026-11 개편). 사이트/무료 리포트의
구매 유도 문구가 다시 '성찰 질문'을 약속하면 이 테스트가 실패한다.
일생 리포트(premium)는 구간별 짧은 질문이 실제로 있으므로 '질문' 약속은 허용된다.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = (ROOT / "static_site" / "index.html").read_text(encoding="utf-8")


def _prompt_text(name):
    d = json.loads((ROOT / "prompts" / name).read_text(encoding="utf-8"))
    c = d["messages"][0]["content"]
    return c if isinstance(c, str) else json.dumps(c, ensure_ascii=False)


def test_annual_prompt_has_no_reflection_question_section():
    paid = _prompt_text("paid_report_prompt.json")
    assert "Reflexionsfrage" not in paid.split("[출력 구조")[-1]


def test_site_does_not_promise_reflection_questions_for_annual():
    for bad in ("Monatskapitel mit Reflexionsfrage", "Monatliche Reflexionsimpulse",
                "Monatliche Reflexionen", "jeweils mit Reflexionsfrage"):
        assert bad not in SITE, bad


def test_site_does_not_call_products_reflection_guide():
    assert "Reflexionsleitfaden" not in SITE


def test_free_report_upsell_matches_annual_product():
    free = _prompt_text("free_report_prompt.json")
    for bad in ("Reflexionsfragen", "Reflexionsreport", "konkreten Fragen für deine eigenen Entscheidungen"):
        assert bad not in free, bad
    assert re.search(r"Jahresdeutung|Jahresreport", free)


def test_brand_headline_is_deutung_not_selbstreflexion():
    assert "Koreanische Saju-Deutung" in SITE
    assert "Kunst der Selbstreflexion" not in SITE
