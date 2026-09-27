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
