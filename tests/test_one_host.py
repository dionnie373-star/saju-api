import unittest
import app as appmod


class OneHostTests(unittest.TestCase):
    def setUp(self):
        self.c = appmod.app.test_client()

    def test_root_serves_english_public_page_with_canonical(self):
        r = self.c.get("/", headers={"Host": "palja.one"})
        t = r.get_data(as_text=True)
        self.assertEqual(r.status_code, 200)
        self.assertIn("buyPaidBtn", t)
        self.assertNotIn('name="robots" content="noindex', t)
        self.assertIn('rel="canonical" href="https://palja.one/"', t)

    def test_subpages_robots_and_sitemap(self):
        h = {"Host": "www.palja.one"}
        self.assertIn("Sitemap: https://palja.one/sitemap.xml", self.c.get("/robots.txt", headers=h).get_data(as_text=True))
        self.assertIn("https://palja.one/en/privacy", self.c.get("/sitemap.xml", headers=h).get_data(as_text=True))
        self.assertEqual(self.c.get("/en/privacy", headers=h).status_code, 200)
        ty = self.c.get("/en/thank-you", headers=h).get_data(as_text=True)
        self.assertIn("noindex", ty)

    def test_main_domain_en_pages_stay_noindex(self):
        t = self.c.get("/en/", headers={"Host": "palja.de"}).get_data(as_text=True)
        self.assertIn('content="noindex', t)
        self.assertEqual(self.c.get("/", headers={"Host": "palja.de"}).status_code, 200)
