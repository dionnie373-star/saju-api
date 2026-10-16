"""무료 신청 메타(출처/관심사) 기록 + 관리자 집계 테스트."""
import os
import unittest
from unittest import mock

os.environ.setdefault("ADMIN_TEST_TOKEN", "x" * 32)

import app as app_module  # noqa: E402
import orders_store  # noqa: E402


class SignupMetaTest(unittest.TestCase):
    def setUp(self):
        orders_store.reset_for_tests()
        app_module._RATE_LIMIT_HISTORY.clear()
        self.c = app_module.app.test_client()

    def _signup(self, **extra):
        body = {"birth_date": "1994-05-05", "birth_city": "Berlin", "email": "a%d@example.com" % len(extra) + str(id(extra))}
        body.update(extra)
        with mock.patch("report_pipeline.run_free_signup"):
            return self.c.post("/signup", json=body)

    def test_records_whitelisted_values_only(self):
        self.assertEqual(self._signup(src="yt-profile", interest="self", lang="de").status_code, 200)
        self._signup(src="Evil<script>", interest="hack", lang="de", x=1)
        tok = os.environ["ADMIN_TEST_TOKEN"]
        r = self.c.get("/admin/signup-stats", headers={"X-Admin-Token": tok}).get_json()
        self.assertEqual(r["total"], 2)
        keys = {(x["src"], x["interest"]) for x in r["rows"]}
        self.assertEqual(keys, {("yt-profile", "self"), ("none", "none")})

    def test_no_pii_in_rows(self):
        self._signup(src="th-bio", interest="korea", lang="de")
        tok = os.environ["ADMIN_TEST_TOKEN"]
        r = self.c.get("/admin/signup-stats", headers={"X-Admin-Token": tok})
        self.assertNotIn(b"example.com", r.data)

    def test_stats_requires_token(self):
        self.assertEqual(self.c.get("/admin/signup-stats").status_code, 401)


if __name__ == "__main__":
    unittest.main()
