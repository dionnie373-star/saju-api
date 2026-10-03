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

import hashlib
import hmac
import os
import re
import sys
import threading
import time
from datetime import datetime, date, time as dtime, timedelta, timezone as dt_timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from flask import Flask, request, jsonify, send_from_directory, redirect
from werkzeug.middleware.proxy_fix import ProxyFix

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
# Render는 요청을 앱에 전달하기 전에 자체 리버스 프록시를 거치므로, 클라이언트가
# 직접 보낸 X-Forwarded-For 헤더값을 그대로 신뢰하면 IP 기반 레이트리밋을
# "X-Forwarded-For: 1.2.3.4"처럼 헤더를 조작해서 우회할 수 있다. ProxyFix는
# 신뢰할 프록시 홉 수(x_for=1)만큼만 거슬러 올라가서 "우리 쪽 인프라가 실제로
# 관찰한" IP를 request.remote_addr로 노출해준다 — 클라이언트가 그 앞에 아무리
# 가짜 X-Forwarded-For 값을 붙여도 영향받지 않는다(표준적인 Flask/werkzeug
# 권장 방식). 레이트리밋 외 용도(로깅 등)로도 이 신뢰 가능한 값을 쓴다.
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1, x_prefix=1)

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

# 심각한 버그 수정(2026-09-27): 아래 "시간대" 테이블이 추가되기 전까지는, 사용자가
# 입력한 "현지 시계 시각"(예: 베를린 07:30)을 아무 변환 없이 그대로 한국표준시(KST)
# 시각으로 취급한 뒤, 거기에 "한국 내부 지역차 보정" 공식((경도-135°)×4분)을 그대로
# 적용하고 있었다. 이러면 베를린은 (13.4-135)×4 ≈ -8시간6분이라는 터무니없는
# 보정이 걸려서, 실제로는 오전인데 자시(子時, 23~01시)로 계산되는 등 시주(時柱)가
# 거의 항상 틀리고, 자정을 넘나드는 경우 일주(日柱)까지 틀어졌다(실측으로 확인,
# 예: 1991-03-14 07:30 베를린 → 잘못된 결과 시주=壬子/일주=壬午, 서울로 바꾸면
# 완전히 다른 일주=癸未가 나옴 — 도시만 바꿔도 "일간(본인 자신)" 자체가 바뀌는 건
# 명백히 버그). 아직 실제 결제 고객에게 발송된 리포트가 없어(사업 오픈 전, Paddle
# 샌드박스 테스트만 진행), 재발송 없이 지금 바로 근본 수정한다.
#
# 수정 방법: 사용자가 입력한 시각을 "출생지의 실제 시간대"(아래 표)로 정확히
# 해석해서(역사적 서머타임까지 IANA tzdata가 자동 처리) 진짜 UTC 절대시각을 구한 뒤,
# 그 절대시각의 "한국표준시(UTC+9) 환산 시각"을 계산해서 그걸 korean_saju 라이브러리에
# 넘긴다. korean_saju 내부 로직(연주/월주 절기 비교, 진태양시 보정 공식 전부)은
# "입력이 이미 정확한 KST"라는 전제로 설계돼 있으므로, 그 전제만 실제로 충족시켜주면
# 라이브러리 자체는 수정할 필요가 없다 — (경도-135)×4 보정도 KST 환산 시각과
# 결합하면 대수적으로 정확히 "UTC + 경도/15시간"(보편적 진태양시 공식)이 된다.
KNOWN_CITY_TIMEZONE = {
    # 독일
    "berlin": "Europe/Berlin", "hamburg": "Europe/Berlin", "münchen": "Europe/Berlin",
    "munich": "Europe/Berlin", "köln": "Europe/Berlin", "koeln": "Europe/Berlin",
    "cologne": "Europe/Berlin", "frankfurt": "Europe/Berlin",
    "frankfurt am main": "Europe/Berlin", "stuttgart": "Europe/Berlin",
    "düsseldorf": "Europe/Berlin", "duesseldorf": "Europe/Berlin",
    "leipzig": "Europe/Berlin", "dortmund": "Europe/Berlin", "essen": "Europe/Berlin",
    "bremen": "Europe/Berlin", "dresden": "Europe/Berlin", "hannover": "Europe/Berlin",
    "hanover": "Europe/Berlin", "nürnberg": "Europe/Berlin", "nuernberg": "Europe/Berlin",
    "nuremberg": "Europe/Berlin", "duisburg": "Europe/Berlin", "bochum": "Europe/Berlin",
    "wuppertal": "Europe/Berlin", "bielefeld": "Europe/Berlin", "bonn": "Europe/Berlin",
    "münster": "Europe/Berlin", "muenster": "Europe/Berlin", "karlsruhe": "Europe/Berlin",
    "mannheim": "Europe/Berlin", "augsburg": "Europe/Berlin", "wiesbaden": "Europe/Berlin",
    "mönchengladbach": "Europe/Berlin", "gelsenkirchen": "Europe/Berlin",
    "braunschweig": "Europe/Berlin", "chemnitz": "Europe/Berlin", "kiel": "Europe/Berlin",
    "aachen": "Europe/Berlin",
    # 오스트리아
    "wien": "Europe/Vienna", "vienna": "Europe/Vienna", "salzburg": "Europe/Vienna",
    "graz": "Europe/Vienna", "innsbruck": "Europe/Vienna",
    # 스위스
    "zürich": "Europe/Zurich", "zuerich": "Europe/Zurich", "zurich": "Europe/Zurich",
    "bern": "Europe/Zurich", "basel": "Europe/Zurich", "genf": "Europe/Zurich",
    "geneva": "Europe/Zurich",
    # 한국
    "서울": "Asia/Seoul", "seoul": "Asia/Seoul", "부산": "Asia/Seoul", "busan": "Asia/Seoul",
    "인천": "Asia/Seoul", "incheon": "Asia/Seoul", "대구": "Asia/Seoul", "daegu": "Asia/Seoul",
}

DEFAULT_TIMEZONE = "Europe/Berlin"  # 독일 타겟 서비스이므로 도시를 못 찾았을 때의 기본값


def _lookup_location(city_name):
    """도시 이름 -> (경도, 시간대, 출처). 1) 내장 표 2) 무료 지오코딩 API 3) 기본값 순으로 시도.

    시간대(IANA 이름, 예: "Europe/Berlin")가 있어야 사용자가 입력한 "현지 시계
    시각"을 정확한 절대시각(UTC)으로 변환할 수 있다 — 경도만으로는 이게 불가능하다
    (경도는 사주 계산 내부의 진태양시 보정에만 쓰이고, 실제 시간대 오프셋/서머타임
    여부는 별도로 알아야 한다).
    """
    key = city_name.strip().lower()
    if key in KNOWN_CITY_LONGITUDE:
        return KNOWN_CITY_LONGITUDE[key], KNOWN_CITY_TIMEZONE.get(key, DEFAULT_TIMEZONE), "known_city"

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
            r = results[0]
            # Open-Meteo 지오코딩 응답에는 "timezone" 필드(IANA 이름)가 같이 온다.
            tz_name = r.get("timezone") or DEFAULT_TIMEZONE
            return float(r["longitude"]), tz_name, "geocoded"
    except Exception:
        pass

    return DEFAULT_LONGITUDE, DEFAULT_TIMEZONE, "default_fallback"


def _to_kst_equivalent_moment(local_dt, timezone_name):
    """출생지 "현지 시계" naive datetime -> korean_saju가 기대하는 "KST 환산" naive datetime.

    korean_saju 내부(연주/월주 절기 비교, 진태양시 보정 공식)는 전달받은 datetime을
    "이미 정확한 한국표준시(UTC+9)"라고 전제하고 동작한다. 그래서 사용자가 입력한
    "베를린 현지시각 07:30" 같은 걸 그대로 넘기면 안 되고, 다음 과정을 거쳐야 한다:

    1. `timezone_name`(예: "Europe/Berlin")으로 이 naive datetime을 실제 시간대가
       적용된 aware datetime으로 해석 — 이 단계에서 역사적 서머타임까지 IANA tzdata가
       자동으로 반영된다(예: 1990-07 베를린은 UTC+2, 1990-01 베를린은 UTC+1).
    2. 그 절대 시각(UTC)을 구한다.
    3. UTC + 9시간 = "이 순간을 한국에서는 몇 시로 부르는가"를 계산해서, tzinfo를
       뗀 naive datetime으로 반환한다 — 이게 korean_saju가 기대하는 형태다.

    `timezone_name`을 알 수 없는 경우(잘못된 문자열 등)는 DEFAULT_TIMEZONE으로
    안전하게 대체한다(전체 계산이 예외로 죽는 것보다 낫다).
    """
    try:
        zone = ZoneInfo(timezone_name)
    except (ZoneInfoNotFoundError, ValueError, KeyError):
        zone = ZoneInfo(DEFAULT_TIMEZONE)

    aware_local = local_dt.replace(tzinfo=zone)
    utc_instant = aware_local.astimezone(dt_timezone.utc)
    kst_equivalent = utc_instant + timedelta(hours=9)
    return kst_equivalent.replace(tzinfo=None)


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


def _compute_daewoon_forecast(saju, day_stem, gender_str, solar_terms, count=8, birth_local_date=None):
    """프리미엄(대운) 리포트용: 10년 단위 대운 시퀀스 + 각 시기의 십성/축 계산.

    대운의 진행 방향(순행/역행)은 연간(年干)의 음양과 성별의 조합으로 정해지므로
    (양남·음녀=순행, 음남·양녀=역행), 대운 계산에는 성별이 반드시 필요하다.
    각 대운 시기의 십성은 이 사람의 일간(day_stem) 기준으로 계산해서
    재물운/관계운/직업운/총운 중 어느 축이 두드러지는 시기인지 매긴다.

    birth_local_date: 나이 계산에 쓸 "출생지 현지 달력 날짜". saju.kst_moment는
    시간대 버그 수정(2026-09-27) 이후로 "KST 환산 시각"이라 자정 근처 출생자는
    현지 날짜와 하루 어긋날 수 있다 — 나이는 반드시 실제 현지 생일 기준으로 계산해야
    하므로 이 값을 우선 사용한다. 생략 시(예: 과거 호출부 호환) saju.kst_moment.date()로
    대체한다.
    """
    gender = _resolve_gender(gender_str)
    daewoon = Daewoon.compute(saju=saju, gender=gender, solar_terms=solar_terms, count=count)

    birth_date = birth_local_date if birth_local_date is not None else saju.kst_moment.date()
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


class CalcError(Exception):
    """run_calculation()에서 잘못된 입력/계산 오류를 알릴 때 쓰는 예외.

    HTTP 라우트(/calculate)에서는 이걸 잡아서 400/500 JSON 응답으로 바꾸고,
    pipeline처럼 HTTP를 거치지 않는 내부 호출에서는 그냥 예외로 전파시킨다.
    """

    def __init__(self, message, status=400):
        super().__init__(message)
        self.status = status


def run_calculation(payload):
    """사주 계산의 핵심 로직. /calculate 라우트와 report_pipeline이 공유한다.

    입력: 요청 payload(dict, /calculate 문서의 필드들).
    출력: /calculate가 그대로 jsonify하는 것과 동일한 result dict.
    실패 시 CalcError를 던진다(.status에 적절한 HTTP 상태 코드).
    """
    name = payload.get("name")
    longitude = payload.get("longitude")
    birth_city = payload.get("birth_city")
    timezone_override = payload.get("timezone")  # 선택: 명시적으로 IANA 시간대를 줄 수도 있음
    yaja_si_separated = payload.get("yaja_si_separated", True)
    target_year = payload.get("target_year")

    if longitude is None and not birth_city:
        raise CalcError("longitude(경도) 또는 birth_city(도시명) 중 하나가 필요합니다.")

    try:
        birth_dt = _resolve_birth_datetime(payload)
    except Exception as e:
        raise CalcError(f"생년월일시를 해석할 수 없습니다: {e}") from e

    longitude_source = "provided"
    timezone_name = timezone_override or DEFAULT_TIMEZONE
    if longitude is not None:
        try:
            longitude = float(longitude)
        except (TypeError, ValueError):
            raise CalcError("longitude 값은 숫자여야 합니다.") from None
        if birth_city and not timezone_override:
            # longitude를 직접 줬어도 birth_city가 같이 왔으면 시간대는 도시로 찾는다.
            _, timezone_name, _ = _lookup_location(birth_city)
    else:
        longitude, timezone_name_from_city, longitude_source = _lookup_location(birth_city)
        if not timezone_override:
            timezone_name = timezone_name_from_city

    # 버그 수정(2026-09-27): 사용자가 입력한 건 "출생지 현지 시계 시각"이지 한국표준시가
    # 아니다. 이걸 그대로 korean_saju에 넘기면 시주/일주가 크게 틀어진다 — 위
    # KNOWN_CITY_TIMEZONE 블록의 설명 참고. birth_dt(현지 시각 원본)는 나이 계산 등에
    # 쓰기 위해 그대로 보존하고, 실제 사주 계산에는 KST 환산 시각만 사용한다.
    birth_local_dt = birth_dt
    kst_equivalent_moment = _to_kst_equivalent_moment(birth_local_dt, timezone_name)

    try:
        saju = Saju.from_birth(
            kst_moment=kst_equivalent_moment,
            solar_terms=_solar_terms,
            longitude=longitude,
            yaja_si_separated=bool(yaja_si_separated),
        )
        analysis = SajuAnalysis(saju)
    except Exception as e:
        raise CalcError(f"사주 계산 중 오류가 발생했습니다: {e}", status=500) from e

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
                birth_local_date=birth_local_dt.date(),
            )
            daewoon_compact = _build_daewoon_compact(daewoon_out)
        except Exception as e:
            daewoon_out = {"error": str(e)}

    result = {
        "ok": True,
        "input": {
            "name": name,
            "birth_datetime_parsed": birth_local_dt.isoformat(),
            "birth_city": birth_city,
            "longitude": longitude,
            "longitude_source": longitude_source,
            "timezone": timezone_name,
            "kst_equivalent_moment": kst_equivalent_moment.isoformat(),
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

    return result


STATIC_SITE_DIR = os.path.join(os.path.dirname(__file__), "static_site")


@app.route("/", methods=["GET"])
def landing_page():
    """랜딩페이지를 이 API와 같은 오리진(same-origin)에서 서빙한다.

    Claude 아티팩트 위에 올렸을 때는 아티팩트 자체의 CSP(connect-src)가
    외부 API(fetch) 호출을 막아버려서, 신청 폼이 서버에 도달하지 못했다.
    같은 Flask 앱에서 정적 파일로 서빙하면 프론트엔드/백엔드가 같은 출처가
    되어 이 제한이 사라진다.
    """
    return send_from_directory(STATIC_SITE_DIR, "index.html")


@app.route("/pricing", methods=["GET"])
def pricing_page():
    """Paddle 계정 인증(웹사이트 검증)용 별도 가격 페이지 경로.

    별도 페이지를 새로 만들지 않고, 가격표가 있는 랜딩페이지 섹션
    (id="pricing")으로 바로 스크롤되도록 프래그먼트로 리다이렉트한다.
    """
    return redirect("/#pricing")


# 법적 필수 페이지 (초안 — 실 오픈 전 실제 정보로 채우고 법률 검토 필요.
# static_site/*.html 상단의 "Entwurf" 경고 참고).
_LEGAL_PAGES = {
    "impressum": "impressum.html",
    "datenschutz": "datenschutz.html",
    "agb": "agb.html",
    "widerruf": "widerruf.html",
    "danke": "danke.html",  # Digistore24 Thank-you 페이지 (승인 요건: 필수 고지문구 + trust badge)
}


@app.route("/<page>", methods=["GET"])
def legal_page(page):
    filename = _LEGAL_PAGES.get(page)
    if not filename:
        return jsonify({"ok": False, "error": "Not found"}), 404
    return send_from_directory(STATIC_SITE_DIR, filename)


IMAGES_DIR = os.path.join(STATIC_SITE_DIR, "images")


@app.route("/images/<path:filename>", methods=["GET"])
def static_image(filename):
    """랜딩페이지에 쓰이는 실사 이미지 서빙 (static_site/images/)."""
    return send_from_directory(IMAGES_DIR, filename)


@app.route("/favicon.svg", methods=["GET"])
def favicon():
    return send_from_directory(STATIC_SITE_DIR, "favicon.svg")


@app.route("/robots.txt", methods=["GET"])
def robots_txt():
    return send_from_directory(STATIC_SITE_DIR, "robots.txt")


@app.route("/sitemap.xml", methods=["GET"])
def sitemap_xml():
    return send_from_directory(STATIC_SITE_DIR, "sitemap.xml")


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"ok": True, "service": "saju-api", "status": "running"})


@app.after_request
def _add_cors_headers(response):
    """랜딩페이지(Claude 아티팩트 등 별도 도메인)에서 이 API를 호출할 수 있도록 CORS 허용.

    ALLOWED_ORIGIN 환경변수로 특정 도메인만 허용하도록 좁힐 수 있다.
    기본값은 "*"(모든 도메인) — MVP 단계에서는 편의상 열어두고,
    실사용자 결제가 붙기 전에 실제 랜딩페이지 도메인으로 좁히는 걸 권장.
    """
    origin = os.environ.get("ALLOWED_ORIGIN", "*")
    response.headers["Access-Control-Allow-Origin"] = origin
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response


@app.route("/calculate", methods=["POST", "OPTIONS"])
def calculate():
    if request.method == "OPTIONS":
        return "", 204
    try:
        payload = request.get_json(force=True, silent=False) or {}
    except Exception:
        return jsonify({"ok": False, "error": "잘못된 JSON 형식입니다."}), 400

    try:
        result = run_calculation(payload)
    except CalcError as e:
        return jsonify({"ok": False, "error": str(e)}), e.status

    return jsonify(result)


# /signup은 인증도 결제도 없는 완전 공개 엔드포인트라서, 별도 방어가 없으면
# 스크립트로 반복 호출해서 (1) Anthropic API 비용을 계속 발생시키거나
# (2) 임의의 제3자 이메일 주소로 원치 않는 메일을 계속 보내는 스팸 도구로
# 악용될 수 있다. 메모리 기반의 아주 단순한 슬라이딩 윈도우 레이트리밋으로
# 최소한의 방어선을 둔다 (Paddle 트랜잭션 중복방지 세트와 같은 방식 —
# gunicorn 워커 1개 구성이라 프로세스 내 메모리로 충분하다).
_RATE_LIMIT_LOCK = threading.Lock()
_RATE_LIMIT_HISTORY = {}


def _rate_limited(bucket: str, key: str, *, max_count: int, window_seconds: float) -> bool:
    """(bucket, key) 조합이 window_seconds 동안 max_count번을 넘게 요청했으면
    True. 넘지 않았으면 이번 요청을 기록하고 False를 반환한다."""
    now = time.time()
    cutoff = now - window_seconds
    with _RATE_LIMIT_LOCK:
        history = _RATE_LIMIT_HISTORY.setdefault((bucket, key), [])
        while history and history[0] < cutoff:
            history.pop(0)
        if len(history) >= max_count:
            return True
        history.append(now)
        return False


def _client_ip() -> str:
    # X-Forwarded-For 헤더를 직접 파싱하지 않는다 - 그러면 클라이언트가 그
    # 헤더값 자체를 조작해서(레이트리밋 우회 목적) 아무 IP나 자처할 수 있다.
    # 위에서 적용한 ProxyFix가 "신뢰할 프록시 홉(Render) 뒤에서 실제로 관찰된
    # IP"만 request.remote_addr에 반영해주므로, 그 값만 신뢰한다.
    return request.remote_addr or "unknown"


@app.route("/signup", methods=["POST", "OPTIONS"])
def signup():
    """무료 리포트 신청 엔드포인트 (랜딩페이지 폼에서 호출).

    받은 정보로 사주를 계산하고, Claude로 무료 리포트 텍스트를 생성해서
    PDF로 만든 뒤 이메일로 발송한다. 유료/프리미엄은 결제 연동이 붙기 전까지는
    이 엔드포인트로 노출하지 않는다(결제 확인 후 별도 웹훅에서 트리거할 예정).
    """
    if request.method == "OPTIONS":
        return "", 204

    try:
        payload = request.get_json(force=True, silent=False) or {}
    except Exception:
        return jsonify({"ok": False, "error": "잘못된 JSON 형식입니다."}), 400

    email = (payload.get("email") or "").strip()
    if not email or "@" not in email:
        return jsonify({"ok": False, "error": "유효한 이메일 주소가 필요합니다."}), 400

    # 같은 이메일로는 10분에 1번, 같은 IP로는 1시간에 5번까지만 허용.
    if _rate_limited("signup_email", email.lower(), max_count=1, window_seconds=600):
        return jsonify({
            "ok": False,
            "error": "Für diese E-Mail-Adresse wurde bereits vor Kurzem ein kostenloses Profil angefordert. Bitte schau in deinem Postfach nach oder versuche es in ein paar Minuten erneut.",
        }), 429
    if _rate_limited("signup_ip", _client_ip(), max_count=5, window_seconds=3600):
        return jsonify({
            "ok": False,
            "error": "Zu viele Anfragen. Bitte versuche es später erneut.",
        }), 429

    try:
        calc_result = run_calculation(payload)
    except CalcError as e:
        return jsonify({"ok": False, "error": str(e)}), e.status

    from report_pipeline import PipelineError, run_free_signup

    try:
        run_free_signup(payload=payload, calc_result=calc_result)
    except PipelineError as e:
        return jsonify({"ok": False, "error": str(e)}), e.status

    return jsonify({"ok": True, "message": "리포트를 생성해서 이메일로 발송했습니다."})


# Paddle 상품 가격(price) ID -> 우리 시스템의 리포트 등급(tier) 매핑.
# 샌드박스/라이브 가격 ID가 서로 다르므로(같은 상품이라도 환경마다 pri_...
# ID가 별개로 발급됨), 하드코딩 대신 전부 환경변수로 주입한다. 이렇게 하면
# 샌드박스<->라이브 전환이 코드 수정/재배포 없이 Render 환경변수만 바꾸면
# 끝난다 (2026-09-28: 라이브 카탈로그 3개 생성 완료, 아래 기본값은 지금까지
# 써온 샌드박스 ID — 아직 Paddle 라이브 계정 KYC/도메인 승인 전이라 Render는
# 계속 샌드박스 값으로 두고, 승인 나면 이 세 환경변수를 라이브 ID로 교체할 것).
#   PADDLE_PRICE_ID_PAID          -> Palja Jahresreport (Paid), EUR 9.90
#   PADDLE_PRICE_ID_PREMIUM       -> Palja Lebenskarte (Premium), EUR 24.90
#   COMPATIBILITY_PADDLE_PRICE_ID -> Palja Kompatibilitäts-Check, EUR 4.90
PADDLE_PRICE_TIER_MAP = {}

_paid_price_id = os.environ.get("PADDLE_PRICE_ID_PAID", "pri_01m3f98f0s27hjx0xy4bc9em4d")
if _paid_price_id:
    PADDLE_PRICE_TIER_MAP[_paid_price_id] = "paid"

_premium_price_id = os.environ.get("PADDLE_PRICE_ID_PREMIUM", "pri_01m3f9bjxx7sgpr1wvm5g8k61r")
if _premium_price_id:
    PADDLE_PRICE_TIER_MAP[_premium_price_id] = "premium"

# 궁합(Kompatibilität) 상품은 처음부터 환경변수로만 주입해왔다 (값이 없으면
# 이 티어는 그냥 비활성 상태로 남는다).
_compatibility_price_id = os.environ.get("COMPATIBILITY_PADDLE_PRICE_ID")
if _compatibility_price_id:
    PADDLE_PRICE_TIER_MAP[_compatibility_price_id] = "compatibility"

# Paddle은 우리 서버의 응답이 늦으면(리포트 생성에 수십 초가 걸림) 같은
# transaction.completed 이벤트를 여러 번 재전송한다. 트랜잭션 ID(data.id)
# 기준으로 "이미 처리 완료된" 결제를 기록해두고, 재전송이 들어오면 리포트를
# 다시 생성/발송하지 않고 조용히 200으로 응답한다.
# (참고: 처리 도중 실패하면 목록에서 제거해서 다음 재시도가 정상적으로
#  다시 시도될 수 있게 한다. 메모리 기반이라 서버 재시작 시 초기화되지만,
#  Paddle의 재시도는 보통 몇 분 안에 끝나므로 이 용도로는 충분하다.)
_PROCESSED_PADDLE_TRANSACTIONS = set()
_PROCESSED_PADDLE_LOCK = threading.Lock()


def _fulfill_report_order(tier, custom_data, email):
    """결제 완료 후 리포트 생성+발송 공통 로직 (Paddle/Digistore24 웹훅이 공유).

    성공하면 (response_dict, 200)을 돌려준다. 실패하면 CalcError 또는
    report_pipeline.PipelineError를 그대로 던진다 — 호출부(각 웹훅)가 이걸
    잡아서 멱등성 마킹을 롤백하고 (.status에 맞는 코드로) 응답을 만든다.
    """
    from report_pipeline import (
        PipelineError,
        run_compatibility_signup,
        run_paid_signup,
        run_premium_signup,
    )

    if tier == "compatibility":
        # 궁합 리포트는 사람 두 명의 생년월일시가 필요하다 (본인 + 상대방).
        # customData 필드명은 랜딩페이지 폼과 맞춰서 _a/_b 접미사로 구분한다.
        required = ("birth_date_a", "birth_city_a", "birth_date_b", "birth_city_b")
        missing = [k for k in required if not custom_data.get(k)]
        if missing:
            raise PipelineError(
                f"Kompatibilität benötigt Geburtsdaten für beide Personen (fehlt: {', '.join(missing)})",
                400,
            )

        payload_a = {
            "name": custom_data.get("name_a"),
            "birth_date": custom_data.get("birth_date_a"),
            "birth_time": custom_data.get("birth_time_a"),
            "birth_city": custom_data.get("birth_city_a"),
        }
        payload_b = {
            "name": custom_data.get("name_b"),
            "birth_date": custom_data.get("birth_date_b"),
            "birth_time": custom_data.get("birth_time_b"),
            "birth_city": custom_data.get("birth_city_b"),
        }

        calc_result_a = run_calculation(payload_a)
        calc_result_b = run_calculation(payload_b)

        compat_payload = dict(custom_data)
        compat_payload["email"] = email

        run_compatibility_signup(
            payload=compat_payload, calc_result_a=calc_result_a, calc_result_b=calc_result_b
        )
        return {"ok": True, "message": "Kompatibilitätsreport를 생성해서 이메일로 발송했습니다."}, 200

    payload = dict(custom_data)
    payload["email"] = email
    payload["tier"] = tier
    if tier == "paid":
        # Jahresreport 대상 연도 결정 규칙(2026-10-03 확정):
        # 7월~12월에 신청 -> 다음 해 운세 (예: 2026-07~2026-12 신청 -> 2027년)
        # 1월~6월에 신청 -> 같은 해 운세 (예: 2027-01~2027-06 신청 -> 2027년)
        # 이전에는 무조건 "올해+1"이어서, 예를 들어 2027년 1~12월 내내 아무도
        # 2027년 리포트를 받을 수 없고 전부 2028년으로 건너뛰는 문제가 있었음.
        _today = date.today()
        _default_monthly_year = _today.year + 1 if _today.month >= 7 else _today.year
        payload.setdefault("monthly_year", _default_monthly_year)
    elif tier == "premium" and not payload.get("gender"):
        raise PipelineError("premium 리포트에는 gender가 필요합니다.", 400)

    calc_result = run_calculation(payload)

    if tier == "paid":
        run_paid_signup(payload=payload, calc_result=calc_result)
    else:
        run_premium_signup(payload=payload, calc_result=calc_result)

    return {"ok": True, "message": f"{tier} 리포트를 생성해서 이메일로 발송했습니다."}, 200


def _verify_paddle_signature(raw_body: bytes, signature_header: str, secret: str) -> bool:
    """Paddle 웹훅 서명(Paddle-Signature 헤더)을 검증한다.

    헤더 형식: "ts=<유닉스시간>;h1=<HMAC-SHA256 hex>"
    서명 대상 문자열은 "{ts}:{raw_request_body}" 이고, 키는 Paddle이 발급한
    notification destination의 시크릿 키(pdl_ntfset_...)다.
    (참고: https://developer.paddle.com/webhooks/signature-verification)
    """
    if not secret or not signature_header:
        return False

    parts = {}
    for chunk in signature_header.split(";"):
        if "=" in chunk:
            k, v = chunk.split("=", 1)
            parts[k.strip()] = v.strip()

    ts = parts.get("ts")
    h1 = parts.get("h1")
    if not ts or not h1:
        return False

    signed_payload = f"{ts}:{raw_body.decode('utf-8')}"
    computed = hmac.new(
        secret.encode("utf-8"), signed_payload.encode("utf-8"), hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(computed, h1)


@app.route("/webhooks/paddle", methods=["POST"])
def paddle_webhook():
    """Paddle 결제 완료(transaction.completed) 웹훅.

    Paddle Checkout을 열 때 프론트엔드가 customData로 birth_date/birth_time/
    birth_city/email/name/(premium이면 gender)을 함께 보내면, 결제가 끝난 뒤
    Paddle이 이 엔드포인트를 호출한다. 여기서는:
      1) Paddle-Signature 헤더로 진짜 Paddle이 보낸 요청인지 검증
      2) 어떤 가격(price)이 결제됐는지로 paid/premium 등급을 판별
      3) customData에 담아온 생년월일시 정보로 사주를 계산해서 리포트 발송
    """
    raw_body = request.get_data()
    secret = os.environ.get("PADDLE_WEBHOOK_SECRET")
    signature = request.headers.get("Paddle-Signature", "")

    if not _verify_paddle_signature(raw_body, signature, secret):
        return jsonify({"ok": False, "error": "서명 검증 실패"}), 401

    try:
        event = request.get_json(force=True, silent=False) or {}
    except Exception:
        return jsonify({"ok": False, "error": "잘못된 JSON 형식입니다."}), 400

    event_type = event.get("event_type")
    if event_type != "transaction.completed":
        # 우리가 구독하지 않은 이벤트가 오더라도 200으로 조용히 무시한다
        # (Paddle은 2xx가 아니면 재시도하므로, 관심 없는 이벤트도 200을 줘야 한다).
        return jsonify({"ok": True, "ignored": event_type})

    data = event.get("data") or {}
    custom_data = data.get("custom_data") or {}

    transaction_id = data.get("id")
    if transaction_id:
        with _PROCESSED_PADDLE_LOCK:
            if transaction_id in _PROCESSED_PADDLE_TRANSACTIONS:
                return jsonify({"ok": True, "duplicate": True, "message": "이미 처리된 트랜잭션입니다."})
            _PROCESSED_PADDLE_TRANSACTIONS.add(transaction_id)
            # 메모리 누수 방지용 상한선 (평소에는 절대 도달하지 않음)
            if len(_PROCESSED_PADDLE_TRANSACTIONS) > 2000:
                _PROCESSED_PADDLE_TRANSACTIONS.clear()
                _PROCESSED_PADDLE_TRANSACTIONS.add(transaction_id)

    items = data.get("items") or []
    price_id = None
    if items:
        price_id = ((items[0] or {}).get("price") or {}).get("id")

    tier = PADDLE_PRICE_TIER_MAP.get(price_id)
    if not tier:
        if transaction_id:
            with _PROCESSED_PADDLE_LOCK:
                _PROCESSED_PADDLE_TRANSACTIONS.discard(transaction_id)
        return jsonify({"ok": False, "error": f"등록되지 않은 price_id: {price_id}"}), 400

    def _unmark_transaction():
        # 처리에 실패하면 목록에서 빼서, Paddle이 재시도할 때 다시 시도할 수 있게 한다.
        if transaction_id:
            with _PROCESSED_PADDLE_LOCK:
                _PROCESSED_PADDLE_TRANSACTIONS.discard(transaction_id)

    email = (
        custom_data.get("email")
        or (data.get("customer") or {}).get("email")
        or ""
    ).strip()
    if not email or "@" not in email:
        _unmark_transaction()
        return jsonify({"ok": False, "error": "customData에 유효한 email이 없습니다."}), 400

    # 디지털 콘텐츠 청약철회권 조기 소멸(§ 356 Abs. 5 BGB)에 필요한 동의는
    # 프론트엔드 체크박스에서 이미 강제하지만, 체크아웃을 우회해서 직접 호출하는
    # 경우를 막기 위해 서버에서도 다시 한번 확인한다.
    if not custom_data.get("withdrawal_consent"):
        _unmark_transaction()
        return jsonify({"ok": False, "error": "Zustimmung zum Widerrufsverzicht (withdrawal_consent) fehlt."}), 400

    from report_pipeline import PipelineError

    try:
        response_dict, status = _fulfill_report_order(tier, custom_data, email)
    except (CalcError, PipelineError) as e:
        _unmark_transaction()
        return jsonify({"ok": False, "error": str(e)}), e.status
    except Exception:
        _unmark_transaction()
        raise

    return jsonify(response_dict), status


# --- Digistore24 연동 (2026-10-03 시작, 테스트 중) ---------------------------
# Paddle이 "업종 승인 거부"로 라이브 전환이 막혀서, 대안으로 Digistore24를
# 검토 중이다 (독일 코칭/에소테릭 셀러들이 전통적으로 많이 쓰는 플랫폼이고,
# 금지 상품 목록에 점성술/운세 관련 조항이 없음을 확인함). Paddle과 달리
# Digistore24는 자체 호스팅 주문서(checkout-ds24.com)로 리다이렉트하는
# 방식이라 프론트엔드 체크아웃 흐름이 근본적으로 다르다 — 생년월일시 등은
# "custom" GET 파라미터 하나에 JSON으로 인코딩해서 주문서 링크에 실어 보내고,
# 결제가 끝나면 그 custom 값이 IPN(웹훅) POST에 그대로 되돌아온다.
#
# 세 상품 모두 2026-10-03에 Digistore24 승인 요청을 제출했고(승인 대기중),
# 승인이 날 때까지는 테스트 결제(Test Pay)만 가능하다 — 값이 없는 tier는
# 그냥 비활성 상태로 남는다 (Paddle의 궁합 애드온과 같은 패턴).
#   DIGISTORE24_PRODUCT_ID_PAID          -> Palja Jahresreport, EUR 9.90 (상품ID 740708, 승인 대기중)
#   DIGISTORE24_PRODUCT_ID_PREMIUM       -> Palja Lebenskarte, EUR 24.90 (상품ID 740939, 승인 대기중)
#   DIGISTORE24_PRODUCT_ID_COMPATIBILITY -> Kompatibilitäts-Check, EUR 4.90 (상품ID 740941, 승인 대기중)
DIGISTORE24_PRODUCT_TIER_MAP = {}

_ds24_paid_id = os.environ.get("DIGISTORE24_PRODUCT_ID_PAID", "740708")
if _ds24_paid_id:
    DIGISTORE24_PRODUCT_TIER_MAP[_ds24_paid_id] = "paid"

_ds24_premium_id = os.environ.get("DIGISTORE24_PRODUCT_ID_PREMIUM")
if _ds24_premium_id:
    DIGISTORE24_PRODUCT_TIER_MAP[_ds24_premium_id] = "premium"

_ds24_compat_id = os.environ.get("DIGISTORE24_PRODUCT_ID_COMPATIBILITY")
if _ds24_compat_id:
    DIGISTORE24_PRODUCT_TIER_MAP[_ds24_compat_id] = "compatibility"

_PROCESSED_DIGISTORE24_ORDERS = set()
_PROCESSED_DIGISTORE24_LOCK = threading.Lock()


def _verify_digistore24_signature(form, passphrase: str) -> bool:
    """Digistore24 IPN의 sha_sign을 검증한다.

    알고리즘 (공식 레퍼런스 구현, digistore24.com/download/ipn/examples/ipn/sha_sign.php의
    digistore_signature() 함수를 그대로 이식 — 처음에 참고했던 digistore_ipn.pdf 기반 알고리즘은
    실제 IPN 요청과 서명이 맞지 않아, 실제 테스트 IPN 호출을 캡처해서 역산/검증 후 수정함):
    sha_sign(대소문자 무관)과 빈 값(""/False)인 파라미터는 제외하고,
    남은 키를 대소문자 구분한 문자열 정렬로 정렬한 뒤, 각 "key=value" 바로 뒤에
    매번 sha_passphrase를 이어붙인다(구분자 없음 — 즉 key1=value1PASSPHRASEkey2=value2PASSPHRASE...).
    이 문자열 전체의 SHA512 hex digest(대문자)가 sha_sign과 일치해야 한다.
    """
    if not passphrase:
        return False

    received = (form.get("sha_sign") or form.get("SHASIGN") or "").strip()
    if not received:
        return False

    items = [
        (k, v)
        for k, v in form.items(multi=False)
        if k.lower() not in ("sha_sign", "shasign") and v not in (None, "", False)
    ]
    items.sort(key=lambda kv: kv[0])  # 대소문자 구분하는 문자열 정렬 (PHP SORT_STRING과 동일)

    sha_string = "".join(f"{k}={v}{passphrase}" for k, v in items)

    computed = hashlib.sha512(sha_string.encode("utf-8")).hexdigest()
    return hmac.compare_digest(computed.lower(), received.lower())


def _decode_digistore24_custom(raw: str) -> str:
    """static_site/index.html의 base64UrlEncodeJson()이 인코딩한 "custom" 값을 원래 JSON
    문자열로 되돌린다.

    왜 JSON을 그대로 안 보내고 base64url을 쓰는가: 실제 테스트 구매로 확인한 결과,
    Digistore24는 "custom" 파라미터 값에서 큰따옴표(")를 전부 제거해버린다 — 보낸 값이
    {"email": "a@b.de"}였는데 실제 IPN 콜백에는 {email: a@b.de}로, 즉 JSON을 깨뜨리는
    방식으로 따옴표만 사라진 채 돌아옴(원인 불명 — Digistore24 쪽 입력 새니타이징으로 추정).
    JSON 파싱이 매번 실패해서, 애초에 큰따옴표가 전혀 없는 base64url 인코딩으로 바꿨다.
    """
    import base64

    padded = raw + "=" * (-len(raw) % 4)
    return base64.urlsafe_b64decode(padded.encode("ascii")).decode("utf-8")


@app.route("/webhooks/digistore24", methods=["POST"])
def digistore24_webhook():
    """Digistore24 IPN(Instant Payment Notification) 웹훅.

    palja.de의 주문 버튼이 Digistore24 주문서 링크로 이동할 때
    "custom" GET 파라미터에 생년월일시/이메일/동의 여부 등을 JSON으로 실어
    보내고, 결제가 끝나면 Digistore24가 그 custom 값을 그대로 담아 이
    엔드포인트를 호출한다. 처리 흐름은 Paddle 웹훅과 동일 — 서명 검증 →
    상품ID로 등급(tier) 판별 → custom에 담긴 생년월일시로 리포트 생성/발송.
    """
    passphrase = os.environ.get("DIGISTORE24_SHA_PASSPHRASE")

    if not _verify_digistore24_signature(request.form, passphrase):
        return jsonify({"ok": False, "error": "서명 검증 실패"}), 401

    event = request.form.get("event", "")
    if event != "on_payment":
        # 환불/차지백 등 우리가 아직 처리하지 않는 이벤트는 조용히 무시한다
        # (Digistore24는 200을 못 받으면 같은 IPN을 재전송하므로, 관심 없는
        # 이벤트도 200을 줘야 재전송 스팸을 피할 수 있다).
        return jsonify({"ok": True, "ignored": event})

    order_id = request.form.get("order_id", "")
    if order_id:
        with _PROCESSED_DIGISTORE24_LOCK:
            if order_id in _PROCESSED_DIGISTORE24_ORDERS:
                return jsonify({"ok": True, "duplicate": True, "message": "이미 처리된 주문입니다."})
            _PROCESSED_DIGISTORE24_ORDERS.add(order_id)
            if len(_PROCESSED_DIGISTORE24_ORDERS) > 2000:
                _PROCESSED_DIGISTORE24_ORDERS.clear()
                _PROCESSED_DIGISTORE24_ORDERS.add(order_id)

    def _unmark_order():
        if order_id:
            with _PROCESSED_DIGISTORE24_LOCK:
                _PROCESSED_DIGISTORE24_ORDERS.discard(order_id)

    product_id = request.form.get("product_id", "")
    tier = DIGISTORE24_PRODUCT_TIER_MAP.get(product_id)
    if not tier:
        _unmark_order()
        return jsonify({"ok": False, "error": f"등록되지 않은 product_id: {product_id}"}), 400

    import binascii as _binascii
    import json as _json

    try:
        custom_data = _json.loads(_decode_digistore24_custom(request.form.get("custom") or ""))
        if not isinstance(custom_data, dict):
            raise ValueError("custom은 JSON 객체여야 합니다.")
    except (ValueError, TypeError, _binascii.Error):
        _unmark_order()
        return jsonify({"ok": False, "error": "custom 파라미터가 올바른 JSON이 아닙니다."}), 400

    email = (request.form.get("email") or custom_data.get("email") or "").strip()
    if not email or "@" not in email:
        _unmark_order()
        return jsonify({"ok": False, "error": "유효한 email이 없습니다."}), 400

    # Paddle과 동일하게, 체크아웃 우회 호출을 막기 위해 서버에서도 재확인.
    if not custom_data.get("withdrawal_consent"):
        _unmark_order()
        return jsonify({"ok": False, "error": "Zustimmung zum Widerrufsverzicht (withdrawal_consent) fehlt."}), 400

    from report_pipeline import PipelineError

    # 실제 테스트 구매로 확인된 버그: gunicorn 워커 타임아웃(--timeout)이 리포트
    # 생성 도중(Claude API 호출 중) 터지면, 워커가 SIGALRM 핸들러에서
    # sys.exit(1)로 SystemExit을 던진다. SystemExit은 BaseException만 상속하고
    # Exception은 상속하지 않기 때문에 아래 "except Exception"으로는 절대 못
    # 잡혀서 _unmark_order()가 호출되지 않았었다 — 그 결과 고객은 리포트를 못
    # 받았는데 order_id는 "처리 완료"로 영원히 남아, Digistore24가 재전송하는
    # IPN도 전부 "이미 처리된 주문"으로 무시되는 치명적인 버그였다. finally로
    # 바꿔서 성공(success=True)한 경우만 제외하고 어떤 예외(SystemExit 포함)가
    # 나도 반드시 unmark되게 한다.
    success = False
    try:
        response_dict, status = _fulfill_report_order(tier, custom_data, email)
        success = True
    except (CalcError, PipelineError) as e:
        return jsonify({"ok": False, "error": str(e)}), e.status
    finally:
        if not success:
            _unmark_order()

    return jsonify(response_dict), status


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
