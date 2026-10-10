import os
import tempfile
import unittest

os.environ.setdefault("ANTHROPIC_API_KEY", "test-not-used")
os.environ.setdefault("BREVO_API_KEY", "test-not-used")
os.environ.setdefault("FROM_EMAIL", "test@example.com")
os.environ.setdefault("FROM_NAME", "Palja Test")

import pdf_design
import report_pipeline as rp

PILLARS = {
    "year": {"hanja": "辛未", "cheon_gan_element": "금", "ji_ji_element": "토"},
    "month": {"hanja": "辛卯", "cheon_gan_element": "금", "ji_ji_element": "목"},
    "day": {"hanja": "癸未", "cheon_gan_element": "수", "ji_ji_element": "토"},
    "hour": {"hanja": "丙辰", "cheon_gan_element": "화", "ji_ji_element": "토"},
}


class PdfDesignTests(unittest.TestCase):
    def test_counts_include_hour_when_known(self):
        c = pdf_design.count_elements(PILLARS, hour_known=True)
        self.assertEqual(sum(c.values()), 8)
        self.assertEqual(c["토"], 3)

    def test_counts_exclude_hour_when_unknown(self):
        c = pdf_design.count_elements(PILLARS, hour_known=False)
        self.assertEqual(sum(c.values()), 6)
        self.assertEqual(c["화"], 0)

    def test_cover_pdf_builds_for_both_languages(self):
        for lang in ("de", "fr"):
            for known in (True, False):
                ov = pdf_design.build_overview_flowables(
                    {"pillars": PILLARS}, hour_known=known, lang=lang,
                    h2_style=rp._PDF_STYLES["h2"], h2_rule=rp._H2_RULE)
                with tempfile.TemporaryDirectory() as d:
                    out = os.path.join(d, "t.pdf")
                    rp.build_pdf(out, title="Titel", subtitle="Untertitel", report_text="## A\n\nText",
                                 lang=lang, cover=True, overview_flowables=ov)
                    self.assertGreater(os.path.getsize(out), 10000)

    def test_default_build_unchanged_without_cover(self):
        with tempfile.TemporaryDirectory() as d:
            out = os.path.join(d, "t.pdf")
            rp.build_pdf(out, title="Titel", subtitle="Untertitel", report_text="## A\n\nText")
            self.assertTrue(os.path.exists(out))


if __name__ == "__main__":
    unittest.main()
