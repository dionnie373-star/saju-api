"""제휴 추적: 판매 페이지가 ?aff=ID 를 주문서 링크에 aff 로 전달하고, 제3자 스크립트는 로드하지 않는다."""
import re
import unittest
from pathlib import Path

PAGES = ["static_site/index.html", "static_site/fr/index.html", "static_site/es/index.html"]
ROOT = Path(__file__).resolve().parent.parent


class AffiliateParamTest(unittest.TestCase):
    def test_pages_pass_aff_to_order_form(self):
        for p in PAGES:
            s = (ROOT / p).read_text(encoding="utf-8")
            self.assertIn("var affiliateId", s, p)
            self.assertIn("params.set('aff', affiliateId)", s, p)
            self.assertTrue(re.search(r"\[A-Za-z0-9_-\]\{2,40\}", s), p)

    def test_no_digistore_third_party_script(self):
        for p in PAGES:
            s = (ROOT / p).read_text(encoding="utf-8")
            self.assertNotIn("digistore24-scripts.com", s, p)


if __name__ == "__main__":
    unittest.main()
