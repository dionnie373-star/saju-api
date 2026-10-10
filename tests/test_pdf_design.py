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
    "year": {"hanja": "辛未", "hangul": "신미", "cheon_gan_element": "금", "ji_ji_element": "토"},
    "month": {"hanja": "辛卯", "hangul": "신묘", "cheon_gan_element": "금", "ji_ji_element": "목"},
    "day": {"hanja": "癸未", "hangul": "계미", "cheon_gan_element": "수", "ji_ji_element": "토"},
    "hour": {"hanja": "丙辰", "hangul": "병진", "cheon_gan_element": "화", "ji_ji_element": "토"},
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

    def test_send_report_falls_back_to_default_layout_when_cover_fails(self):
        from unittest import mock
        sent = {}

        def fake_send(**kw):
            sent["size"] = os.path.getsize(kw["attachment_path"])

        ov = pdf_design.build_overview_flowables(
            {"pillars": PILLARS}, hour_known=True, lang="de",
            h2_style=rp._PDF_STYLES["h2"], h2_rule=rp._H2_RULE)
        with mock.patch.object(rp, "send_email", fake_send), \
                mock.patch.object(pdf_design, "draw_cover", side_effect=RuntimeError("boom")):
            rp._send_report(
                email="a@b.c", name="X", pdf_title="T", pdf_subtitle="S", report_text="## A\n\nText",
                email_subject="s", email_html_template="{name_suffix}{geocoding_notice}",
                pdf_filename="t.pdf", pdf_overview_flowables=ov)
        self.assertGreater(sent["size"], 1000)

    def test_hangul_readings_are_standard_and_covered_by_font(self):
        from fontTools.ttLib import TTFont
        from korean_saju.saju.cheon_gan import CheonGan
        from korean_saju.saju.ji_ji import JiJi
        stems = "갑을병정무기경신임계"
        branches = "자축인묘진사오미신유술해"
        self.assertEqual("".join(g.hangul for g in CheonGan), stems)
        self.assertEqual("".join(j.hangul for j in JiJi), branches)
        cmap = TTFont(pdf_design._KO_FONT_PATH).getBestCmap()
        needed = set(stems + branches + "".join(pdf_design.ELEMENT_KO.values()))
        self.assertEqual([c for c in needed if ord(c) not in cmap], [])


if __name__ == "__main__":
    unittest.main()
