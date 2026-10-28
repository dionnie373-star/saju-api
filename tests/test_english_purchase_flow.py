"""English page (/en/): real Digistore24 purchase flow, USD prices, no EUR, legal pages, /orders/pending lang=en."""
import os
import re
import unittest

os.environ.setdefault("ANTHROPIC_API_KEY", "test-not-used")
os.environ.setdefault("BREVO_API_KEY", "test-not-used")
os.environ.setdefault("FROM_EMAIL", "test@example.com")
os.environ.setdefault("FROM_NAME", "Palja Test")

import app as app_module  # noqa: E402

ROOT = os.path.join(os.path.dirname(__file__), "..", "static_site", "en")
PAGES = ["index.html", "privacy.html", "legal-notice.html", "terms.html", "refund.html", "thank-you.html"]


def read(name):
    with open(os.path.join(ROOT, name), encoding="utf-8") as f:
        return f.read()


class EnglishPurchasePageTests(unittest.TestCase):
    def setUp(self):
        self.c = app_module.app.test_client()
        self.html = read("index.html")

    def test_product_ids_and_prices(self):
        for pid in ("756320", "756325", "756333"):
            self.assertIn(pid, self.html)
        for pid in ("746476", "746480", "746481", "746748", "746751", "746753", "740708"):
            self.assertNotIn(pid, self.html)
        for price in ("$9.90", "$24.90"):
            self.assertIn(price, self.html)
        self.assertIn("https://www.checkout-ds24.com/product/", self.html)

    def test_buttons_and_containers(self):
        for i in ("resUpsell", "resBuyPaid", "resBuyPremium", "buyPaidBtn", "buyPremiumBtn", "compatibility",
                  "buyCompatBtn", "buyModal", "mBirthdate", "mBirthplace", "mEmail", "mGo", "compatDate_a", "compatDate_b",
                  "compatCity_a", "compatCity_b", "compatEmail"):
            self.assertIn(f'id="{i}"', self.html, i)

    def test_fake_door_removed(self):
        for w in ("resInterest", "resInterestBtn", "resInterestMsg", "Fake door"):
            self.assertNotIn(w, self.html)

    def test_no_euro_or_german_vat_wording(self):
        body = re.sub(r"<svg.*?</svg>", "", self.html, flags=re.S)
        self.assertNotIn("€", body)
        self.assertNotRegex(body, r"\bEUR\b")
        self.assertNotIn("VAT included", body)
        self.assertNotIn("Mehrwertsteuer", body)
        self.assertIn("Taxes may be added at checkout depending on your country", self.html)

    def test_no_withdrawal_waiver_and_no_checkbox(self):
        self.assertNotIn("withdrawal_consent", self.html)
        self.assertNotIn("withdrawalConsent", self.html)
        self.assertNotIn('type="checkbox"', self.html)

    def test_required_notes_and_links(self):
        self.assertIn("Payment is processed by Digistore24.com", self.html)
        self.assertIn("60-day money-back guarantee", self.html)
        for link in ("/en/refund", "/en/terms", "/en/privacy", "/en/legal-notice"):
            self.assertIn(f'href="{link}"', self.html, link)

    def test_footer_and_internal_links_resolve(self):
        links = set()
        for p in PAGES:
            links.update(re.findall(r'href="(/en/[a-z-]*)"', read(p)))
        self.assertTrue(links)
        for link in sorted(links):
            self.assertEqual(self.c.get(link).status_code, 200, link)

    def test_anchor_used_by_email_exists(self):
        import i18n
        self.assertEqual(i18n.STRINGS["en"]["promo_anchor"], "compatibility")
        self.assertIn('id="compatibility"', self.html)

    def test_noindex_kept_and_events(self):
        self.assertIn('content="noindex, nofollow"', self.html)
        for ev in ("view_form", "buy_open", "res_up_view", "res_up_paid", "res_up_premium"):
            self.assertIn(ev, self.html)
        self.assertIn("$('resUpsell')", self.html)
        for ev in ("buy_open", "res_up_view", "res_up_paid", "res_up_premium"):
            self.assertIn(ev, app_module._EV_ALLOWED)

    def test_kept_fixes(self):
        self.assertIn("resPlaceNote", self.html)
        self.assertIn("prefers-reduced-motion", self.html)
        self.assertIn("rh.focus", self.html)

    def test_scripts_balanced(self):
        for js in re.findall(r"<script>(.*?)</script>", self.html, flags=re.S):
            self.assertEqual(js.count("{"), js.count("}"))
            self.assertEqual(js.count("("), js.count(")"))

    def test_legal_pages_describe_paid_orders(self):
        priv = read("privacy.html")
        self.assertNotIn("not offered yet", priv)
        self.assertNotIn("We do not send newsletters or advertising emails. You only receive an email from us if you write to us first.", priv)
        for w in ("Digistore24", "Merchant of Record", "Anthropic", "Brevo", "24 hours"):
            self.assertIn(w, priv)
        legal = read("legal-notice.html")
        self.assertIn("Merchant of Record", legal)
        self.assertIn("Digistore24.com", legal)

    def test_profile_close_points_to_annual_report(self):
        import profile_view
        src = open(profile_view.__file__, encoding="utf-8").read()
        self.assertIn("The annual report shows the year month by month.", src)


class EnglishOrdersPendingTests(unittest.TestCase):
    def setUp(self):
        self.c = app_module.app.test_client()

    def test_pending_order_accepts_lang_en(self):
        import orders_store
        payload = {"email": "reader@example.com", "birth_date": "1990-05-17", "birth_time": "08:30",
                   "birth_city": "Lagos, Nigeria", "lang": "en"}
        r = self.c.post("/orders/pending", json=payload)
        self.assertEqual(r.status_code, 200)
        token = r.get_json()["token"]
        self.assertTrue(orders_store.pending_token_exists(token))

    def test_pending_order_compat_payload_en(self):
        payload = {"email": "reader@example.com", "lang": "en",
                   "birth_date_a": "1990-05-17", "birth_city_a": "Lagos, Nigeria",
                   "birth_date_b": "1992-01-02", "birth_city_b": "Manila, Philippines"}
        r = self.c.post("/orders/pending", json=payload)
        self.assertEqual(r.status_code, 200)

    def test_pending_order_needs_email(self):
        r = self.c.post("/orders/pending", json={"lang": "en", "email": "nope"})
        self.assertEqual(r.status_code, 400)

    def test_en_product_ids_mapped_to_tiers(self):
        m = app_module.DIGISTORE24_PRODUCT_TIER_MAP
        self.assertEqual((m["756320"], m["756325"], m["756333"]), ("paid", "premium", "compatibility"))


class EnglishWebhookFlowTests(unittest.TestCase):
    """/orders/pending (lang=en) -> signed Digistore24 IPN -> English pipeline entry (mocked, no AI/mail)."""

    def setUp(self):
        import orders_store
        from tests import test_digistore24_webhook as w
        self.w, self.store = w, orders_store
        app_module.app.config["TESTING"] = True
        self._flags = (app_module.FULFILL_ASYNC, app_module.FULFILL_RETRY_DELAY_SECONDS, app_module._alert_owner)
        app_module.FULFILL_ASYNC = False
        app_module.FULFILL_RETRY_DELAY_SECONDS = 0
        app_module._alert_owner = lambda *a, **k: None
        orders_store.reset_for_tests()
        app_module._RATE_LIMIT_HISTORY.clear()
        self.c = app_module.app.test_client()

    def tearDown(self):
        app_module.FULFILL_ASYNC, app_module.FULFILL_RETRY_DELAY_SECONDS, app_module._alert_owner = self._flags
        self.store.reset_for_tests()

    def _ipn(self, product_id, data, order_id):
        import report_pipeline
        calls = []
        orig = {n: getattr(report_pipeline, n) for n in ("run_paid_signup", "run_premium_signup", "run_compatibility_signup")}
        try:
            for n in orig:
                setattr(report_pipeline, n, lambda **kw: calls.append(kw))
            token = self.c.post("/orders/pending", json=data).get_json()["token"]
            form = self.w._base_form(order_id, product_id, data["email"], token)
            resp = self.c.post("/webhooks/digistore24", data=form)
        finally:
            for n, f in orig.items():
                setattr(report_pipeline, n, f)
        return resp, calls

    def test_en_paid_order_reaches_pipeline_with_lang_en(self):
        data = {"email": "reader@example.com", "birth_date": "1990-05-17", "birth_time": "08:30",
                "birth_city": "Lagos, Nigeria", "lang": "en"}
        resp, calls = self._ipn("756320", data, "ds24_en_paid")
        self.assertEqual(resp.status_code, 200, resp.get_data(as_text=True))
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]["payload"]["tier"], "paid")
        self.assertEqual(calls[0]["payload"]["lang"], "en")

    def test_en_premium_order_reaches_pipeline(self):
        data = {"email": "reader@example.com", "birth_date": "1990-05-17", "birth_city": "Lagos, Nigeria",
                "gender": "female", "lang": "en"}
        resp, calls = self._ipn("756325", data, "ds24_en_premium")
        self.assertEqual(resp.status_code, 200, resp.get_data(as_text=True))
        self.assertEqual(calls[0]["payload"]["tier"], "premium")

    def test_en_compatibility_order_reaches_pipeline(self):
        data = {"email": "reader@example.com", "lang": "en", "name_a": "Ada", "name_b": "Ben",
                "birth_date_a": "1990-05-17", "birth_city_a": "Lagos, Nigeria",
                "birth_date_b": "1992-01-02", "birth_city_b": "Manila, Philippines"}
        resp, calls = self._ipn("756333", data, "ds24_en_compat")
        self.assertEqual(resp.status_code, 200, resp.get_data(as_text=True))
        self.assertEqual(len(calls), 1)


if __name__ == "__main__":
    unittest.main()
