"""2026-11-28 실제 PDF 검토에서 나온 오류의 회귀 테스트."""
import json
import os
from pathlib import Path

os.environ.setdefault("ANTHROPIC_API_KEY", "test-not-used")

import report_facts  # noqa: E402
import report_pipeline as rp  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


def _entry(i, start, el1, el2, axis):
    return {
        "index": i, "start_age": start, "end_age": start + 9, "start_year": 2000 + start, "start_month": 4,
        "pillar": {"cheon_gan_element": el1, "ji_ji_element": el2, "hanja": "", "hangul": ""},
        "shipsin": {"cheon_gan": "", "ji_ji": ""}, "axis": axis, "is_current": i == 3,
    }


def test_daewoon_facts_contain_ordinal_table():
    # 1991-03-08 여성 차트와 같은 원소 배열: 화는 19/29/49/59세에 4번 등장
    els = [("수", "토"), ("수", "화"), ("목", "화"), ("목", "토"), ("화", "금"), ("화", "금"), ("토", "토"), ("토", "수")]
    axes = ["관계운", "관계운", "총운", "직업운", "재물운", "재물운", "직업운", "관계운"]
    entries = [_entry(i + 1, 9 + 10 * i, a, b, axes[i]) for i, (a, b) in enumerate(els)]
    facts = report_facts.compute_daewoon_facts(
        {"gender": "female", "forward": True, "current_age": 35, "entries": entries}
    )
    text = report_facts.render_daewoon_facts_kr(facts)
    assert "시기별 오행 등장 순번" in text
    line = next(l for l in text.splitlines() if l.startswith("- 29~38세: 목="))
    assert "목=1번째/총 2번 (첫 등장)" in line and "화=2번째/총 4번" in line
    assert "59~68세: 화=4번째/총 4번 (마지막 등장), 금=2번째/총 2번 (마지막 등장)" in text


def test_german_dates_in_headings_do_not_break():
    flow = rp._report_text_to_flowables("## Februar — Das Gesamtbild: Wasser und Holz, ab 4. Februar\n\nText")
    flat = []
    for f in flow:
        flat.extend(getattr(f, "_content", None) or [f])
    texts = [getattr(f, "text", "") or "" for f in flat]
    assert any("ab 4. Februar" in t for t in texts)


def test_prompts_have_round2_rules():
    def content(name):
        d = json.loads((ROOT / "prompts" / name).read_text(encoding="utf-8"))
        return d["messages"][0]["content"]

    life = content("premium_report_prompt.json")
    assert "서수 표현 규칙" in life and "동사와 부문장" in life
    annual = content("paid_report_prompt.json")
    assert "질문 금지 재확인" in annual and "독자의 사전 행동 가정 금지" in annual
    compat = content("compatibility_report_prompt.json")
    assert "vermutlich" in compat and "이름별 속도 배정 금지" in compat
