import unittest
import app as appmod


class WissenTest(unittest.TestCase):
    def setUp(self):
        self.c = appmod.app.test_client()

    def test_index_and_articles(self):
        for path in ("/wissen", "/wissen/", "/wissen/chinesisches-horoskop-2027", "/wissen/jahr-des-feuer-schafs-2027"):
            r = self.c.get(path)
            self.assertEqual(r.status_code, 200, path)
        t = self.c.get("/wissen/chinesisches-horoskop-2027").get_data(as_text=True)
        self.assertIn("丁未", t)
        self.assertIn("src=cta-horoskop-2027", t)
        self.assertIn("canonical", t)

    def test_unknown_and_traversal(self):
        self.assertEqual(self.c.get("/wissen/gibt-es-nicht").status_code, 404)
        self.assertEqual(self.c.get("/wissen/..%2Fapp").status_code, 404)

    def test_not_on_fr_host(self):
        r = self.c.get("/wissen/chinesisches-horoskop-2027", headers={"Host": "palja.fr"})
        self.assertEqual(r.status_code, 404)


if __name__ == "__main__":
    unittest.main()
