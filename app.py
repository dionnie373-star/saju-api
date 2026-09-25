"""
saju-api: 사주(四柱) 계산 웹 API

POST /calculate
{
  "name": "홍길동",              // optional
  "birth_datetime": "1984-09-27T20:00:00",  // 필수, 양력 기준, 시간 모름이면 12:00 사용 권장
  "birth_city": "Berlin",         // longitude 대신 도시 이름으로도 가능 (서버가 자동으로 경도를 찾음)
  "longitude": 126.9784,          // birth_city 대신 직접 경도를 줄 수도 있음
  "yaja_si_separated": true,      // 선택, 기본 true (야자시/조자시 구분)
  "target_year": 2027             // 선택, 특정 연도 세운(년주)까지 함께 계산하고 싶을 때
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

from korean_saju import Saju, SajuAnalysis, load_bundled_data  # noqa: E402

app = Flask(__name__)

_lunar, _solar_terms = load_bundled_data()

ELEMENT_HANJA = {
    "목": "木", "화": "火", "토": "土", "금": "金", "수": "水",
}

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


def _build_compact(name, saju, counts, yearly=None):
    pillars_str = (
        f"년주 {saju.year_pillar.hanja}({saju.year_pillar.hangul}) / "
        f"월주 {saju.month_pillar.hanja}({saju.month_pillar.hangul}) / "
        f"일주 {saju.day_pillar.hanja}({saju.day_pillar.hangul}) / "
        f"시주 {saju.hour_pillar.hanja}({saju.hour_pillar.hangul})"
    )
    counts_str = ", ".join(f"{el}{ELEMENT_HANJA[el]} {cnt}개" for el, cnt in counts.items())
    max_el = max(counts, key=counts.get)
    min_els = [el for el, cnt in counts.items() if cnt == min(counts.values())]
    lines = [
        f"이름: {name or '(미입력)'}",
        f"사주: {pillars_str}",
        f"오행 분포: {counts_str}",
        f"가장 많은 오행: {max_el}({ELEMENT_HANJA[max_el]})",
        f"가장 적은/없는 오행: {', '.join(f'{e}({ELEMENT_HANJA[e]})' for e in min_els)}",
    ]
    for y in (yearly or []):
        lines.append(
            f"{y['year']}년 세운: {y['pillar'].hanja}({y['pillar'].hangul}), "
            f"천간 오행 {y['pillar'].cheon_gan.o_haeng.hangul}({ELEMENT_HANJA[y['pillar'].cheon_gan.o_haeng.hangul]})"
        )
    return "\n".join(lines)


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

    target_years = payload.get("target_years")
    if not target_years and target_year:
        target_years = [target_year]

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
        "jeonggyeok": getattr(analysis, "jeonggyeok", None) and str(analysis.jeonggyeok),
        "yongsin": getattr(analysis, "yongsin", None) and str(analysis.yongsin),
        "compact": _build_compact(name, saju, counts, yearly),
        "yearly": yearly_out,
    }

    return jsonify(result)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
