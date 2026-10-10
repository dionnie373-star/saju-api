import os, unittest
import app as appmod

class FrHostTests(unittest.TestCase):
    def setUp(self):
        self.c = appmod.app.test_client()
        os.environ.pop("FR_PUBLIC", None)

    def get(self, path, host="palja.fr"):
        return self.c.get(path, headers={"Host": host})

    def test_pages_ok_and_rewritten(self):
        for p in ["/", "/cgv", "/mentions-legales", "/confidentialite", "/retractation", "/contact", "/merci"]:
            r = self.get(p)
            self.assertEqual(r.status_code, 200, p)
        t = self.get("/").get_data(as_text=True)
        self.assertIn("https://palja.fr/", t)
        self.assertNotIn("https://palja.de/fr/", t)
        self.assertIn("noindex", t)  # 공개 전

    def test_private_until_flag(self):
        self.assertIn("Disallow: /\n", self.get("/robots.txt").get_data(as_text=True))

    def test_public_flag(self):
        os.environ["FR_PUBLIC"] = "1"
        try:
            t = self.get("/").get_data(as_text=True)
            self.assertNotIn("noindex", t)
            self.assertIn('rel="canonical" href="https://palja.fr/"', t)
            rb = self.get("/robots.txt").get_data(as_text=True)
            self.assertIn("Allow: /", rb)
            self.assertIn("palja.fr/sitemap.xml", rb)
            self.assertIn("palja.fr/cgv", self.get("/sitemap.xml").get_data(as_text=True))
            self.assertIn("noindex", self.get("/merci").get_data(as_text=True))
            self.assertIn("palja.fr", self.get("/cgv").get_data(as_text=True))
        finally:
            os.environ.pop("FR_PUBLIC", None)

    def test_de_host_unchanged(self):
        t = self.get("/fr/", host="palja.de").get_data(as_text=True)
        self.assertIn("noindex", t)
        self.assertEqual(self.get("/", host="palja.de").status_code, 200)

if __name__ == "__main__":
    unittest.main()
