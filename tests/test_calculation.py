"""run_calculation()의 순수 계산 로직에 대한 회귀 테스트 (표준 라이브러리 unittest만 사용
— 이 환경에서 pytest를 pip로 설치할 수 없어서, 의존성 없이 항상 돌아가게 만듦).

네트워크 호출이 전혀 없다: "Berlin"은 KNOWN_CITY_LONGITUDE 내장 표에 있어서
지오코딩 API를 타지 않는다. 사주 계산(korean_saju) 자체가 잘못 건드려져서
결과가 조용히 깨지는 것을 잡기 위한 스모크 테스트다.

실행: cd /home/claude/saju-api && python3 -m unittest discover tests -v
"""
import os
import unittest
from datetime import datetime

os.environ.setdefault("ANTHROPIC_API_KEY", "test-not-used")
os.environ.setdefault("BREVO_API_KEY", "test-not-used")
os.environ.setdefault("FROM_EMAIL", "test@example.com")
os.environ.setdefault("FROM_NAME", "Palja Test")

from app import (  # noqa: E402
    CalcError,
    run_calculation,
    _lookup_location,
    _to_kst_equivalent_moment,
)

FIVE_ELEMENTS = {"목", "화", "토", "금", "수"}  # 木火土金水 (오행)


class CalculationTests(unittest.TestCase):
    def test_basic_free_profile_calculation_smoke(self):
        """무료 프로필 흐름과 동일한 최소 입력으로 계산이 에러 없이 끝나고,
        기대되는 필드들이 다 채워지는지 확인한다."""
        result = run_calculation({
            "name": "Test",
            "birth_date": "1990-05-15",
            "birth_time": "14:30",
            "birth_city": "Berlin",
        })

        self.assertTrue(result.get("ok"))
        self.assertIn("pillars", result)
        self.assertIn("element_counts", result)
        # 오행 합계는 항상 4개 기둥 x 2글자 = 8이어야 한다 (천간 4 + 지지 4).
        self.assertEqual(sum(result["element_counts"].values()), 8)
        self.assertTrue(set(result["element_counts"].keys()) <= FIVE_ELEMENTS)

    def test_missing_birthdate_and_city_raises_calc_error(self):
        with self.assertRaises(CalcError):
            run_calculation({"name": "Nobody"})

    def test_birth_city_resolved_without_network_for_known_city(self):
        """Berlin처럼 내장 표에 있는 도시는 지오코딩 API를 타지 않아야 한다
        (테스트 환경에 네트워크가 없어도 항상 통과해야 함)."""
        result = run_calculation({
            "name": "Test",
            "birth_date": "1990-05-15",
            "birth_time": "08:00",
            "birth_city": "Berlin",
        })
        self.assertEqual(result.get("input", {}).get("longitude_source"), "known_city")

    def test_premium_daewoon_requires_gender_field_present_when_given(self):
        """프리미엄 리포트 경로(대운 계산)가 gender 없이도 죽지 않고, gender가
        있으면 daewoon 관련 필드가 채워지는지 확인한다."""
        result_no_gender = run_calculation({
            "name": "Test",
            "birth_date": "1990-05-15",
            "birth_time": "14:30",
            "birth_city": "Berlin",
        })
        self.assertIsNone(result_no_gender.get("daewoon"))

        result_with_gender = run_calculation({
            "name": "Test",
            "birth_date": "1990-05-15",
            "birth_time": "14:30",
            "birth_city": "Berlin",
            "gender": "female",
        })
        self.assertIsNotNone(result_with_gender.get("daewoon"))

    def test_monthly_forecast_for_paid_tier_produces_twelve_months(self):
        result = run_calculation({
            "name": "Test",
            "birth_date": "1990-05-15",
            "birth_time": "14:30",
            "birth_city": "Berlin",
            "monthly_year": 2027,
        })
        monthly = result.get("monthly")
        self.assertIsNotNone(monthly)
        self.assertEqual(monthly.get("year"), 2027)
        self.assertEqual(len(monthly.get("months") or []), 12)


class TimezoneBugFixTests(unittest.TestCase):
    """시간대 버그 수정(2026-09-28) 회귀 테스트.

    발견된 버그: 사용자가 입력한 "출생지 현지 시계 시각"(예: 베를린 07:30)을
    아무 변환 없이 그대로 한국표준시(KST)로 취급한 뒤 거기에 "한국 내부 지역차
    보정" 공식을 적용하고 있었다. 베를린은 (경도 13.4°-135°)×4분 ≈ -8시간6분이라는
    터무니없는 보정이 걸려서, 실제로는 아침인데 자시(子時, 23~01시)로 계산되는 등
    시주가 거의 항상 틀렸고, 자정을 넘나드는 경우 일주까지 틀어졌다.

    수정: 출생지의 실제 IANA 시간대로 정확히 UTC 절대시각을 구한 뒤, 그 시각의
    KST(UTC+9) 환산 시각을 korean_saju에 넘긴다.
    """

    def test_known_city_timezone_lookup_covers_germany_austria_switzerland_korea(self):
        cases = [
            ("berlin", "Europe/Berlin"), ("hamburg", "Europe/Berlin"),
            ("wien", "Europe/Vienna"), ("vienna", "Europe/Vienna"),
            ("zürich", "Europe/Zurich"), ("zurich", "Europe/Zurich"),
            ("seoul", "Asia/Seoul"), ("서울", "Asia/Seoul"),
        ]
        for city, expected_tz in cases:
            _, tz_name, source = _lookup_location(city)
            self.assertEqual(tz_name, expected_tz, msg=f"failed for {city}")
            self.assertEqual(source, "known_city")

    def test_kst_equivalent_moment_accounts_for_the_8_hour_timezone_gap_to_berlin(self):
        # 1991-03-14는 서머타임 시작 전(1991년 서머타임은 3/31 시작)이라 베를린은
        # CET(UTC+1). 07:30 CET = 06:30 UTC = 15:30 KST(UTC+9).
        moment = _to_kst_equivalent_moment(datetime(1991, 3, 14, 7, 30), "Europe/Berlin")
        self.assertEqual(moment, datetime(1991, 3, 14, 15, 30))

    def test_kst_equivalent_moment_reflects_historical_daylight_saving_time(self):
        # 1991-07-14는 서머타임 기간(CEST, UTC+2). 같은 07:30이어도 겨울과
        # 한 시간 차이가 나야 한다 — zoneinfo/IANA tzdata가 역사적 서머타임을
        # 자동으로 반영한다는 증거.
        winter = _to_kst_equivalent_moment(datetime(1991, 3, 14, 7, 30), "Europe/Berlin")
        summer = _to_kst_equivalent_moment(datetime(1991, 7, 14, 7, 30), "Europe/Berlin")
        self.assertEqual(winter, datetime(1991, 3, 14, 15, 30))
        self.assertEqual(summer, datetime(1991, 7, 14, 14, 30))

    def test_kst_equivalent_moment_for_seoul_is_a_near_no_op(self):
        # 한국은 실제로 UTC+9(=KST)라서, 서울 입력은 변환해도 그대로여야 한다
        # (버그 수정 이전부터 이미 맞았던 한국 사용자 케이스가 안 깨졌는지 확인).
        moment = _to_kst_equivalent_moment(datetime(1991, 3, 14, 7, 30), "Asia/Seoul")
        self.assertEqual(moment, datetime(1991, 3, 14, 7, 30))

    def test_kst_equivalent_moment_can_roll_over_to_the_next_calendar_date(self):
        # 22:00 CET(UTC+1) = 21:00 UTC = 06:00 다음날 KST.
        moment = _to_kst_equivalent_moment(datetime(1991, 3, 14, 22, 0), "Europe/Berlin")
        self.assertEqual(moment, datetime(1991, 3, 15, 6, 0))

    def test_unknown_timezone_name_falls_back_instead_of_raising(self):
        # 잘못된/모르는 시간대 문자열이 들어와도 전체 계산이 죽으면 안 된다.
        moment = _to_kst_equivalent_moment(datetime(1991, 3, 14, 7, 30), "Not/AZone")
        self.assertIsInstance(moment, datetime)

    def test_run_calculation_reports_the_resolved_timezone_and_kst_equivalent(self):
        result = run_calculation({
            "birth_date": "1991-03-14",
            "birth_time": "07:30",
            "birth_city": "Berlin",
        })
        self.assertEqual(result["input"]["timezone"], "Europe/Berlin")
        self.assertEqual(result["input"]["kst_equivalent_moment"], "1991-03-14T15:30:00")
        # 원본 "현지 시각"은 그대로 보존되어야 한다(나이 계산 등에 쓰임).
        self.assertEqual(result["input"]["birth_datetime_parsed"], "1991-03-14T07:30:00")

        # 2026-09-28 production 검증에서 실측 확인된 정답값 그대로 고정(회귀 안전망).
        # 이 4주 중 하나라도 바뀌면 timezone/진태양시 파이프라인이 어딘가 깨진 것이다.
        pillars = result["pillars"]
        self.assertEqual(pillars["year"]["hanja"], "辛未")
        self.assertEqual(pillars["month"]["hanja"], "辛卯")
        self.assertEqual(pillars["day"]["hanja"], "癸未")
        self.assertEqual(pillars["hour"]["hanja"], "丙辰")  # 辰時 — 子時 아님(버그였던 부분)

    def test_run_calculation_dst_winter_vs_summer_produce_different_hour_pillars(self):
        """같은 07:30 입력이라도 겨울(CET)과 여름(CEST)은 실제 UTC 절대시각이
        달라서 시주가 달라야 한다 — DST가 KST 환산 단계에서 실제로 반영된다는
        end-to-end 증거(단순 kst_equivalent_moment 값이 아니라 최종 시주까지)."""
        winter = run_calculation({
            "birth_date": "1991-01-14", "birth_time": "07:30", "birth_city": "Berlin",
        })
        summer = run_calculation({
            "birth_date": "1991-07-14", "birth_time": "07:30", "birth_city": "Berlin",
        })
        self.assertEqual(winter["input"]["kst_equivalent_moment"], "1991-01-14T15:30:00")
        self.assertEqual(summer["input"]["kst_equivalent_moment"], "1991-07-14T14:30:00")
        self.assertEqual(winter["pillars"]["hour"]["hanja"], "戊辰")
        self.assertEqual(summer["pillars"]["hour"]["hanja"], "己卯")
        self.assertNotEqual(winter["pillars"]["hour"], summer["pillars"]["hour"])

    def test_run_calculation_midnight_rollover_is_internally_consistent(self):
        """베를린 23:30(자정 전)과 다음날 00:30(자정 후) — local date가 하루
        넘어가면 KST-환산 날짜와 일주도 함께, 논리적으로 일관되게 넘어가야 한다.
        둘 다 실제로 자정 근접 시각이므로 시주가 子時(甲子)로 나오는 것 자체는
        정상이다 — 버그였던 것은 "07:30 같은 낮 시간"이 子時로 나오는 것이었다."""
        before = run_calculation({
            "birth_date": "1991-03-14", "birth_time": "23:30", "birth_city": "Berlin",
        })
        after = run_calculation({
            "birth_date": "1991-03-15", "birth_time": "00:30", "birth_city": "Berlin",
        })
        self.assertEqual(before["input"]["kst_equivalent_moment"], "1991-03-15T07:30:00")
        self.assertEqual(after["input"]["kst_equivalent_moment"], "1991-03-15T08:30:00")
        # 로컬 날짜가 03-14 -> 03-15로 넘어가면 일주도 함께 넘어간다.
        self.assertEqual(before["pillars"]["day"]["hanja"], "癸未")
        self.assertEqual(after["pillars"]["day"]["hanja"], "甲申")
        # 둘 다 자정 근접 시각이라 시주는 子時(甲子)로 동일 — 정상.
        self.assertEqual(before["pillars"]["hour"]["hanja"], "甲子")
        self.assertEqual(after["pillars"]["hour"]["hanja"], "甲子")

    def test_run_calculation_seoul_pillars_are_the_known_good_regression_values(self):
        """한국 사용자 계산은 이번 timezone 수정과 무관하게(항등변환이므로)
        수정 전과 완전히 동일해야 한다 — 정확한 4주 값을 고정해 회귀를 막는다."""
        result = run_calculation({
            "birth_date": "1991-03-14", "birth_time": "07:30", "birth_city": "Seoul",
        })
        self.assertEqual(result["input"]["timezone"], "Asia/Seoul")
        self.assertEqual(result["input"]["kst_equivalent_moment"], "1991-03-14T07:30:00")
        pillars = result["pillars"]
        self.assertEqual(pillars["year"]["hanja"], "辛未")
        self.assertEqual(pillars["month"]["hanja"], "辛卯")
        self.assertEqual(pillars["day"]["hanja"], "癸未")
        self.assertEqual(pillars["hour"]["hanja"], "乙卯")

    def test_same_literal_clock_time_gives_different_pillars_in_berlin_vs_seoul(self):
        # 이게 바로 실측으로 발견한 버그의 핵심 증거: 도시만 바꿨는데 일간(본인
        # 자신, 일주의 천간)까지 달라지면 안 되는 게 아니라 — 실제 절대적인 출생
        # "순간"이 다르므로 달라지는 게 정상이다. 수정 전에는 오히려 "베를린"과
        # "서울"의 시차를 전혀 반영하지 않아서 시주가 항상 자시 근처로 잘못
        # 쏠렸다. 여기서는 최소한 "시주가 23~01시 자시로 잘못 고정되지 않는다"는
        # 것과, 베를린 결과가 자체적으로 일관되게 재현되는지를 확인한다.
        r_berlin_1 = run_calculation({
            "birth_date": "1991-03-14", "birth_time": "07:30", "birth_city": "Berlin",
        })
        r_berlin_2 = run_calculation({
            "birth_date": "1991-03-14", "birth_time": "07:30", "birth_city": "Berlin",
        })
        # 같은 입력이면 항상 같은 결과(결정론적 계산) — 회귀 안전망.
        self.assertEqual(r_berlin_1["pillars"], r_berlin_2["pillars"])

        # 자시(子時)는 23시/00시대인데, 07:30(아침) 입력이 더 이상 자시로
        # 나오면 안 된다 — 버그 수정 전에는 이게 항상 자시로 잘못 나왔었다.
        hour_ji_ji_hanja = r_berlin_1["pillars"]["hour"]["hanja"][-1]
        self.assertNotEqual(hour_ji_ji_hanja, "子")


if __name__ == "__main__":
    unittest.main()
