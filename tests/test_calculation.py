"""run_calculation()의 순수 계산 로직에 대한 회귀 테스트 (표준 라이브러리 unittest만 사용
— 이 환경에서 pytest를 pip로 설치할 수 없어서, 의존성 없이 항상 돌아가게 만듦).

네트워크 호출이 전혀 없다: "Berlin"은 KNOWN_CITY_LONGITUDE 내장 표에 있어서
지오코딩 API를 타지 않는다. 사주 계산(korean_saju) 자체가 잘못 건드려져서
결과가 조용히 깨지는 것을 잡기 위한 스모크 테스트다.

실행: cd /home/claude/saju-api && python3 -m unittest discover tests -v
"""
import os
import unittest

os.environ.setdefault("ANTHROPIC_API_KEY", "test-not-used")
os.environ.setdefault("BREVO_API_KEY", "test-not-used")
os.environ.setdefault("FROM_EMAIL", "test@example.com")
os.environ.setdefault("FROM_NAME", "Palja Test")

from app import CalcError, run_calculation  # noqa: E402

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


if __name__ == "__main__":
    unittest.main()
