"""실제 연간 리포트 PDF(2026-11-28 검토)에서 발견된 결함의 회귀 테스트."""
import json
from pathlib import Path

from reportlab.platypus import KeepTogether, Paragraph

import report_facts
import report_pipeline

ROOT = Path(__file__).resolve().parent.parent


def test_heading_is_kept_with_body_even_when_blank_line_follows():
    flow = report_pipeline._report_text_to_flowables("## Prolog\n\nErster Absatz des Textes.\n\nZweiter Absatz.")
    first = flow[0]
    assert isinstance(first, KeepTogether)
    kinds = [type(f).__name__ for f in first._content]
    assert "Paragraph" in kinds[2:], f"제목 묶음에 본문 단락이 없음: {kinds}"
    body_in_group = [f for f in first._content if isinstance(f, Paragraph) and f.style.name == "PaljaBody"]
    assert body_in_group, "제목이 본문 없이 홀로 묶임(페이지 하단 고아 제목 재발)"


def test_german_solar_term_names_given_in_facts():
    txt = report_facts.render_solar_boundaries_kr(2027, "de")
    for ko, de in (("입춘", "Frühlingsbeginn"), ("입하", "Sommerbeginn"), ("소서", "Kleine Hitze"),
                   ("한로", "Kalter Tau"), ("입동", "Winterbeginn")):
        assert f"{ko}({de})" in txt
    assert "Lichtbeginn" not in txt


def test_annual_prompt_does_not_assume_free_report_and_uses_new_disclaimer():
    d = json.loads((ROOT / "prompts" / "paid_report_prompt.json").read_text(encoding="utf-8"))
    c = d["messages"][0]["content"]
    c = c if isinstance(c, str) else json.dumps(c, ensure_ascii=False)
    assert "무료 리포트를 이미 읽은 고객" not in c
    assert "persönlichen Reflexion" not in c
    assert "als persönliche Orientierung" in c
    assert "직접 번역하거나 새로 만들지" in c


def test_lifetime_prompt_does_not_assume_annual_report_and_uses_new_disclaimer():
    d = json.loads((ROOT / "prompts" / "premium_report_prompt.json").read_text(encoding="utf-8"))
    c = d["messages"][0]["content"]
    c = c if isinstance(c, str) else json.dumps(c, ensure_ascii=False)
    assert "이미 연간 리포트를 읽은 고객" not in c
    assert "알 수 없으므로" in c
    assert "persönlichen Reflexion" not in c
    assert "als persönliche Orientierung" in c


def test_compat_prompt_disclaimer_has_no_reflexion():
    d = json.loads((ROOT / "prompts" / "compatibility_report_prompt.json").read_text(encoding="utf-8"))
    c = json.dumps(d, ensure_ascii=False)
    assert "gemeinsamen Reflexion" not in c
    assert "als gemeinsame Gesprächsgrundlage" in c
