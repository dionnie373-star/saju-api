"""report_facts: 오행/축 등장 횟수, 최장 연속 구간, 전환점 등을 원본 계산 데이터에서

직접(코드로, 결정론적으로) 뽑아내는 모듈.

왜 필요한가: 유료/프리미엄 리포트에서 실제 Claude API로 반복해서 발견된 오류
(예: "화는 두 번만 등장"이라고 썼는데 실제로는 세 번, "8개 구간"을 "10개"라고 씀,
현재 나이와 시기 시작 나이를 혼동)는 전부 "숫자를 세는 일"과 "그걸 자연스러운
문장으로 쓰는 일"을 LLM 한 번의 생성 호출에 동시에 맡겨서 생긴 문제다. LLM은
장문을 쓰면서 자기가 쓴 숫자를 끝까지 정확히 추적하는 데 구조적으로 약하고,
2차 LLM 검증 패스를 붙여도 그 검증 자체가 같은 종류의 실수(오탐 포함)를 한다는
것도 실제 API 테스트로 확인됐다.

그래서 "세는 일"은 여기(파이썬 코드)에서 100% 정확하게 처리하고, Claude에게는
이미 계산된 숫자를 "주어진 사실"로 건네주고 자연스러운 문장으로 풀어쓰는 일만
맡긴다. 이렇게 하면 프롬프트가 아무리 길고 복잡한 리포트를 써도 오행 등장
횟수 같은 사실관계 오류 자체가 나올 수 없다(모델이 다시 셀 필요가 없으므로).
"""

from __future__ import annotations

_ELEMENT_NAMES_KR = ["목", "화", "토", "금", "수"]
_ELEMENT_HANJA = {"목": "木", "화": "火", "토": "土", "금": "金", "수": "水"}


def _period_elements(entry):
    """한 시기/달의 오행 조합(천간+지지)을 집합으로 반환. 같은 오행이 천간/지지에

    둘 다 있어도 "등장"은 1회로 센다(예: 33-42세 화/토 -> {화, 토}).
    """
    pillar = entry["pillar"]
    return {pillar["cheon_gan_element"], pillar["ji_ji_element"]}


def _compute_axis_runs(entries):
    """연속된 항목들을 같은 축(axis)끼리 묶어서 [{axis, start_index, end_index, count}] 반환."""
    runs = []
    for i, e in enumerate(entries):
        if runs and runs[-1]["axis"] == e["axis"]:
            runs[-1]["end_index"] = i
            runs[-1]["count"] += 1
        else:
            runs.append({"axis": e["axis"], "start_index": i, "end_index": i, "count": 1})
    return runs


def _compute_transitions(entries):
    """항목 i-1 -> i 사이에 축이 바뀌는 지점을 전부 나열."""
    transitions = []
    for i in range(1, len(entries)):
        if entries[i]["axis"] != entries[i - 1]["axis"]:
            transitions.append({"from_index": i - 1, "to_index": i})
    return transitions


def compute_daewoon_facts(daewoon):
    """run_calculation()이 반환한 daewoon(dict, entries 포함)에서 사실들을 계산.

    반환값의 각 시기는 daewoon["entries"]의 인덱스(0-based)로 참조된다.
    """
    entries = daewoon["entries"]

    element_occurrences = {el: [] for el in _ELEMENT_NAMES_KR}
    for e in entries:
        for el in _period_elements(e):
            element_occurrences[el].append({"start_age": e["start_age"], "end_age": e["end_age"]})

    axis_runs = _compute_axis_runs(entries)
    for run in axis_runs:
        run["start_age"] = entries[run["start_index"]]["start_age"]
        run["end_age"] = entries[run["end_index"]]["end_age"]
        run["years"] = run["count"] * 10

    longest_axis_run = max(axis_runs, key=lambda r: r["count"]) if axis_runs else None

    transitions = _compute_transitions(entries)
    for t in transitions:
        t["age"] = entries[t["to_index"]]["start_age"]
        t["from_axis"] = entries[t["from_index"]]["axis"]
        t["to_axis"] = entries[t["to_index"]]["axis"]

    current_index = next((i for i, e in enumerate(entries) if e.get("is_current")), None)

    return {
        "entries": entries,
        "element_occurrences": element_occurrences,
        "axis_runs": axis_runs,
        "longest_axis_run": longest_axis_run,
        "transitions": transitions,
        "current_age": daewoon.get("current_age"),
        "current_index": current_index,
        "total_periods": len(entries),
    }


def compute_monthly_facts(monthly, element_counts=None):
    """run_calculation()이 반환한 monthly(dict, months 포함)에서 사실들을 계산.

    element_counts가 주어지면(기본 사주의 오행 분포), 그 사람에게 없거나 적은
    오행이 몇 월에 등장하는지도 같이 표시한다.
    """
    months = monthly["months"]
    entries = [{"start_age": m["month"], "end_age": m["month"], "axis": m["axis"], "pillar": m["pillar"]} for m in months]

    element_occurrences = {el: [] for el in _ELEMENT_NAMES_KR}
    for m in months:
        for el in {m["pillar"]["cheon_gan_element"], m["pillar"]["ji_ji_element"]}:
            element_occurrences[el].append(m["month"])

    axis_runs = _compute_axis_runs(entries)
    for run in axis_runs:
        run["start_month"] = entries[run["start_index"]]["start_age"]
        run["end_month"] = entries[run["end_index"]]["end_age"]

    longest_axis_run = max(axis_runs, key=lambda r: r["count"]) if axis_runs else None
    transitions = _compute_transitions(entries)
    for t in transitions:
        t["month"] = entries[t["to_index"]]["start_age"]
        t["from_axis"] = entries[t["from_index"]]["axis"]
        t["to_axis"] = entries[t["to_index"]]["axis"]

    rare_elements = []
    if element_counts:
        for el, count in element_counts.items():
            if count == 0 and element_occurrences.get(el):
                rare_elements.append({"element": el, "months": element_occurrences[el]})

    return {
        "months": months,
        "element_occurrences": element_occurrences,
        "axis_runs": axis_runs,
        "longest_axis_run": longest_axis_run,
        "transitions": transitions,
        "rare_elements": rare_elements,
        "year": monthly.get("year"),
    }


def _fmt_periods_daewoon(periods):
    return ", ".join(f"{p['start_age']}~{p['end_age']}세" for p in periods)


def render_daewoon_facts_kr(facts):
    """프롬프트에 [계산된 사실]로 그대로 붙여넣을 한국어 텍스트 블록을 생성.

    여기 적힌 숫자는 전부 코드로 계산된 것이므로 100% 정확하다. Claude에게는
    "이 숫자를 다시 세지 말고 그대로 사용하라"고 지시해야 한다(프롬프트 쪽 책임).
    """
    lines = []
    lines.append(f"총 시기 개수: {facts['total_periods']}개")
    lines.append(f"현재 나이: {facts['current_age']}세 (시작 나이와 혼동 금지)")

    ci = facts["current_index"]
    if ci is not None:
        cur = facts["entries"][ci]
        lines.append(
            f"현재 시기: {cur['start_age']}~{cur['end_age']}세 (인덱스 {ci + 1}번째, 축={cur['axis']})"
        )

    lines.append("")
    lines.append("오행별 등장 횟수 (다시 세지 말고 이 숫자를 그대로 사용):")
    for el in _ELEMENT_NAMES_KR:
        periods = facts["element_occurrences"][el]
        if periods:
            lines.append(
                f"- {el}({_ELEMENT_HANJA[el]}): 정확히 {len(periods)}번 등장 - {_fmt_periods_daewoon(periods)}"
            )
        else:
            lines.append(f"- {el}({_ELEMENT_HANJA[el]}): 등장하지 않음(0번)")

    lines.append("")
    lines.append("시기별 오행 등장 순번 (서수 표현 '몇 번째/마지막/처음'은 반드시 이 표의 값만 사용, 직접 세지 말 것):")
    for e in facts["entries"]:
        parts = []
        for el in sorted(_period_elements(e), key=_ELEMENT_NAMES_KR.index):
            occ = facts["element_occurrences"][el]
            order = next(
                (i + 1 for i, p_ in enumerate(occ) if p_["start_age"] == e["start_age"]), None
            )
            mark = " (마지막 등장)" if order == len(occ) else (" (첫 등장)" if order == 1 else "")
            parts.append(f"{el}={order}번째/총 {len(occ)}번{mark}")
        lines.append(f"- {e['start_age']}~{e['end_age']}세: " + ", ".join(parts))

    lines.append("")
    lines.append("동일 축 연속 구간 (전부 나열, 다시 계산하지 말 것):")
    for run in facts["axis_runs"]:
        lines.append(
            f"- {run['axis']}: {run['start_age']}~{run['end_age']}세, {run['count']}개 시기, {run['years']}년"
        )
    lr = facts["longest_axis_run"]
    if lr:
        lines.append(
            f"=> 가장 길게 이어지는 동일 축: {lr['axis']} ({lr['start_age']}~{lr['end_age']}세, "
            f"{lr['count']}개 시기, {lr['years']}년)"
        )

    lines.append("")
    if facts["transitions"]:
        lines.append("축이 바뀌는 전환점 (전부 나열):")
        for t in facts["transitions"]:
            lines.append(f"- {t['age']}세: {t['from_axis']} → {t['to_axis']}")
    else:
        lines.append("축 전환점 없음(전체 시기가 같은 축)")

    return "\n".join(lines)


def _fmt_months(months):
    return ", ".join(f"{m}월" for m in months)


def render_monthly_facts_kr(facts):
    """프롬프트에 [계산된 사실]로 그대로 붙여넣을 한국어 텍스트 블록(유료 리포트용)."""
    lines = []
    lines.append(f"대상 연도: {facts['year']}년 (총 12개월)")

    lines.append("")
    lines.append("오행별 등장 횟수 (다시 세지 말고 이 숫자를 그대로 사용):")
    for el in _ELEMENT_NAMES_KR:
        months = facts["element_occurrences"][el]
        if months:
            lines.append(f"- {el}({_ELEMENT_HANJA[el]}): 정확히 {len(months)}개월 등장 - {_fmt_months(months)}")
        else:
            lines.append(f"- {el}({_ELEMENT_HANJA[el]}): 등장하지 않음(0개월)")

    if facts["rare_elements"]:
        lines.append("")
        lines.append("이 사람의 기본 사주에는 없는데 이 해에만 등장하는 오행(하이라이트 후보):")
        for r in facts["rare_elements"]:
            lines.append(f"- {r['element']}({_ELEMENT_HANJA[r['element']]}): {_fmt_months(r['months'])}에 등장")

    lines.append("")
    lines.append("동일 축 연속 구간 (전부 나열, 다시 계산하지 말 것):")
    for run in facts["axis_runs"]:
        lines.append(f"- {run['axis']}: {run['start_month']}월~{run['end_month']}월, {run['count']}개월 연속")
    lr = facts["longest_axis_run"]
    if lr:
        lines.append(
            f"=> 가장 길게 이어지는 동일 축: {lr['axis']} ({lr['start_month']}월~{lr['end_month']}월, "
            f"{lr['count']}개월 연속)"
        )

    lines.append("")
    if facts["transitions"]:
        lines.append("축이 바뀌는 전환점 (전부 나열):")
        for t in facts["transitions"]:
            lines.append(f"- {t['month']}월: {t['from_axis']} → {t['to_axis']}")
    else:
        lines.append("축 전환점 없음(전체 달이 같은 축)")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 월별 지지 관계 + 기운 등급 (2026-11-28 추가)
# 원칙: 등급은 AI가 정하지 않고 아래 규칙으로 계산한다. 규칙은 단순하고 투명하게 둔다.
#  - 오행 점수: 월간·월지 오행이 용신 +2, 희신(용신을 생하는 오행) +1, 기신(용신을 극하는 오행) -1.5, 그 외 0
#  - 관계 점수: 합(육합·반합·방합) +0.5, 충 -1, 형(부분형·자묘형·삼형 완성) -1, 해·파·원진 -0.5, 자형 -0.5
#  - 관계는 (월지 vs 원국 각 기둥 지지)와 (월지 vs 세운 지지)를 모두 본다.
#  - 인성(정인/편인) 십성이 천간·지지 모두인 달은 점수와 무관하게 '쉬어가는 달'로 분류한다.
# ---------------------------------------------------------------------------
import re as _re

_EL_GEN = {"목": "화", "화": "토", "토": "금", "금": "수", "수": "목"}   # 상생
_EL_OVR = {"목": "토", "토": "수", "수": "화", "화": "금", "금": "목"}   # 상극
_STEMS = "甲乙丙丁戊己庚辛壬癸"
_BRANCHES = "子丑寅卯辰巳午未申酉戌亥"
_BANGHAP = ({"寅", "卯", "辰"}, {"巳", "午", "未"}, {"申", "酉", "戌"}, {"亥", "子", "丑"})
_SAMHYUNG = ({"寅", "巳", "申"}, {"丑", "戌", "未"})
_JAHYUNG = {"辰", "午", "酉", "亥"}
_POS_KR = {"year": "년지", "month": "월지", "day": "일지", "hour": "시지"}
_REL_SCORE = {"yukhap": 0.5, "banhap": 0.5, "bangap": 0.5, "chung": -1.0, "hyung": -1.0,
              "hyung_partial": -1.0, "samhyung": -1.0, "hae": -0.5, "pa": -0.5, "wonjin": -0.5, "jahyung": -0.5}
_REL_KO = {"yukhap": "육합", "banhap": "반합", "bangap": "방합(삼회)", "chung": "충", "hyung": "자묘형",
           "hyung_partial": "부분 형", "samhyung": "삼형 완성", "hae": "해", "pa": "파", "wonjin": "원진", "jahyung": "자형"}
GRADE_DE = {"up": "Rückenwind", "mid": "Ausgewogen", "hard": "Herausfordernd", "rest": "Ruhiger"}
GRADE_KO = {"up": "힘이 실리는 달", "mid": "보통의 달", "hard": "고민이 생기는 달", "rest": "쉬어가는 달"}


def _yongsin_element(yongsin_text):
    m = _re.search(r"용신=([목화토금수])", yongsin_text or "")
    return m.group(1) if m else None


def _year_pillar_hanja(year):
    return _STEMS[(year - 4) % 10] + _BRANCHES[(year - 4) % 12]


def compute_monthly_grades(calc_result):
    """calc_result(run_calculation 결과, monthly 포함) -> 월별 관계·점수·등급 리스트. 실패 시 [] ."""
    from pair_relations import branch_relations, pillar_chars
    monthly = calc_result.get("monthly") or {}
    months = monthly.get("months") or []
    year = monthly.get("year")
    yong = _yongsin_element(calc_result.get("yongsin"))
    if not months or not year or not yong:
        return []
    hee = next((k for k, v in _EL_GEN.items() if v == yong), None)
    gi = next((k for k, v in _EL_OVR.items() if v == yong), None)
    natal = pillar_chars(calc_result.get("pillars"))
    natal_branches = {pos: b for pos, (_, b) in natal.items()}
    se_hanja = _year_pillar_hanja(year)
    se_branch = se_hanja[1]

    def el_score(el):
        return 2.0 if el == yong else 1.0 if el == hee else -1.5 if el == gi else 0.0

    out = []
    for m in months:
        hanja = m["pillar"]["hanja"]
        mb = hanja[1]
        rels = []  # (코드, 대상 설명)
        targets = [(f"원국 {_POS_KR[p]} {b}", b) for p, b in natal_branches.items()] + [(f"세운 {se_branch}", se_branch)]
        for label, tb in targets:
            if tb == mb:
                if mb in _JAHYUNG:
                    rels.append(("jahyung", label))
                continue
            for code in branch_relations(mb, tb):
                if code in _REL_SCORE:
                    rels.append((code, label))
        pool = set(natal_branches.values()) | {se_branch}
        for g in _BANGHAP:
            if mb in g and g <= (pool | {mb}) and len(g & pool) >= 2:
                rels.append(("bangap", "·".join(sorted(g))))
        for g in _SAMHYUNG:
            if mb in g and g <= (pool | {mb}) and len(g & pool) >= 2:
                rels.append(("samhyung", "·".join(sorted(g))))
        # 같은 코드·같은 대상 중복 제거
        seen, uniq = set(), []
        for r in rels:
            if r not in seen:
                seen.add(r); uniq.append(r)
        score = el_score(m["pillar"]["cheon_gan_element"]) + el_score(m["pillar"]["ji_ji_element"])
        # 같은 대상과 여러 관계가 겹치면(예: 子未 해+원진) 가장 영향이 큰 것 하나만 점수에 반영한다.
        by_target = {}
        for c, t in uniq:
            if t not in by_target or abs(_REL_SCORE[c]) > abs(_REL_SCORE[by_target[t]]):
                by_target[t] = c
        rel_score = sum(_REL_SCORE[c] for c in by_target.values())
        score += max(-3.0, min(1.5, rel_score))
        sh = m["shipsin"]
        if sh["cheon_gan"] in ("정인", "편인") and sh["ji_ji"] in ("정인", "편인"):
            grade = "rest"
        elif score >= 2.0:
            grade = "up"
        elif score <= -1.5:
            grade = "hard"
        else:
            grade = "mid"
        volatile = sum(1 for c, _ in uniq if c in ("chung", "hyung", "hyung_partial", "samhyung")) >= 2
        out.append({"month": m["month"], "pillar": hanja, "relations": uniq, "score": round(score, 1), "grade": grade, "volatile": volatile})
    return out


def render_monthly_grades_kr(grades, year):
    if not grades:
        return ""
    lines = ["", f"[월별 지지 관계와 기운 등급 — 계산 결과, 다시 정하지 말고 그대로 사용 (세운 {_year_pillar_hanja(year)})]"]
    for g in grades:
        rel = "; ".join(f"{_REL_KO[c]}({t})" for c, t in g["relations"]) or "특별한 관계 없음"
        lines.append(f"- {g['month']}월 {g['pillar']}: 등급={GRADE_KO[g['grade']]}({GRADE_DE[g['grade']]}), 점수 {g['score']}{', 변동 큰 달(충·형 2개 이상: 좋다/나쁘다보다 \'움직임이 큰 달\'로 서술)' if g.get('volatile') else ''}, 관계: {rel}")
    lines.append("등급 해석 규칙: 힘이 실리는 달=순풍, 보통=균형, 고민이 생기는 달=조정할 일이 두드러짐(나쁜 달로 쓰지 말 것), 쉬어가는 달=정리·재점검. 충·형·해가 있는 달은 그 관계를 월별 서술에 구체적으로 반영하되 사건을 단정하지 말 것.")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 절기 기준 월 경계 (사주 월은 양력 1일~말일이 아니라 절입 시각으로 바뀐다)
# ---------------------------------------------------------------------------
_JEOL_MONTHS = ["소한", "입춘", "경칩", "청명", "입하", "망종", "소서", "입추", "백로", "한로", "입동", "대설"]


_LANG_DISPLAY_TZ = {"de": "Europe/Berlin", "es": "Europe/Madrid", "fr": "Europe/Paris", "en": "Europe/London"}


def solar_month_boundaries(year, lang="de"):
    """year의 1~12월(사주 월 丑·寅·…·子) 시작/끝 절입 시각을 독자 언어권의 현지 시간대로 돌려준다.
    1월 = 소한(丑월), 2월 = 입춘(寅월) … 12월 = 대설(子월). 12월의 끝은 다음 해 소한.
    절입은 하나의 천문 순간이며(월주 계산은 이 순간 기준, 시간대 무관), 여기서 바꾸는 것은 표시 날짜뿐이다.
    반환: [{"month", "name", "start": datetime(현지 naive), "end": datetime(현지 naive)}], tz 이름
    """
    from zoneinfo import ZoneInfo
    from korean_saju.calendar.solar_term_calculator import SolarTermCalculator as _C
    tz = ZoneInfo(_LANG_DISPLAY_TZ.get(lang, "Europe/Berlin"))
    cur = {t.name: t.datetime for t in _C.terms_for_year(year)}
    nxt = {t.name: t.datetime for t in _C.terms_for_year(year + 1)}
    loc = lambda dt: dt.astimezone(tz).replace(tzinfo=None)
    out = []
    for i, name in enumerate(_JEOL_MONTHS):
        start = loc(cur[name])
        end = loc(cur[_JEOL_MONTHS[i + 1]]) if i < 11 else loc(nxt["소한"])
        out.append({"month": i + 1, "name": name, "start": start, "end": end})
    return out


# 독일어 절기 이름(고정). AI가 한국어 이름을 스스로 번역하면 입춘을 "Lichtbeginn"처럼 지어내는 일이 실제로 발생했다.
_TERM_DE = {
    "소한": "Kleine Kälte", "입춘": "Frühlingsbeginn", "경칩": "Erwachen der Insekten", "청명": "Klare Helle",
    "입하": "Sommerbeginn", "망종": "Korn in Ähren", "소서": "Kleine Hitze", "입추": "Herbstbeginn",
    "백로": "Weißer Tau", "한로": "Kalter Tau", "입동": "Winterbeginn", "대설": "Großer Schnee",
}


def render_solar_boundaries_kr(year, lang="de"):
    tzname = _LANG_DISPLAY_TZ.get(lang, "Europe/Berlin")
    b = solar_month_boundaries(year, lang)
    lines = ["", f"[절기(Solartermine) 기준 사주 월 경계 — 계산 결과, 이 날짜를 그대로 사용 (독자 현지 시간대 {tzname} 기준)]"]
    if lang == "de":
        lines.append("절기 이름은 괄호 안의 독일어 이름만 그대로 쓰고, 스스로 번역하거나 바꾸지 마세요.")
    for x in b:
        de = _TERM_DE.get(x["name"]) if lang == "de" else None
        nm = f"{x['name']}({de})" if de else x["name"]
        lines.append(f"- {x['month']}월: {nm} {x['start']:%m월 %d일 %H:%M} ~ {x['end']:%m월 %d일 %H:%M}")
    lines.append(f"참고: 1월(丑월)은 {year}년 입춘 이전이라 세운으로는 전년도에 속한다. {year}년 세운은 입춘({b[1]['start']:%m월 %d일})부터 시작한다.")
    return "\n".join(lines)
