"""전 세계 도시 조회: 내장 표, "City, Country" 형식, 지오코딩 국가 필터, 실패 시 표/기본값 폴백.

실행: cd /home/claude/saju-api && python3 -m unittest tests.test_world_cities -v
"""
import io
import json
import os
import unittest
from unittest import mock
from zoneinfo import ZoneInfo

os.environ.setdefault("ANTHROPIC_API_KEY", "test-not-used")

import app as app_module  # noqa: E402
import world_cities  # noqa: E402


class FakeResp(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def fake_geocode(results):
    def _open(req, timeout=5):
        return FakeResp(json.dumps({"results": results}).encode())
    return _open


class WorldCityTests(unittest.TestCase):
    def test_all_timezones_valid_and_lons_sane(self):
        for name, (lon, tz) in world_cities.WORLD_CITIES.items():
            ZoneInfo(tz)
            self.assertTrue(-180 <= lon <= 180, name)
            # 경도와 시간대 오프셋이 크게 어긋나지 않는지(대략 ±4시간 이내)
            off = ZoneInfo(tz).utcoffset(__import__("datetime").datetime(2000, 1, 15)).total_seconds() / 3600
            self.assertLess(abs(lon / 15 - off), 4.0, (name, lon, tz, off))

    def test_known_without_network(self):
        with mock.patch("urllib.request.urlopen", side_effect=OSError("offline")):
            for q, tz in [("Lagos", "Africa/Lagos"), ("Lagos, Nigeria", "Africa/Lagos"), ("MANILA", "Asia/Manila"),
                          ("Ho Chi Minh City", "Asia/Ho_Chi_Minh"), ("Paris, France", "Europe/Paris")]:
                lon, zone, src = app_module._lookup_location(q, "de")
                self.assertEqual((zone, src), (tz, "known_city"), q)

    def test_country_filter_picks_matching_result(self):
        results = [
            {"longitude": -76.5, "timezone": "America/Toronto", "country": "Canada", "country_code": "CA", "admin1": "Ontario"},
            {"longitude": -76.79, "timezone": "America/Jamaica", "country": "Jamaica", "country_code": "JM", "admin1": "Kingston"},
        ]
        with mock.patch("urllib.request.urlopen", fake_geocode(results)):
            lon, tz, src = app_module._lookup_location("Smallville, Jamaica", "de")
            self.assertEqual((tz, src), ("America/Jamaica", "geocoded"))

    def test_unknown_place_falls_back(self):
        with mock.patch("urllib.request.urlopen", side_effect=OSError("offline")):
            self.assertEqual(app_module._lookup_location("Atlantis", "de")[2], "default_fallback")


if __name__ == "__main__":
    unittest.main()
