import os, unittest
import app as appmod
import orders_store


class DashboardTests(unittest.TestCase):
    def setUp(self):
        self.c = appmod.app.test_client()
        orders_store.reset_for_tests()
        os.environ.pop("ADMIN_DASH_PASSWORD", None)

    def tearDown(self):
        os.environ.pop("ADMIN_DASH_PASSWORD", None)

    def _auth(self, pw):
        import base64
        return {"Authorization": "Basic " + base64.b64encode(f"x:{pw}".encode()).decode()}

    def test_404_when_unset(self):
        self.assertEqual(self.c.get("/admin/dashboard").status_code, 404)

    def test_401_wrong_or_missing(self):
        os.environ["ADMIN_DASH_PASSWORD"] = "correct-horse-battery"
        self.assertEqual(self.c.get("/admin/dashboard").status_code, 401)
        self.assertEqual(self.c.get("/admin/dashboard", headers=self._auth("nope")).status_code, 401)

    def test_short_password_treated_as_unset(self):
        os.environ["ADMIN_DASH_PASSWORD"] = "short"
        self.assertEqual(self.c.get("/admin/dashboard", headers=self._auth("short")).status_code, 404)

    def test_hit_counts_humans_not_bots_and_shows_on_dashboard(self):
        ua = {"User-Agent": "Mozilla/5.0 (iPhone) Safari"}
        self.c.post("/api/hit", json={"src": "tt-bio", "path": "/"}, headers=ua)
        self.c.post("/api/hit", json={"src": "tt-bio", "path": "/"}, headers=ua)
        self.c.post("/api/hit", json={"src": "BAD SRC!", "path": "/x y"}, headers=ua)
        self.c.post("/api/hit", json={"src": "tt-bio"}, headers={"User-Agent": "Googlebot/2.1"})
        self.c.post("/api/hit", json={"src": "tt-bio"}, headers={"User-Agent": ""})
        os.environ["ADMIN_DASH_PASSWORD"] = "correct-horse-battery"
        r = self.c.get("/admin/dashboard", headers=self._auth("correct-horse-battery"))
        self.assertEqual(r.status_code, 200)
        t = r.get_data(as_text=True)
        self.assertIn("tt-bio", t)
        self.assertIn("<b>3</b>페이지뷰", t)
        self.assertIn("noindex", r.headers.get("X-Robots-Tag", ""))
        self.assertEqual(r.headers.get("Cache-Control"), "no-store")

    def test_signup_shows_up(self):
        orders_store.record_signup_meta("ig-bio", "self", "de")
        os.environ["ADMIN_DASH_PASSWORD"] = "correct-horse-battery"
        t = self.c.get("/admin/dashboard", headers=self._auth("correct-horse-battery")).get_data(as_text=True)
        self.assertIn("ig-bio", t)
        self.assertIn("<b>1</b>무료 프로필", t)

    def test_sites_are_split_by_host_and_path(self):
        ua = {"User-Agent": "Mozilla/5.0 (iPhone) Safari"}
        self.c.post("/api/hit", json={"src": "ig-bio", "path": "/en/"}, headers=ua)
        self.c.post("/api/hit", json={"src": "ig-bio", "path": "/"}, headers=ua)
        self.c.post("/api/hit", json={"src": "tt-bio", "path": "/"}, headers={**ua, "Host": "palja.fr"})
        self.c.post("/api/ev", json={"ev": "res_up_paid", "src": "ig-bio"}, headers={**ua, "Referer": "https://palja.de/en/"})
        os.environ["ADMIN_DASH_PASSWORD"] = "correct-horse-battery"
        t = self.c.get("/admin/dashboard", headers=self._auth("correct-horse-battery")).get_data(as_text=True)
        import re
        row = lambda lbl: re.search(r"<tr><td>" + re.escape(lbl) + r"</td>(.*?)</tr>", t).group(1)
        self.assertEqual(row("palja.de (DE)"), "<td>1</td><td>0</td><td>0</td><td>0</td>")
        self.assertEqual(row("palja.one·/en (EN)"), "<td>1</td><td>0</td><td>1</td><td>0</td>")
        self.assertEqual(row("palja.fr (FR)"), "<td>1</td><td>0</td><td>0</td><td>0</td>")
        self.assertEqual(row("palja.es (ES)"), "<td>0</td><td>0</td><td>0</td><td>0</td>")
        self.assertEqual(orders_store.split_site("/x|fr"), ("/x", "fr"))
        self.assertEqual(orders_store.split_site("/x"), ("/x", "de"))
        self.assertIn("<b>3</b>페이지뷰", t)


if __name__ == "__main__":
    unittest.main()
