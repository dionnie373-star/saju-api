"""두 사람의 사주 사이의 지지·천간 관계 계산 (궁합용).

설계 기준: Claude 문서 "Palja 두 사람 궁합 엔진 설계안 (2026-11-03)".

원칙
- 두 사람의 기둥을 교차 비교하고, 한 쌍이 여러 관계에 걸리면 모두 기록한다(하나로 합치지 않는다).
- 일지-일지를 핵심(primary), 나머지 기둥 조합은 보조(secondary)로 표시한다.
- 형은 두 글자 '부분 형'(hyung_partial)과 자묘형(hyung)만 기록한다. 삼형 완성/교차 자형은 판정하지 않는다.
- 반합은 왕지(子午卯酉)를 포함한 8쌍만, 생지+고지 4쌍은 same_trine_group으로 따로 기록한다.
- 방합·천간충·합화·용신 보완·'합이 형충을 푼다' 규칙은 적용하지 않는다.
- 같은 지지끼리는 same_branch로만 기록한다(길흉 판정 없음).
- 계산(이 모듈)과 독일어 표현(프롬프트)은 분리한다. 근거 수준은 CONFIDENCE에 둔다.
"""

from __future__ import annotations

POSITIONS = ("year", "month", "day", "hour")


def _pairs(*items):
    return tuple(frozenset(s) for s in items)


# ---- 지지 관계표 (한자 1글자 기준) ------------------------------------------
YUKHAP = _pairs("子丑", "寅亥", "卯戌", "辰酉", "巳申", "午未")
CHUNG = _pairs("子午", "丑未", "寅申", "卯酉", "辰戌", "巳亥")
PA = _pairs("子酉", "丑辰", "寅亥", "卯午", "巳申", "未戌")
HAE = _pairs("子未", "丑午", "寅巳", "卯辰", "申亥", "酉戌")
# 원진: 김만태 논문(정신문화연구 36권 3호)에서 6쌍 확인
WONJIN = _pairs("子未", "丑午", "寅酉", "卯申", "辰亥", "巳戌")
# 귀문관살: 현대 실무 기준(원진과 子·寅의 짝만 다름)
GWIMUN = _pairs("子酉", "丑午", "寅未", "卯申", "辰亥", "巳戌")
# 형: 삼형(寅巳申, 丑戌未)의 두 글자 부분 관계 + 자묘형
HYUNG_PARTIAL = _pairs("寅巳", "巳申", "寅申", "丑戌", "戌未", "丑未")
HYUNG = _pairs("子卯")
# 삼합: (생지, 왕지, 고지)
TRINES = (("申", "子", "辰"), ("亥", "卯", "未"), ("寅", "午", "戌"), ("巳", "酉", "丑"))
BANHAP_PRIMARY = _pairs("申子", "子辰", "亥卯", "卯未", "寅午", "午戌", "巳酉", "酉丑")
SAME_TRINE_GROUP = _pairs("申辰", "亥未", "寅戌", "巳丑")
# 천간합 (합화 오행은 판정하지 않으므로 기록하지 않는다)
STEM_HAP = _pairs("甲己", "乙庚", "丙辛", "丁壬", "戊癸")

# 근거 수준: 관계가 성립할 확률이 아니라 그 규칙의 문헌·전통상 근거 수준이다.
CONFIDENCE = {
    "yukhap": "traditional_rule",
    "chung": "traditional_rule",
    "pa": "traditional_rule",
    "hae": "traditional_rule",
    "banhap": "modern_practice",
    "same_trine_group": "modern_practice",
    "hyung_partial": "modern_practice",
    "hyung": "traditional_rule",
    "wonjin": "academic_paper",
    "gwimun": "modern_practice",
    "stem_hap": "traditional_rule",
}

# 프롬프트에서 쓰는 한국어 이름(독일어 표현은 프롬프트가 담당)
KO_NAME = {
    "yukhap": "육합",
    "chung": "충",
    "pa": "파",
    "hae": "해",
    "banhap": "반합(삼합의 부분 조합)",
    "same_trine_group": "같은 삼합 그룹",
    "hyung_partial": "부분 형",
    "hyung": "자묘형",
    "wonjin": "원진",
    "gwimun": "귀문관살",
    "stem_hap": "천간합",
}

_BRANCH_TABLES = (
    ("yukhap", YUKHAP),
    ("chung", CHUNG),
    ("pa", PA),
    ("hae", HAE),
    ("banhap", BANHAP_PRIMARY),
    ("same_trine_group", SAME_TRINE_GROUP),
    ("hyung_partial", HYUNG_PARTIAL),
    ("hyung", HYUNG),
    ("wonjin", WONJIN),
    ("gwimun", GWIMUN),
)


def branch_relations(a, b):
    """두 지지(한자 1글자) 사이에 성립하는 관계 코드 목록. 순서와 무관하다."""
    if not a or not b:
        return []
    if a == b:
        return []
    key = frozenset((a, b))
    return [code for code, table in _BRANCH_TABLES if key in table]


def stem_relations(a, b):
    if not a or not b or a == b:
        return []
    return ["stem_hap"] if frozenset((a, b)) in STEM_HAP else []


def pillar_chars(pillars):
    """calc_result["pillars"] -> {위치: (천간, 지지)}. 시주가 없으면(None) 해당 위치를 건너뛴다."""
    out = {}
    for pos in POSITIONS:
        p = (pillars or {}).get(pos)
        if not p:
            continue
        hanja = (p.get("hanja") or "").strip()
        if len(hanja) >= 2:
            out[pos] = (hanja[0], hanja[1])
    return out


def compare(pillars_a, pillars_b):
    """두 사람의 기둥을 교차 비교해 관계 목록을 돌려준다.

    반환: {"branch_pairs": [...], "stem_pairs": [...]}
    각 항목: person_a_position, person_b_position, a, b, relations(코드 목록),
             same_branch(bool, 지지 쌍에서만), priority("primary"|"secondary")
    관계가 하나도 없는 쌍(같은 지지 포함)은 same_branch 쌍만 남긴다.
    """
    ca, cb = pillar_chars(pillars_a), pillar_chars(pillars_b)
    branch_pairs, stem_pairs = [], []
    for pa, (sa, ba) in ca.items():
        for pb, (sb, bb) in cb.items():
            priority = "primary" if (pa, pb) == ("day", "day") else "secondary"
            rels = branch_relations(ba, bb)
            same = ba == bb
            if rels or same:
                branch_pairs.append({
                    "person_a_position": pa, "person_b_position": pb,
                    "a": ba, "b": bb, "relations": rels,
                    "same_branch": same, "priority": priority,
                })
            srels = stem_relations(sa, sb)
            if srels:
                stem_pairs.append({
                    "person_a_position": pa, "person_b_position": pb,
                    "a": sa, "b": sb, "relations": srels, "priority": priority,
                })
    return {"branch_pairs": branch_pairs, "stem_pairs": stem_pairs}


_POS_KO = {"year": "년지", "month": "월지", "day": "일지", "hour": "시지"}
_STEM_POS_KO = {"year": "년간", "month": "월간", "day": "일간", "hour": "시간"}

# 프롬프트에 넣는 보조 관계 개수 상한(리포트 길이·비용 제한). 핵심(일지-일지)은 항상 포함한다.
MAX_SECONDARY = 6


def _fmt_pair(item, name_a, name_b, stem=False):
    pos = _STEM_POS_KO if stem else _POS_KO
    label = " + ".join(KO_NAME[c] for c in item["relations"]) if item["relations"] else "같은 지지"
    if not stem and item.get("same_branch") and item["relations"]:
        label += " (같은 지지)"
    return (
        f"{name_a}의 {pos[item['person_a_position']]} {item['a']} ↔ "
        f"{name_b}의 {pos[item['person_b_position']]} {item['b']}: {label}"
    )


def _rank(item):
    # 관계가 있는 쌍을 먼저, 같은 지지만 있는 쌍은 뒤로. 그다음 월지·년지·시지 순.
    order = {"day": 0, "month": 1, "year": 2, "hour": 3}
    return (
        0 if item["relations"] else 1,
        order[item["person_a_position"]] + order[item["person_b_position"]],
    )


def select_displayed(result):
    """프롬프트에 실제로 실리는 쌍만 고른다: (핵심, 보조(최대 MAX_SECONDARY), 천간(최대 2)).

    장면 후보도 이 목록에 있는 관계에서만 고른다(사실 블록에 없는 관계의 장면이 나가지 않도록).
    """
    bp, sp = result["branch_pairs"], result["stem_pairs"]
    primary = [i for i in bp if i["priority"] == "primary"]
    secondary = sorted([i for i in bp if i["priority"] == "secondary" and i["relations"]], key=_rank)
    return primary, secondary[:MAX_SECONDARY], sp[:2]


def build_facts_text(result, name_a, name_b):
    """compare() 결과를 프롬프트용 한국어 사실 블록으로 만든다(한자는 내부용, 출력에는 쓰지 않도록 프롬프트가 지시)."""
    primary, secondary, stems = select_displayed(result)
    primary_lines = [_fmt_pair(i, name_a, name_b) for i in primary]
    secondary_lines = [_fmt_pair(i, name_a, name_b) for i in secondary]
    stem_lines = [_fmt_pair(i, name_a, name_b, stem=True) for i in stems]

    lines = []
    if primary_lines:
        lines.append("[핵심 관계 - 두 사람의 일지(태어난 날을 나타내는 지지) 사이]")
        lines += [f"- {l}" for l in primary_lines]
    else:
        lines.append("[핵심 관계 - 두 사람의 일지 사이] 특별히 성립하는 관계 없음 (이 사실은 'So haben wir gerechnet' 박스에서만 한 번 쓰고, 본문 섹션에서는 언급하지 마세요)")
    if secondary_lines:
        lines.append("[보조 관계 - 다른 기둥의 지지 사이 (중요도 낮음, 최대 %d개만 제공)]" % MAX_SECONDARY)
        lines += [f"- {l}" for l in secondary_lines]
    if stem_lines:
        lines.append("[천간 관계 - 합화(오행이 바뀜)는 판단하지 않음]")
        lines += [f"- {l}" for l in stem_lines]
    if not (primary_lines or secondary_lines or stem_lines):
        lines.append("두 사람 사이에서 이 리포트가 다룰 만한 지지·천간 관계가 확인되지 않았습니다.")
    return "\n".join(lines)


# 관계 계산이 실패했을 때 프롬프트에 넣는 문구 (리포트는 해당 섹션만 생략하고 정상 생성된다)
FALLBACK_FACTS = "(이번 리포트에서는 지지 관계 정보가 제공되지 않았습니다. 섹션 3-2는 쓰지 말고 건너뛰세요.)"


def relations_for_report(calc_result_a, calc_result_b, name_a, name_b, lang="de"):
    """파이프라인 진입점: 두 계산 결과에서 프롬프트용 사실 블록을 만든다. 실패하면 FALLBACK_FACTS(리포트는 해당 섹션만 생략하고 생성)."""
    try:
        result = compare(calc_result_a.get("pillars"), calc_result_b.get("pillars"))
        facts = build_facts_text(result, name_a, name_b)
    except Exception as e:  # 관계 계산 오류가 주문 처리 전체를 막으면 안 된다
        print(f"[pair_relations] 경고: 관계 계산 실패 - {e}")
        return FALLBACK_FACTS
    try:
        import pair_scenes
        primary, secondary, stems = select_displayed(result)
        shown = {"branch_pairs": primary + secondary, "stem_pairs": stems}
        facts += "\n\n" + pair_scenes.build_scene_text(pair_scenes.select(shown, lang))
    except Exception as e:  # 장면 선택 실패는 사실 블록만으로 리포트를 생성하게 둔다
        print(f"[pair_relations] 경고: 장면 후보 선택 실패 - {e}")
    return facts
