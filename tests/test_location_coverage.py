import unittest
from zoneinfo import ZoneInfo
import app


class LocationCoverageTests(unittest.TestCase):
    def test_all_builtin_timezones_valid(self):
        for city, tz in app.KNOWN_CITY_TIMEZONE.items():
            ZoneInfo(tz)  # raises if invalid
            self.assertIn(city, app.KNOWN_CITY_LONGITUDE)

    def test_longitude_matches_timezone_roughly(self):
        # 경도와 표준시 오프셋이 크게 어긋나면(>30°) 표 입력 오류 가능성
        from datetime import datetime
        for city, lon in app.KNOWN_CITY_LONGITUDE.items():
            off = ZoneInfo(app.KNOWN_CITY_TIMEZONE[city]).utcoffset(datetime(2000, 1, 15)).total_seconds() / 3600
            self.assertLess(abs(lon - off * 15), 30, city)

    def test_francophone_overseas_and_mexico_known(self):
        for city, lang in [("Québec", "fr"), ("Montréal", "fr"), ("Dakar", "fr"), ("México", "es"), ("Mexico", "es")]:
            _, _, src = app._lookup_location(city, lang)
            self.assertEqual(src, "known_city", city)


if __name__ == "__main__":
    unittest.main()
