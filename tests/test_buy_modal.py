"""구매 버튼은 입력창(모달)을 열고 Digistore24로 이동하며, 철회권 포기 체크박스는 없다(2026-10-14, Digistore24 컴플라이언스)."""
import os
import re
import unittest

ROOT = os.path.join(os.path.dirname(__file__), "..", "static_site")
PAGES = ["index.html", "fr/index.html", "es/index.html"]


class BuyModalTest(unittest.TestCase):
    def _read(self, p):
        with open(os.path.join(ROOT, p), encoding="utf-8") as f:
            return f.read()

    def test_no_withdrawal_waiver_checkbox(self):
        for p in PAGES:
            s = self._read(p)
            self.assertNotIn("withdrawalConsent", s, p)
            self.assertNotIn("compatConsent", s, p)
            self.assertNotIn("withdrawal_consent", s, p)

    def test_buy_buttons_open_modal_with_fields(self):
        for p in PAGES:
            s = self._read(p)
            self.assertIn('id="buyModal"', s, p)
            for fid in ("mBirthdate", "mBirthplace", "mEmail", "mGo"):
                self.assertIn(f'id="{fid}"', s, p)
            self.assertIn("openBuyModal('paid')", s, p)
            self.assertIn("openBuyModal('premium')", s, p)

    def test_scripts_parse_balanced(self):
        for p in PAGES:
            js = re.findall(r"<script>(.*?)</script>", self._read(p), flags=re.S)[0]
            self.assertEqual(js.count("{"), js.count("}"), p)


if __name__ == "__main__":
    unittest.main()
