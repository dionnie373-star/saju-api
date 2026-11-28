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


def test_lifetime_prompt_fixes_axis_names_and_forbids_period_recap():
    d = json.loads((ROOT / "prompts" / "premium_report_prompt.json").read_text(encoding="utf-8"))
    c = d["messages"][0]["content"]
    c = c if isinstance(c, str) else json.dumps(c, ensure_ascii=False)
    # PDF 그래프 라벨과 같은 축 이름을 본문에서도 쓰도록 고정
    for ko, de in (("재물운", "Ressourcen"), ("관계운", "Beziehung"), ("직업운", "Talent & Werk"), ("총운", "Stabilität")):
        assert f"{ko}={de}" in c
    assert "Vermögensachse" in c and "만들거나" in c  # 금지 예시로만 등장
    # 개요에서 8개 시기 재요약 금지
    assert "다시 요약하는 문단" in c
    assert "1시기당 1문장 이내" not in c
    # 그래프 라벨은 코드와 일치
    labels = report_pipeline._AXIS_LABELS_DE
    assert labels == {"재물운": "Ressourcen", "관계운": "Beziehung", "직업운": "Talent & Werk", "총운": "Stabilität"}


def test_free_profile_and_share_card_use_unified_disclaimer_de():
    import profile_view, share_card
    assert "Selbstreflexion" not in share_card.TXT["de"]["note"]
    assert "Selbstreflexion" not in share_card.CTXT["de"]["note"]
    assert "Orientierung" in share_card.TXT["de"]["note"] and "Orientierung" in share_card.CTXT["de"]["note"]
    assert "Überblick zur Reflexion" not in profile_view.T["de"]["y_close"]
    assert "persönliche Orientierung" in profile_view.T["de"]["y_close"]
    d = json.loads((ROOT / "prompts" / "free_report_prompt.json").read_text(encoding="utf-8"))
    c = d["messages"][0]["content"]
    c = c if isinstance(c, str) else json.dumps(c, ensure_ascii=False)
    assert "Dieser Inhalt dient der Unterhaltung und als persönliche Orientierung." in c


def test_annual_cross_sell_uses_product_name():
    """연간 리포트 끝 교차판매는 상품 이름을 Saju-Lebenskarte로만 쓰게 한다(실제 PDF에서 Premium-Report/Daeun이 나온 사고)."""
    c = json.loads((ROOT / "prompts" / "paid_report_prompt.json").read_text(encoding="utf-8"))["messages"][0]["content"]
    assert '정확히 "Saju-Lebenskarte"' in c
    assert "프리미엄(대운 리포트)" not in c
