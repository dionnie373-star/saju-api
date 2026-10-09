import os
import tempfile
import unittest

import i18n
import report_pipeline as rp


class FrenchMechanicalRulesTest(unittest.TestCase):
    def _issues(self, text, min_words=0):
        return rp.check_mechanical_rules(text, min_words=min_words, lang="fr")

    def test_clean_vous_text_passes(self):
        text = "Votre année commence avec du Bois et de l'Eau. Vous pouvez prendre le temps de vous poser. Or, ce mois reste calme."
        self.assertEqual(self._issues(text), [])

    def test_destin_banned_but_destination_ok(self):
        self.assertTrue(self._issues("Ce n'est pas le destin qui décide."))
        self.assertTrue(self._issues("Votre destinée."))
        self.assertEqual(self._issues("Votre destination favorite."), [])

    def test_informal_tu_flagged(self):
        self.assertTrue(any("tu/toi" in i for i in self._issues("Tu peux prendre ton temps, toi.")))

    def test_german_output_flagged(self):
        german = "Dein Jahr beginnt ruhig und die Energie ist nicht laut. Eine Zeit mit Wasser."
        self.assertTrue(any("독일어" in i for i in self._issues(german)))
        self.assertFalse(any("독일어로 작성" in i for i in self._issues("Votre année commence calmement. Une période avec de l'Eau.")))

    def test_german_leak_and_hanja_flagged(self):
        self.assertTrue(self._issues("Votre élément Holz est fort."))
        self.assertTrue(self._issues("丙午 est une combinaison."))

    def test_wrong_metal_word(self):
        self.assertTrue(self._issues("L'élément Or domine."))

    def test_science_claims_flagged(self):
        self.assertTrue(self._issues("Des études montrent que c'est efficace."))
        self.assertTrue(self._issues("Une approche scientifique."))

    def test_min_words(self):
        self.assertTrue(any("분량 미달" in i for i in self._issues("trop court", min_words=50)))

    def test_german_rules_unchanged(self):
        self.assertTrue(rp.check_mechanical_rules("Sie können das tun.", min_words=0))
        self.assertEqual(rp.check_mechanical_rules("Du kannst das tun.", min_words=0), [])


class FrenchPromptTest(unittest.TestCase):
    def test_override_only_first_message_and_only_for_fr(self):
        self.assertEqual(i18n.localize_prompt_text("abc", "de"), "abc")
        out = i18n.localize_prompt_text("abc", "fr")
        self.assertIn("프랑스어", out)
        self.assertIn("abc", out)
        mid = i18n.localize_prompt_text("독일어 abc", "fr", is_first_message=False, is_last_message=False)
        self.assertEqual(mid, "프랑스어 abc")
        self.assertIn("최종 확인", out)

    def test_all_prompts_build_with_fr(self):
        for name in ("free_report_prompt.json", "paid_report_prompt.json",
                     "premium_report_prompt.json", "compatibility_report_prompt.json"):
            tpl = rp._load_prompt_template(name)
            msgs = rp._build_messages(tpl, {}, "fr", "NOTE")
            self.assertIn("vous", msgs[0]["content"])
            self.assertTrue(msgs[-1]["content"].endswith("NOTE"))

    def test_normalize_lang(self):
        self.assertEqual(i18n.normalize_lang("FR"), "fr")
        self.assertEqual(i18n.normalize_lang("xx"), "de")
        self.assertEqual(i18n.normalize_lang(None), "de")


class FrenchOutputTest(unittest.TestCase):
    def test_email_templates_format(self):
        for kind in ("free", "paid", "premium", "compatibility"):
            tpl = rp._fr_email_template(kind)
            html = tpl.format(name_suffix=" Léa", geocoding_notice="")
            self.assertIn("Bonjour Léa,", html)
            self.assertIn("Mentions légales", html)
            self.assertNotIn("Hallo", html)

    def test_geo_notice_fr(self):
        html = rp._geocoding_fallback_notice_html(["Quimper"], "fr")
        self.assertIn("Paris", html)
        self.assertIn('"Quimper"', html)

    def test_pdf_builds_with_accents(self):
        text = (
            "# 1. Introduction\n\nBonjour, voici votre année : œuvre, Août, « équilibre » — très bien.\n\n"
            "## Janvier — Des ressources qui souhaitent se montrer\n\nÇa va être l'été à Noël, où l'Eau et le Bois se rencontrent.\n"
        )
        with tempfile.TemporaryDirectory() as d:
            out = os.path.join(d, "t.pdf")
            rp.build_pdf(out, title="Votre rapport annuel Saju", subtitle="Établi pour Léa",
                         report_text=text, lang="fr")
            self.assertGreater(os.path.getsize(out), 1000)

    def test_destin_sentence_strip(self):
        out = rp._strip_schicksal_sentences("Bonjour. Ce n'est pas le destin. Merci.", i18n.FR_DESTIN_RE)
        self.assertNotIn("destin", out)
        self.assertIn("Merci", out)


class FrenchLocationTest(unittest.TestCase):
    def test_french_city_known(self):
        import app
        lon, tz, src = app._lookup_location("Paris", "fr")
        self.assertEqual((tz, src), ("Europe/Paris", "known_city"))
        lon, tz, src = app._lookup_location("Lyon", "fr")
        self.assertAlmostEqual(lon, 4.8357, places=3)

    def test_fallback_fr(self):
        import app
        # 지오코딩(네트워크)이 막힌 환경에서도 크래시 없이 프랑스 기본값
        lon, tz, src = app._lookup_location("Zzzzqqq-nowhere", "fr")
        if src == "default_fallback":
            self.assertEqual(tz, "Europe/Paris")


class FrenchSiteRoutesTest(unittest.TestCase):
    def test_pages_served(self):
        import app
        c = app.app.test_client()
        for url in ("/fr/", "/fr/cgv", "/fr/confidentialite", "/fr/retractation", "/fr/mentions-legales"):
            r = c.get(url)
            self.assertEqual(r.status_code, 200, url)
            self.assertIn(b'lang="fr"', r.data)
            self.assertIn(b"noindex", r.data)
        self.assertEqual(c.get("/fr/unknown").status_code, 404)

    def test_fr_index_has_no_german_checkout_leftovers(self):
        import app
        html = app.app.test_client().get("/fr/").data.decode("utf-8")
        self.assertIn("lang: 'fr'", html)
        self.assertNotIn("Digistore24 Inc", html)
        self.assertNotIn("§ 356", html)


if __name__ == "__main__":
    unittest.main()
