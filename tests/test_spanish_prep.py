"""스페인어(es) 사전 준비 테스트 — de/fr 동작이 바뀌지 않았는지도 함께 확인."""
import unittest

import i18n
import pdf_design
import report_pipeline as rp

GOOD_ES = (
    "## Tu año de un vistazo\n"
    "Este informe es una reflexión personal basada en la tradición coreana del Saju. "
    "Tienes energía para empezar con calma y ¿qué tal si eliges una sola prioridad? "
    "Madera y Fuego se apoyan en tus pilares. "
)


class SpanishMechanicalTests(unittest.TestCase):
    def issues(self, text):
        return i18n.es_mechanical_issues(text)

    def test_clean_text_passes(self):
        self.assertEqual(self.issues(GOOD_ES), [])

    def test_banned_words(self):
        for bad in ("Es tu destino.", "Un estudio científico lo demuestra.", "Está validado.",
                    "Es la última oportunidad."):
            self.assertTrue(self.issues(bad), bad)

    def test_negated_science_disclaimer_allowed(self):
        t = GOOD_ES + "Es una reflexión, no un diagnóstico de personalidad con base científica."
        self.assertEqual(self.issues(t), [])

    def test_formal_address_rejected(self):
        self.assertTrue(self.issues("Usted puede empezar. Vosotros también."))

    def test_gendered_reader_rejected(self):
        self.assertTrue(self.issues("Hoy estás preparado para todo."))

    def test_oro_and_leaks(self):
        self.assertTrue(self.issues("El elemento Oro domina."))
        self.assertTrue(self.issues("Votre année avec Bois et Feu."))
        self.assertTrue(self.issues("Dein Jahr und der Tag ist nicht leicht."))
        self.assertTrue(self.issues("Your energy and the flow."))

    def test_pipeline_dispatch(self):
        out = rp.check_mechanical_rules("Es tu destino. " * 5, lang="es", min_words=1)
        self.assertTrue(any("destino" in i for i in out))


class LanguageRegistryTests(unittest.TestCase):
    def test_normalize(self):
        self.assertEqual(i18n.normalize_lang("ES"), "es")
        self.assertEqual(i18n.normalize_lang("fr"), "fr")
        self.assertEqual(i18n.normalize_lang("xx"), "de")
        self.assertEqual(i18n.normalize_lang(None), "de")

    def test_prompt_localization(self):
        de = i18n.localize_prompt_text("독일어로 쓰기", "de")
        self.assertEqual(de, "독일어로 쓰기")
        es = i18n.localize_prompt_text("독일어로 쓰기", "es")
        self.assertIn("스페인어", es)
        self.assertNotIn("프랑스어로 쓰기", es)
        fr = i18n.localize_prompt_text("독일어로 쓰기", "fr")
        self.assertIn("프랑스어로 쓰기", fr)
        self.assertIn("tú", es)
        self.assertNotIn("tú", fr)

    def test_string_tables_have_same_keys(self):
        fr, es = i18n.STRINGS["fr"], i18n.STRINGS["es"]
        self.assertEqual(set(fr), set(es))
        for k in ("free", "paid", "premium", "compatibility"):
            self.assertEqual(set(fr[k]), set(es[k]))
        self.assertEqual(set(fr["axis_labels"]), set(es["axis_labels"]))

    def test_pdf_string_tables_have_same_keys(self):
        self.assertEqual(set(pdf_design.STRINGS["de"]), set(pdf_design.STRINGS["es"]))
        self.assertEqual(set(pdf_design.ELEMENT_NAMES["de"]), set(pdf_design.ELEMENT_NAMES["es"]))

    def test_email_template_es(self):
        for kind in ("free", "paid", "premium", "compatibility"):
            html = rp._fr_email_template(kind, "es")
            self.assertIn("Hola", html)
            self.assertIn("{geocoding_notice}", html)
            self.assertNotIn("Bonjour", html)
        self.assertIn("/es/", rp._lang_url("es/aviso-legal", "es"))

    def test_doc_strings_es(self):
        t, st, fn, subj, tpl = rp._doc_strings("paid", "es", "Ana")
        self.assertEqual(fn, "Palja-Informe-anual.pdf")
        self.assertIn("Ana", st)

    def test_fr_email_unchanged_links(self):
        html = rp._fr_email_template("paid", "fr")
        self.assertIn("#compatibilite", html)
        self.assertIn("mentions-legales", html)

    def test_geo_notice_es(self):
        self.assertIn("Madrid", rp._geocoding_fallback_notice_html(["X"], lang="es"))
        self.assertIn("Paris", rp._geocoding_fallback_notice_html(["X"], lang="fr"))


class SpanishLocationTests(unittest.TestCase):
    def test_known_cities_and_fallback(self):
        import app
        lon, tz, src = app._lookup_location("Madrid", "es")
        self.assertEqual((tz, src), ("Europe/Madrid", "known_city"))
        _, tz, _ = app._lookup_location("Ciudad de México", "es")
        self.assertEqual(tz, "America/Mexico_City")
        _, tz, _ = app._lookup_location("Buenos Aires", "es")
        self.assertEqual(tz, "America/Argentina/Buenos_Aires")

    def test_all_timezones_valid(self):
        from zoneinfo import ZoneInfo
        import app
        for k, (_lon, tz) in app._ES_CITIES.items():
            ZoneInfo(tz)


if __name__ == "__main__":
    unittest.main()


class SpanishSiteTests(unittest.TestCase):
    def setUp(self):
        import app
        self.c = app.app.test_client()

    def test_pages_served_and_noindex(self):
        for p in ("", "aviso-legal", "condiciones", "privacidad", "desistimiento", "contacto", "gracias"):
            r = self.c.get("/es/" + p)
            self.assertEqual(r.status_code, 200, p)
            body = r.get_data(as_text=True)
            self.assertIn('lang="es"', body)
            self.assertIn("noindex", body, p)

    def test_no_french_or_german_leftovers_in_index(self):
        import re
        body = self.c.get("/es/").get_data(as_text=True)
        body = re.sub(r"<svg.*?</svg>", "", body, flags=re.S)
        body = re.sub(r"//[^\n]*", "", body)
        for w in ("Veuillez", "Paiement", "Rétractation", "Bitte", "Datenschutz", "votre ", "/fr/"):
            self.assertNotIn(w, body, w)

    def test_no_live_product_ids(self):
        body = self.c.get("/es/").get_data(as_text=True)
        for pid in ("746476", "746480", "746481"):
            self.assertNotIn(pid, body)
        self.assertNotIn("trusted-badge", body)

    def test_unknown_page_404(self):
        self.assertEqual(self.c.get("/es/nope").status_code, 404)

    def test_contact_and_signup_messages_es(self):
        r = self.c.post("/kontakt/senden", json={"lang": "es", "email": "bad", "message": "x"})
        self.assertEqual(r.status_code, 400)
        self.assertIn("correo", r.get_json()["error"])
