"""장면 후보 은행·패턴 별명 선택 테스트 (의존성 없이 실행 가능)."""
import json
import re
from pathlib import Path

import pair_relations
import pair_scenes

# report_pipeline의 검사와 같은 기준을 의존성 없이 재현한다(대문자 Ihr/Sie, 한자·한글, 금지어).
FORMAL = re.compile(r"\bSie\b|\bIhr(e|er|es|em|en)?\b")
CJK = re.compile(r"[぀-ヿ㐀-鿿가-힯豈-﫿]")
BANNED = ["beweist", "garantiert", "offenbart", "einmalige Gelegenheit", "letzte Chance",
          "idealer Zeitpunkt", "entscheidender Moment", "empirisch", "wissenschaftlich",
          "Schicksal", "Karma", "Seelenverwandt", "Studien zeigen", "signifikant", "validiert"]


def _all_texts():
    for code, items in pair_scenes.BANK.items():
        for theme, family, scene, question in items:
            yield code, theme, scene
            yield code, theme, question
    for name in pair_scenes.PATTERN_NAMES.values():
        yield "pattern", name, name


def test_bank_texts_pass_mechanical_rules():
    for code, theme, text in _all_texts():
        assert not FORMAL.search(text), (code, theme, text)
        assert not CJK.search(text), (code, theme, text)
        for w in BANNED:
            assert w.lower() not in text.lower(), (code, theme, w)


def test_themes_unique_and_codes_known():
    themes = [i[0] for items in pair_scenes.BANK.values() for i in items]
    assert len(themes) == len(set(themes))
    known = set(pair_relations.KO_NAME) | {"same_branch"}
    assert set(pair_scenes.BANK) <= known
    assert set(pair_scenes.SCENE_ORDER) == set(pair_scenes.BANK)
    assert set(pair_scenes.KO_LABEL) >= set(pair_scenes.BANK)


def test_scenes_are_conditional():
    cond = re.compile(r"könnte|könnten|kann|bedeutet nicht|ist zunächst|lohnt sich|muss nicht")
    for code, items in pair_scenes.BANK.items():
        for theme, _f, scene, _q in items:
            assert cond.search(scene), (code, theme)


def _pill(h):
    return {"hanja": h}


def _result(a, b):
    return pair_relations.compare(a, b)


A = {"year": _pill("甲子"), "month": _pill("乙酉"), "day": _pill("甲子")}
B = {"year": _pill("乙丑"), "day": _pill("甲寅")}


def test_sample_pair_selection():
    r = _result(A, B)
    sel = pair_scenes.select(r)
    codes = [s["code"] for s in sel["scenes"]]
    assert codes[:2] == ["yukhap", "wonjin"]
    assert len(codes) <= pair_scenes.MAX_SCENES
    assert "banhap" in codes  # 세 번째 슬롯
    assert sel["pattern_name"] == pair_scenes.PATTERN_NAMES["both"]


def test_deterministic_and_family_unique():
    r = _result(A, B)
    assert pair_scenes.select(r) == pair_scenes.select(r)
    fams = [s["family"] for s in pair_scenes.select(r)["scenes"]]
    assert len(fams) == len(set(fams))


def test_different_pairs_can_pick_different_candidates():
    picks = set()
    for a in "子丑寅卯辰巳午未申酉戌亥":
        for b in "子丑寅卯辰巳午未申酉戌亥":
            r = _result({"day": _pill("甲" + a)}, {"day": _pill("乙" + b)})
            for s in pair_scenes.select(r)["scenes"]:
                if s["code"] == "chung":
                    picks.add(s["theme"])
    assert len(picks) >= 2


def test_pattern_name_rules():
    none = _result({"day": _pill("甲子")}, {"day": _pill("乙寅")})
    assert pair_scenes.pattern_name(none) == pair_scenes.PATTERN_NAMES["none"]
    conn = _result({"day": _pill("甲子")}, {"day": _pill("乙丑")})
    assert pair_scenes.pattern_name(conn) == pair_scenes.PATTERN_NAMES["connection"]
    tens = _result({"day": _pill("甲子")}, {"day": _pill("乙午")})
    assert pair_scenes.pattern_name(tens) == pair_scenes.PATTERN_NAMES["tension"]
    same = _result({"day": _pill("甲子")}, {"day": _pill("乙子")})
    assert pair_scenes.pattern_name(same) == pair_scenes.PATTERN_NAMES["same_only"]
    trine = _result({"day": _pill("甲寅")}, {"day": _pill("乙戌")})  # 같은 삼합 그룹(생지+고지)
    assert pair_scenes.pattern_name(trine) == pair_scenes.PATTERN_NAMES["trine_only"]


def test_no_relation_no_scene_and_text():
    none = _result({"day": _pill("甲子")}, {"day": _pill("乙寅")})
    sel = pair_scenes.select(none)
    assert sel["scenes"] == []
    text = pair_scenes.build_scene_text(sel)
    assert "장면 후보가 없습니다" in text and sel["pattern_name"] in text


def test_gwimun_has_no_scene():
    r = _result({"day": _pill("甲寅")}, {"day": _pill("乙未")})  # 귀문(寅未)만 성립
    assert "gwimun" in pair_relations.branch_relations("寅", "未")
    assert all(s["code"] != "gwimun" for s in pair_scenes.select(r)["scenes"])


def test_relations_for_report_includes_scene_block():
    ca = {"pillars": A}
    cb = {"pillars": B}
    text = pair_relations.relations_for_report(ca, cb, "A", "B")
    assert "[핵심 관계" in text and "[편집 장면 후보와 패턴 별명" in text
    assert "Nähe mit leiser Reibung" in text


def test_prompt_updated():
    p = Path(__file__).resolve().parent.parent / "prompts" / "compatibility_report_prompt.json"
    t = json.loads(p.read_text(encoding="utf-8"))["messages"][0]["content"]
    assert "{{relations_facts}}" in t
    assert "[장면·개인화 규칙" in t and "Euer Muster:" in t
    assert "750~1000단어" in t and "750~1050" not in t
    assert "(~25%, 이 리포트에서 가장 긴 핵심 섹션)" in t


def test_scenes_only_for_displayed_relations():
    """사실 블록(보조 최대 4개)에 안 실린 관계의 장면이 나가면 안 된다 (실제 4기둥 쌍에서 발견된 버그)."""
    A4 = {k: {"hanja": v} for k, v in dict(year="甲子", month="癸酉", day="甲子", hour="甲戌").items()}
    B4 = {k: {"hanja": v} for k, v in dict(year="乙丑", month="丁亥", day="甲寅", hour="己巳").items()}
    text = pair_relations.relations_for_report({"pillars": A4}, {"pillars": B4}, "A", "B")
    facts, scenes = text.split("[편집 장면 후보와 패턴 별명")
    for code, label in pair_scenes.KO_LABEL.items():
        if f"· {label}" in scenes:
            ko = label.split("(")[0]
            assert ko in facts or code == "same_branch", (code, facts)
