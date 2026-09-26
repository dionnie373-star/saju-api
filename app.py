"""
saju-api: 사주(四柱) 계산 웹 API

POST /calculate
{
  "name": "홍길동",              // optional
  "birth_datetime": "1984-09-27T20:00:00",  // 필수, 양력 기준, 시간 모름이면 12:00 사용 권장
  "birth_city": "Berlin",         // longitude 대신 도시 이름으로도 가능 (서버가 자동으로 경도를 찾음)
  "longitude": 126.9784,          // birth_city 대신 직접 경도를 줄 수도 있음
  "yaja_si_separated": true,      // 선택, 기본 true (야자시/조자시 구분)
  "target_year": 2027,            // 선택, 특정 연도 세운(년주)까지 함께 계산하고 싶을 때
  "monthly_year": 2027,           // 선택, 유료 리포트용: 이 해 1~12월 월별 흐름(월주+십성+축) 계산
  "gender": "female",             // 선택, 프리미엄 리포트용: 대운 계산에 필요 ("male"/"female" 또는 "남"/"여")
  "daewoon_count": 8              // 선택, 프리미엄 리포트용: 대운 몇 단위(10년)까지 계산할지 (기본 8 = 80년치)
}

longitude와 birth_city 중 하나만 있으면 됩니다. birth_city가 오면 서버가
자동으로 경도를 찾아서 계산합니다(자주 쓰이는 도시는 내장 표에서 즉시 찾고,
표에 없는 도시는 무료 지오코딩 서비스로 조회하며, 그마저 실패하면 독일
중앙 경도를 기본값으로 사용합니다).

응답에는 사주 4주(년/월/일/시), 오행 개수, 그리고 AI 프롬프트에 바로 넣을 수 있는
"compact" 텍스트 요약이 포함됩니다.
"""

import os
import re
import sys
from datetime import datetime, date, time as dtime

from flask import Flask, request, jsonify

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from korean_saju import (  # noqa: E402
    Daewoon,
    Gender,
    IlganStrengthAnalyzer,
    Saju,
    SajuAnalysis,
    ShipsinCalculator,
    load_bundled_data,
)

app = Flask(__name__)

_lunar, _solar_terms = load_bundled_data()

ELEMENT_HANJA = {
    "목": "木", "화": "火", "토": "土", "금": "金", "수": "水",
}

# 십성 -> 유료 리포트용 "축(재물/관계/직업/총운)" 매핑.
# 관성(정관/편관)은 전통적으로 배우자를 상징하지만, 성별을 단정하지 않기 위해
# "관계에서의 책임·구조"로 중립적으로 재해석해 관계운 축에 배정한다.
SHIPSIN_AXIS = {
    "정재": "재물운", "편재": "재물운",
    "정관": "관계운", "편관": "관계운",
    "식신": "직업운", "상관": "직업운",
    "정인": "총운", "편인": "총운",
    "비견": "총운", "겁재": "총운",
}
# 우선순위: 그 달에 여러 축이 겹치면 이 순서대로 하나를 대표 축으로 뽑는다
# (재물/관계/직업처럼 구체적인 축을 총운보다 우선한다).
AXIS_PRIORITY = ["재물운", "관계운", "직업운", "총운"]

# 자주 나올 도시는 네트워크 호출 없이 즉시 처리 (독일/오스트리아/스위스 주요 도시 + 한국 주요 도시)
KNOWN_CITY_LONGITUDE = {
    "berlin": 13.4050, "hamburg": 9.9937, "münchen": 11.5820, "munich": 11.5820,
    "köln": 6.9603, "koeln": 6.9603, "cologne": 6.9603, "frankfurt": 8.6821,
    "frankfurt am main": 8.6821, "stuttgart": 9.1829, "düsseldorf": 6.7735,
    "duesseldorf": 6.7735, "leipzig": 12.3731, "dortmund": 7.4653,
    "essen": 7.0116, "bremen": 8.8017, "dresden": 13.7373, "hannover": 9.7320,
    "hanover": 9.7320, "nürnberg": 11.0767, "nuernberg": 11.0767,
    "nuremberg": 11.0767, "duisburg": 6.7623, "bochum": 7.2160,
    "wuppertal": 7.1500, "bielefeld": 8.5325, "bonn": 7.0982,
    "münster": 7.6261, "muenster": 7.6261, "karlsruhe": 8.4037,
    "mannheim": 8.4660, "augsburg": 10.8978, "wiesbaden": 8.2412,
    "mönchengladbach": 6.4428, "gelsenkirchen": 7.1013,
    "braunschweig": 10.5268, "chemnitz": 12.9214, "kiel": 10.1228,
    "aachen": 6.0839, "wien": 16.3738, "vienna": 16.3738,
    "salzburg": 13.0550, "graz": 15.4395, "innsbruck": 11.4041,
    "zürich": 8.5417, "zuerich": 8.5417, "zurich": 8.5417,
    "bern": 7.4474, "basel": 7.5886, "genf": 6.1432, "geneva": 6.1432,
    "서울": 126.9784, "seoul": 126.9784, "부산": 129.0756, "busan": 129.0756,
    "인천": 126.7052, "incheon": 126.7052, "대구": 128.6014, "daegu": 128.6014,
}

DEFAULT_LONGITUDE = 10.4515  # 독일 중앙 부근 경도 (도시를 못 찾았을 때의 최종 대비값)


def _lookup_longitude(city_name):
    """도시 이름 -> 경도. 1) 내장 표 2) 무료 지오코딩 API 3) 기본값 순으로 시도."""
    key = city_name.strip().lower()
    if key in KNOWN_CITY_LONGITUDE:
        return KNOWN_CITY_LONGITUDE[key], "known_city"

    try:
        import urllib.parse
        import urllib.request
        import json as _json

        url = (
            "https://geocoding-api.open-meteo.com/v1/search?name="
            + urllib.parse.quote(city_name)
            + "&count=1&format=json"
        )
        req = urllib.request.Request(url, headers={"User-Agent": "saju-api/1.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = _json.loads(resp.read().decode("utf-8"))
        results = data.get("results") or []
        if results:
            return float(results[0]["longitude"]), "geocoded"
    except Exception:
        pass

    return DEFAULT_LONGITUDE, "default_fallback"


def _parse_flexible_date(s):
    """'1984-09-27', '1984. 9. 27', '27.09.1984' 등 다양한 형식의 날짜 문자열을 date로 변환."""
    s = s.strip()
    nums = [int(n) for n in re.findall(r"\d+", s)]
    if len(nums) < 3:
        raise ValueError(f"날짜를 해석할 수 없습니다: {s}")

    year = None
    year_idx = None
    for i, n in enumerate(nums):
        if n >= 1000:
            year = n
            year_idx = i
            break

    if year is None:
        # 4자리 연도를 못 찾은 경우, 순서를 연/월/일로 가정하고 2자리 연도는 2000년대로 취급
        year, month, day = nums[0], nums[1], nums[2]
        if year < 100:
            year += 2000
    else:
        rest = nums[:year_idx] + nums[year_idx + 1:]
        if len(rest) < 2:
            raise ValueError(f"날짜를 해석할 수 없습니다: {s}")
        if year_idx == 0:
            # YYYY-MM-DD / 1984. 9. 27 형식 (연도가 맨 앞)
            month, day = rest[0], rest[1]
        else:
            # DD.MM.YYYY 형식 (독일식, 연도가 맨 뒤)
            day, month = rest[0], rest[1]

    return date(year, month, day)


def _parse_flexible_time(s):
    """'20:00:00', '오후 8:00:00', '8:00 PM' 등을 time으로 변환. 비어있으면 정오(12:00)."""
    if not s or not s.strip():
        return dtime(12, 0, 0)

    s = s.strip()
    is_pm = ("오후" in s) or bool(re.search(r"\bPM\b", s, re.IGNORECASE))
    is_am = ("오전" in s) or bool(re.search(r"\bAM\b", s, re.IGNORECASE))

    nums = [int(n) for n in re.findall(r"\d+", s)]
    if not nums:
        raise ValueError(f"시간을 해석할 수 없습니다: {s}")

    hour = nums[0]
    minute = nums[1] if len(nums) > 1 else 0
    second = nums[2] if len(nums) > 2 else 0

    if is_pm and hour < 12:
        hour += 12
    if is_am and hour == 12:
        hour = 0

    return dtime(hour % 24, minute, second)


def _parse_flexible_datetime(date_str, time_str=None):
    d = _parse_flexible_date(date_str)
    t = _parse_flexible_time(time_str)
    return datetime.combine(d, t)


def _resolve_birth_datetime(payload):
    """birth_date(+birth_time) 또는 birth_datetime(ISO 우선, 실패 시 유연 파싱)으로부터 datetime을 얻는다."""
    birth_date_str = payload.get("birth_date")
    birth_time_str = payload.get("birth_time")
    birth_datetime_str = payload.get("birth_datetime")

    if birth_date_str:
        return _parse_flexible_datetime(birth_date_str, birth_time_str)

    if birth_datetime_str:
        try:
            return datetime.fromisoformat(birth_datetime_str)
        except ValueError:
            # 'T' 구분자로만 나눈다 (날짜 자체에 공백이 들어있는 로캘이 있어 공백 기준 분리는 쓰지 않음)
            if "T" in birth_datetime_str:
                date_part, time_part = birth_datetime_str.split("T", 1)
            else:
                date_part, time_part = birth_datetime_str, None
            return _parse_flexible_datetime(date_part, time_part)

    raise ValueError("birth_datetime 또는 birth_date 값이 필요합니다.")


def _pillar_dict(pillar):
    return {
        "hanja": pillar.hanja,
        "hangul": pillar.hangul,
        "cheon_gan_element": pillar.cheon_gan.o_haeng.hangul,
        "ji_ji_element": pillar.ji_ji.o_haeng.hangul,
    }


def _count_elements(saju):
    counts = {"목": 0, "화": 0, "토": 0, "금": 0, "수": 0}
    for pillar in [saju.year_pillar, saju.month_pillar, saju.day_pillar, saju.hour_pillar]:
        counts[pillar.cheon_gan.o_haeng.hangul] += 1
        counts[pillar.ji_ji.o_haeng.hangul] += 1
    return counts


MONTH_NAMES_KO = [
    "1월", "2월", "3월", "4월", "5월", "6월",
    "7월", "8월", "9월", "10월", "11월", "12월",
]


def _compute_monthly_forecast(day_stem, target_year, solar_terms, longitude, yaja_si_separated=True):
    """target_year 1~12월의 월주(月柱)와 그 달의 십성(일간 기준)을 계산.

    월주는 태어난 사람의 사주와 무관하게 절기 기준으로 정해지므로,
    각 달의 15일 정오를 기준 시점으로 잡아 월주만 뽑아내면 된다
    (유료 리포트의 '이번 해 월별 흐름'용 데이터).
    십성은 이 사람의 일간(day_stem)을 기준으로 계산해서,
    그 달이 재물운/관계운/직업운/총운 중 어디에 해당하는지 축을 매긴다.
    """
    months = []
    for m in range(1, 13):
        probe = datetime(target_year, m, 15, 12, 0)
        probe_saju = Saju.from_birth(
            kst_moment=probe,
            solar_terms=solar_terms,
            longitude=longitude,
            yaja_si_separated=bool(yaja_si_separated),
        )
        mp = probe_saju.month_pillar
        stem_shipsin = ShipsinCalculator.for_cheon_gan(day_stem, mp.cheon_gan)
        branch_shipsin = ShipsinCalculator.for_ji_ji(day_stem, mp.ji_ji)

        axes_present = {
            SHIPSIN_AXIS[s.hangul]
            for s in (stem_shipsin, branch_shipsin)
            if s.hangul in SHIPSIN_AXIS
        }
        primary_axis = next((a for a in AXIS_PRIORITY if a in axes_present), "총운")

        months.append({
            "month": m,
            "month_name": MONTH_NAMES_KO[m - 1],
            "pillar": {
                "hanja": mp.hanja,
                "hangul": mp.hangul,
                "cheon_gan_element": mp.cheon_gan.o_haeng.hangul,
                "ji_ji_element": mp.ji_ji.o_haeng.hangul,
            },
            "shipsin": {
                "cheon_gan": stem_shipsin.hangul,
                "ji_ji": branch_shipsin.hangul,
            },
            "axis": primary_axis,
        })
    return months


def _build_monthly_compact(target_year, months):
    """월별 데이터를 AI 프롬프트에 바로 넣을 수 있는 한 줄짜리 텍스트로 압축."""
    lines = [f"{target_year}년 월별 흐름 (일간 기준 십성으로 계산):"]
    for mo in months:
        p = mo["pillar"]
        el_str = f"{p['cheon_gan_element']}{ELEMENT_HANJA[p['cheon_gan_element']]}/{p['ji_ji_element']}{ELEMENT_HANJA[p['ji_ji_element']]}"
        lines.append(
            f"{mo['month_name']}: {p['hanja']}({p['hangul']}) 오행={el_str} "
            f"십성(천간/지지)={mo['shipsin']['cheon_gan']}/{mo['shipsin']['ji_ji']} "
            f"| 이 달의 축={mo['axis']}"
        )
    return " | ".join(lines)


def _resolve_gender(gender_str):
    key = (gender_str or "").strip().lower()
    if key in ("male", "m", "남", "남성", "남자"):
        return Gender.MALE
    if key in ("female", "f", "여", "여성", "여자"):
        return Gender.FEMALE
    raise ValueError("gender 값은 'male' 또는 'female'(또는 '남'/'여')이어야 합니다.")


def _compute_daewoon_forecast(saju, day_stem, gender_str, solar_terms, count=8):
    """프리미엄(대운) 리포트용: 10년 단위 대운 시퀀스 + 각 시기의 십성/축 계산.

    대운의 진행 방향(순행/역행)은 연간(年干)의 음양과 성별의 조합으로 정해지므로
    (양남·음녀=순행, 음남·양녀=역행), 대운 계산에는 성별이 반드시 필요하다.
    각 대운 시기의 십성은 이 사람의 일간(day_stem) 기준으로 계산해서
    재물운/관계운/직업운/총운 중 어느 축이 두드러지는 시기인지 매긴다.
    """
    gender = _resolve_gender(gender_str)
    daewoon = Daewoon.compute(saju=saju, gender=gender, solar_terms=solar_terms, count=count)

    birth_date = saju.kst_moment.date()
    today = date.today()
    current_age = today.year - birth_date.year - (
        (today.month, today.day) < (birth_date.month, birth_date.day)
    )

    entries = []
    for i, entry in enumerate(daewoon.entries):
        stem_shipsin = ShipsinCalculator.for_cheon_gan(day_stem, entry.gan_ji.cheon_gan)
        branch_shipsin = ShipsinCalculator.for_ji_ji(day_stem, entry.gan_ji.ji_ji)
        axes_present = {
            SHIPSIN_AXIS[s.hangul]
            for s in (stem_shipsin, branch_shipsin)
            if s.hangul in SHIPSIN_AXIS
        }
        primary_axis = next((a for a in AXIS_PRIORITY if a in axes_present), "총운")
        end_age = entry.start_age + 9
        entries.append({
            "index": i + 1,
            "start_age": entry.start_age,
            "end_age": end_age,
            "start_year": birth_date.year + entry.start_age,
            "pillar": {
                "hanja": entry.gan_ji.hanja,
                "hangul": entry.gan_ji.hangul,
                "cheon_gan_element": entry.gan_ji.cheon_gan.o_haeng.hangul,
                "ji_ji_element": entry.gan_ji.ji_ji.o_haeng.hangul,
            },
            "shipsin": {
                "cheon_gan": stem_shipsin.hangul,
                "ji_ji": branch_shipsin.hangul,
            },
            "axis": primary_axis,
            "is_current": entry.start_age <= current_age <= end_age,
        })

    return {
        "gender": gender.value,
        "forward": daewoon.forward,
        "current_age": current_age,
        "entries": entries,
    }


def _build_daewoon_compact(daewoon_out):
    direction = "순행" if daewoon_out["forward"] else "역행"
    lines = [f"대운 방향: {direction} | 현재 만 나이: {daewoon_out['current_age']}세"]
    for e in daewoon_out["entries"]:
        marker = " ← 현재 대운" if e["is_current"] else ""
        p = e["pillar"]
        el_str = f"{p['cheon_gan_element']}{ELEMENT_HANJA[p['cheon_gan_element']]}/{p['ji_ji_element']}{ELEMENT_HANJA[p['ji_ji_element']]}"
        lines.append(
            f"{e['start_age']}~{e['end_age']}세({e['start_year']}년~): "
            f"{p['hanja']}({p['hangul']}) 오행={el_str} "
            f"십성(천간/지지)={e['shipsin']['cheon_gan']}/{e['shipsin']['ji_ji']} "
            f"| 이 시기의 축={e['axis']}{marker}"
        )
    return " | ".join(lines)


def _build_compact(name, saju, counts, yearly=None, ilgan_strength=None, jeonggyeok=None, yongsin=None):
    pillars_str = (
        f"년주 {saju.year_pillar.hanja}({saju.year_pillar.hangul}) / "
        f"월주 {saju.month_pillar.hanja}({saju.month_pillar.hangul}) / "
        f"일주 {saju.day_pillar.hanja}({saju.day_pillar.hangul}) / "
        f"시주 {saju.hour_pillar.hanja}({saju.hour_pillar.hangul})"
    )
    counts_str = ", ".join(f"{el}{ELEMENT_HANJA[el]} {cnt}개" for el, cnt in counts.items())
    max_el = max(counts, key=counts.get)
    min_els = [el for el, cnt in counts.items() if cnt == min(counts.values())]
    day_stem_el = saju.day_stem.o_haeng.hangul
    lines = [
        f"이름: {name or '(미입력)'}",
        f"사주: {pillars_str}",
        f"오행 분포: {counts_str}",
        f"가장 많은 오행: {max_el}({ELEMENT_HANJA[max_el]})",
        f"가장 적은/없는 오행: {', '.join(f'{e}({ELEMENT_HANJA[e]})' for e in min_els)}",
        f"일간(본인 자신): {saju.day_stem.hangul}({saju.day_stem.hanja}), 오행 {day_stem_el}({ELEMENT_HANJA[day_stem_el]})",
    ]
    if ilgan_strength is not None:
        lines.append(
            f"일간 강약: {ilgan_strength.level.hangul}({ilgan_strength.level.hanja}) "
            f"[점수 {ilgan_strength.total:.1f}/10] — {ilgan_strength.reason}"
        )
    if jeonggyeok is not None:
        lines.append(f"격국: {jeonggyeok}")
    if yongsin is not None:
        lines.append(f"{yongsin} (이 사람에게 필요한 기운) — 근거: {yongsin.reason}")
    for y in (yearly or []):
        lines.append(
            f"{y['year']}년 세운: {y['pillar'].hanja}({y['pillar'].hangul}), "
            f"천간 오행 {y['pillar'].cheon_gan.o_haeng.hangul}({ELEMENT_HANJA[y['pillar'].cheon_gan.o_haeng.hangul]})"
        )
    # Make.com 같은 자동화 도구에서 이 문자열을 JSON 안에 그대로 끼워 넣을 때
    # 실제 줄바꿈 문자가 있으면 JSON이 깨지므로, 줄바꿈 대신 " | "로 구분한다.
    return " | ".join(lines)


@app.route("/", methods=["GET"])
def health():
    return jsonify({"ok": True, "service": "saju-api", "status": "running"})


@app.route("/calculate", methods=["POST"])
def calculate():
    try:
        payload = request.get_json(force=True, silent=False) or {}
    except Exception:
        return jsonify({"ok": False, "error": "잘못된 JSON 형식입니다."}), 400

    name = payload.get("name")
    longitude = payload.get("longitude")
    birth_city = payload.get("birth_city")
    yaja_si_separated = payload.get("yaja_si_separated", True)
    target_year = payload.get("target_year")

    if longitude is None and not birth_city:
        return jsonify({"ok": False, "error": "longitude(경도) 또는 birth_city(도시명) 중 하나가 필요합니다."}), 400

    try:
        birth_dt = _resolve_birth_datetime(payload)
    except Exception as e:
        return jsonify({"ok": False, "error": f"생년월일시를 해석할 수 없습니다: {e}"}), 400

    longitude_source = "provided"
    if longitude is not None:
        try:
            longitude = float(longitude)
        except (TypeError, ValueError):
            return jsonify({"ok": False, "error": "longitude 값은 숫자여야 합니다."}), 400
    else:
        longitude, longitude_source = _lookup_longitude(birth_city)

    try:
        saju = Saju.from_birth(
            kst_moment=birth_dt,
            solar_terms=_solar_terms,
            longitude=longitude,
            yaja_si_separated=bool(yaja_si_separated),
        )
        analysis = SajuAnalysis(saju)
    except Exception as e:
        return jsonify({"ok": False, "error": f"사주 계산 중 오류가 발생했습니다: {e}"}), 500

    counts = _count_elements(saju)
    ilgan_strength = IlganStrengthAnalyzer.analyze(saju)
    jeonggyeok = getattr(analysis, "jeonggyeok", None)
    yongsin = getattr(analysis, "yongsin", None)

    target_years = payload.get("target_years")
    if not target_years and target_year:
        target_years = [target_year]

    monthly_year = payload.get("monthly_year")  # 유료 리포트용: 이 해의 12개월 흐름 계산
    gender = payload.get("gender")  # 프리미엄 리포트용: 대운 계산에 필요
    daewoon_count = payload.get("daewoon_count", 8)  # 프리미엄 리포트용: 대운 몇 단위(10년)까지

    yearly = []
    yearly_out = {}
    if target_years:
        for y in target_years:
            try:
                y = int(y)
                year_moment = datetime(y, 7, 1, 12, 0)
                year_saju = Saju.from_birth(
                    kst_moment=year_moment,
                    solar_terms=_solar_terms,
                    longitude=longitude,
                    yaja_si_separated=bool(yaja_si_separated),
                )
                yearly.append({"year": y, "pillar": year_saju.year_pillar})
                yearly_out[str(y)] = {"year": y, "year_pillar": _pillar_dict(year_saju.year_pillar)}
            except Exception as e:
                yearly_out[str(y)] = {"year": y, "error": str(e)}

    monthly_out = None
    monthly_compact = None
    if monthly_year:
        try:
            monthly_year = int(monthly_year)
            months = _compute_monthly_forecast(
                day_stem=saju.day_stem,
                target_year=monthly_year,
                solar_terms=_solar_terms,
                longitude=longitude,
                yaja_si_separated=bool(yaja_si_separated),
            )
            monthly_out = {"year": monthly_year, "months": months}
            monthly_compact = _build_monthly_compact(monthly_year, months)
        except Exception as e:
            monthly_out = {"year": monthly_year, "error": str(e)}

    daewoon_out = None
    daewoon_compact = None
    if gender:
        try:
            daewoon_out = _compute_daewoon_forecast(
                saju=saju,
                day_stem=saju.day_stem,
                gender_str=gender,
                solar_terms=_solar_terms,
                count=int(daewoon_count),
            )
            daewoon_compact = _build_daewoon_compact(daewoon_out)
        except Exception as e:
            daewoon_out = {"error": str(e)}

    result = {
        "ok": True,
        "input": {
            "name": name,
            "birth_datetime_parsed": birth_dt.isoformat(),
            "birth_city": birth_city,
            "longitude": longitude,
            "longitude_source": longitude_source,
            "yaja_si_separated": bool(yaja_si_separated),
        },
        "pillars": {
            "year": _pillar_dict(saju.year_pillar),
            "month": _pillar_dict(saju.month_pillar),
            "day": _pillar_dict(saju.day_pillar),
            "hour": _pillar_dict(saju.hour_pillar),
        },
        "element_counts": counts,
        "ilgan_strength": {
            "level": ilgan_strength.level.hangul,
            "score": round(ilgan_strength.total, 2),
            "reason": ilgan_strength.reason,
        },
        "jeonggyeok": jeonggyeok and str(jeonggyeok),
        "yongsin": yongsin and str(yongsin),
        "compact": _build_compact(
            name, saju, counts, yearly,
            ilgan_strength=ilgan_strength, jeonggyeok=jeonggyeok, yongsin=yongsin,
        ),
        "yearly": yearly_out,
        "monthly": monthly_out,
        "monthly_compact": monthly_compact,
        "daewoon": daewoon_out,
        "daewoon_compact": daewoon_compact,
    }

    return jsonify(result)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
