import unittest
import app as appmod


class CompatPreviewTest(unittest.TestCase):
    def setUp(self):
        self.c = appmod.app.test_client()
        self.body = {"lang": "fr", "birth_date_a": "1990-05-14", "birth_city_a": "Paris",
                     "birth_date_b": "1992-11-03", "birth_city_b": "Lyon"}

    def test_preview_no_personal_data(self):
        r = self.c.post("/compat-preview", json=self.body)
        self.assertEqual(r.status_code, 200)
        j = r.get_json()
        self.assertTrue(j["ok"])
        self.assertIn("pattern_name", j)
        self.assertEqual(len(j["a"]["counts"]), 5)
        txt = r.get_data(as_text=True)
        for s in ("1990", "Paris", "Lyon", "1992"):
            self.assertNotIn(s, txt)

    def test_card_png(self):
        for lang in ("de", "fr", "es", "en"):
            self.body["lang"] = lang
            r = self.c.post("/compat-card", json=self.body)
            self.assertEqual(r.status_code, 200)
            self.assertTrue(r.data.startswith(b"\x89PNG"))

    def test_bad_date(self):
        self.body["birth_date_b"] = ""
        self.assertEqual(self.c.post("/compat-preview", json=self.body).status_code, 400)


if __name__ == "__main__":
    unittest.main()
