"""/profile (웹 즉시 결과) 회귀 테스트: 이메일 없이 동작, 4개 언어 문구 치환 누락·금지어 없음, 시주 모름 처리, 레이트리밋.

실행: cd /home/claude/saju-api && python3 -m unittest tests.test_profile_view -v
"""
import os
import unittest

os.environ.setdefault("ANTHROPIC_API_KEY", "test-not-used")
os.environ.setdefault("BREVO_API_KEY", "test-not-used")
os.environ.setdefault("FROM_EMAIL", "test@example.com")
os.environ.setdefault("FROM_NAME", "Palja Test")

import app as app_module  # noqa: E402
import report_pipeline as rp  # noqa: E402

CASES = [("1990-05-15", "Berlin"), ("1985-11-03", "Paris"), ("1978-02-20", "Madrid"), ("2001-07-30", "Hamburg"), ("1969-12-31", "Wien")]


class ProfileViewTests(unittest.TestCase):
    def setUp(self):
        app_module._RATE_LIMIT_HISTORY.clear()
        self.c = app_module.app.test_client()

    def post(self, **kw):
        app_module._RATE_LIMIT_HISTORY.clear()
        return self.c.post("/profile", json=kw)

    def test_no_email_needed_and_no_input_echo(self):
        r = self.post(birth_date="1990-05-15", birth_city="Berlin", lang="de").get_json()
        self.assertTrue(r["ok"])
        self.assertNotIn("birth_date", r)
        self.assertNotIn("birth_city", r)
        self.assertEqual(len(r["counts"]), 5)
        self.assertEqual(len(r["sections"]), 3)

    def test_hour_unknown(self):
        r = self.post(birth_date="1990-05-15", birth_time="", birth_city="Berlin", lang="de").get_json()
        self.assertFalse(r["hour_known"])
        self.assertIsNone(r["pillars"]["hour"])
        self.assertEqual(r["total"], 6)
        self.assertIn("Ohne Geburtszeit", r["sections"][1]["text"])
        r2 = self.post(birth_date="1990-05-15", birth_time="14:00", birth_city="Berlin", lang="de").get_json()
        self.assertTrue(r2["hour_known"])
        self.assertEqual(r2["total"], 8)

    def test_all_languages_clean(self):
        for lang in ("de", "fr", "es", "en"):
            for d, city in CASES:
                for bt in ("", "14:00"):
                    r = self.post(birth_date=d, birth_time=bt, birth_city=city, lang=lang).get_json()
                    self.assertTrue(r["ok"], (lang, d, r))
                    txt = "\n".join(s["text"] for s in r["sections"])
                    self.assertNotIn("{", txt)
                    self.assertNotIn("}", txt)
                    if lang != "en":
                        self.assertEqual(rp.check_mechanical_rules(txt, min_words=0, lang=lang), [], (lang, d))

    def test_bad_input_localized(self):
        r = self.post(birth_date="", birth_city="Berlin", lang="fr")
        self.assertEqual(r.status_code, 400)
        self.assertIn("vérifier", r.get_json()["error"])

    def test_rate_limit(self):
        app_module._RATE_LIMIT_HISTORY.clear()
        codes = [self.c.post("/profile", json={"birth_date": "1990-05-15", "birth_city": "Berlin"}).status_code for _ in range(31)]
        self.assertEqual(codes[:30], [200] * 30)
        self.assertEqual(codes[30], 429)

    def test_events_allowed(self):
        for ev in ("res_ok", "res_up_paid", "res_up_premium", "res_pdf_ok"):
            self.assertIn(ev, app_module._EV_ALLOWED)


if __name__ == "__main__":
    unittest.main()


class ProfilePlaceTests(unittest.TestCase):
    def test_unknown_place_with_time_is_rejected_without_time_ok(self):
        orig = app_module._lookup_location
        app_module._lookup_location = lambda city, lang="de": (10.45, "Europe/Berlin", "default_fallback")
        try:
            c = app_module.app.test_client()
            app_module._RATE_LIMIT_HISTORY.clear()
            r = c.post("/profile", json={"birth_date": "1990-05-15", "birth_time": "14:00", "birth_city": "Nowhereville", "lang": "en"})
            self.assertEqual(r.status_code, 422)
            self.assertEqual(r.get_json()["code"], "place_not_found")
            app_module._RATE_LIMIT_HISTORY.clear()
            r = c.post("/profile", json={"birth_date": "1990-05-15", "birth_time": "", "birth_city": "Nowhereville", "lang": "en"})
            self.assertEqual(r.status_code, 200)
        finally:
            app_module._lookup_location = orig


class EnglishPilotPageTests(unittest.TestCase):
    def test_en_page_served_noindex(self):
        c = app_module.app.test_client()
        r = c.get("/en/")
        self.assertEqual(r.status_code, 200)
        body = r.get_data(as_text=True)
        self.assertIn('id="resultSection"', body)
        self.assertIn("noindex", body)
        self.assertEqual(c.get("/en").status_code, 302)
