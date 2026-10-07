"""Fungies 웹훅(/webhooks/fungies) 회귀 테스트 — Digistore24 테스트와 같은 방식."""
import hashlib
import hmac
import json
import os
import unittest

os.environ.setdefault("PADDLE_WEBHOOK_SECRET", "test_secret_for_pytest")
os.environ.setdefault("DIGISTORE24_SHA_PASSPHRASE", "test_ds24_passphrase")
os.environ.setdefault("ANTHROPIC_API_KEY", "test-not-used")
os.environ.setdefault("BREVO_API_KEY", "test-not-used")
os.environ.setdefault("FROM_EMAIL", "test@example.com")
os.environ.setdefault("FROM_NAME", "Palja Test")

import app as app_module  # noqa: E402
import orders_store  # noqa: E402
import report_pipeline  # noqa: E402

SECRET = "fungies_test_secret"
OFFER = "offer_paid_test"


def _sig(body: bytes, secret=SECRET):
    return "sha256_" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def _event(token, offer=OFFER, etype="payment_success", order_id="ord_1", status="PAID"):
    return {
        "id": "evt_" + order_id,
        "type": etype,
        "testMode": False,
        "data": {
            "items": [{"offer": {"id": "uuid-x", "internalId": offer},
                       "customFields": {"order_token": token}}],
            "order": {"id": order_id, "status": status},
            "user": {"email": "kunde@example.com"},
        },
    }


class FungiesWebhookTests(unittest.TestCase):
    def setUp(self):
        app_module.app.config["TESTING"] = True
        orders_store.reset_for_tests()
        app_module._RATE_LIMIT_HISTORY.clear()
        self.client = app_module.app.test_client()
        os.environ["FUNGIES_WEBHOOK_SECRET"] = SECRET
        app_module.FUNGIES_OFFER_TIER_MAP.clear()
        app_module.FUNGIES_OFFER_TIER_MAP[OFFER] = "paid"
        self._orig = report_pipeline.run_paid_signup
        self.calls = []
        report_pipeline.run_paid_signup = lambda **kw: self.calls.append(kw)

    def tearDown(self):
        report_pipeline.run_paid_signup = self._orig
        app_module.FUNGIES_OFFER_TIER_MAP.clear()
        orders_store.reset_for_tests()

    def _token(self):
        data = {"email": "kunde@example.com", "name": "T", "birth_date": "1990-05-15",
                "birth_time": "14:30", "birth_city": "Berlin", "withdrawal_consent": True}
        r = self.client.post("/orders/pending", json=data)
        self.assertEqual(r.status_code, 200)
        return r.get_json()["token"]

    def _post(self, ev, sig=None):
        body = json.dumps(ev).encode()
        return self.client.post("/webhooks/fungies", data=body,
                                headers={"x-fngs-signature": sig or _sig(body),
                                         "Content-Type": "application/json"})

    def test_bad_signature_rejected(self):
        resp = self._post(_event(self._token()), sig="sha256_deadbeef")
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(self.calls, [])

    def test_missing_signature_rejected(self):
        body = json.dumps(_event(self._token())).encode()
        resp = self.client.post("/webhooks/fungies", data=body, content_type="application/json")
        self.assertEqual(resp.status_code, 403)

    def test_other_event_ignored(self):
        resp = self._post(_event(self._token(), etype="payment_refunded"))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(self.calls, [])

    def test_valid_payment_sends_report_and_consumes_token(self):
        token = self._token()
        resp = self._post(_event(token))
        self.assertEqual(resp.status_code, 200, resp.get_data(as_text=True))
        self.assertEqual(len(self.calls), 1)
        self.assertEqual(self.calls[0]["payload"]["tier"], "paid")
        self.assertFalse(orders_store.pending_token_exists(token))

    def test_duplicate_order_not_resent(self):
        token = self._token()
        self._post(_event(token))
        resp = self._post(_event(token))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(self.calls), 1)

    def test_unknown_offer_rejected(self):
        resp = self._post(_event(self._token(), offer="nope"))
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(self.calls, [])

    def test_unknown_token_rejected_and_not_marked(self):
        resp = self._post(_event("made_up"))
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(self.calls, [])

    def test_failed_pipeline_allows_retry(self):
        def boom(**kw):
            raise report_pipeline.PipelineError("x", 502)
        report_pipeline.run_paid_signup = boom
        token = self._token()
        self.assertEqual(self._post(_event(token)).status_code, 502)
        self.assertTrue(orders_store.pending_token_exists(token))
        report_pipeline.run_paid_signup = lambda **kw: self.calls.append(kw)
        self.assertEqual(self._post(_event(token)).status_code, 200)
        self.assertEqual(len(self.calls), 1)


if __name__ == "__main__":
    unittest.main()
