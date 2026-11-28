"""결제 완료 집계(order_paid)의 정확성: 같은 IPN 재전송은 한 번만 세고, 상품(tier)별 카운터가 나뉜다."""
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
from tests.test_digistore24_webhook import (  # noqa: E402
    PAID_PRODUCT_ID, _base_form, _valid_paid_order_data,
)

PREMIUM_PRODUCT_ID = "740939"


def _count(ev):
    # DE 사이트의 이벤트는 접미사 없이 저장된다(_enc 참고). 이름이 정확히 일치하는 것만 합산한다.
    return sum(r["n"] for r in orders_store.events_stats(2) if r["ev"] == ev)


class OrderPaidCounterTests(unittest.TestCase):
    def setUp(self):
        app_module.app.config["TESTING"] = True
        app_module.FULFILL_ASYNC = False
        app_module.FULFILL_RETRY_DELAY_SECONDS = 0
        self._orig_alert = app_module._alert_owner
        app_module._alert_owner = lambda *a, **k: None
        self._orig = {n: getattr(report_pipeline, n) for n in ("run_paid_signup", "run_premium_signup")}
        report_pipeline.run_paid_signup = lambda **kw: None
        report_pipeline.run_premium_signup = lambda **kw: None
        orders_store.reset_for_tests()
        app_module._RATE_LIMIT_HISTORY.clear()
        self.client = app_module.app.test_client()

    def tearDown(self):
        app_module._alert_owner = self._orig_alert
        for n, f in self._orig.items():
            setattr(report_pipeline, n, f)
        orders_store.reset_for_tests()

    def _token(self, premium=False):
        data = _valid_paid_order_data()
        if premium:
            data["gender"] = "male"
        resp = self.client.post("/orders/pending", json=data)
        self.assertEqual(resp.status_code, 200, resp.get_json())
        return resp.get_json()["token"]

    def test_same_ipn_twice_counts_once(self):
        form = _base_form("cnt_dup_1", PAID_PRODUCT_ID, "kunde@example.com", self._token())
        self.assertEqual(self.client.post("/webhooks/digistore24", data=form).status_code, 200)
        self.assertEqual(self.client.post("/webhooks/digistore24", data=form).status_code, 200)
        self.assertEqual(_count("order_paid"), 1)
        self.assertEqual(_count("order_paid_annual"), 1)

    def test_different_orders_each_counted_once_and_split_by_tier(self):
        f1 = _base_form("cnt_a", PAID_PRODUCT_ID, "kunde@example.com", self._token())
        f2 = _base_form("cnt_b", PREMIUM_PRODUCT_ID, "kunde@example.com", self._token(premium=True))
        self.client.post("/webhooks/digistore24", data=f1)
        self.client.post("/webhooks/digistore24", data=f2)
        self.assertEqual(_count("order_paid"), 2)
        self.assertEqual(_count("order_paid_annual"), 1)
        self.assertEqual(_count("order_paid_lifetime"), 1)
        self.assertEqual(_count("order_paid_compat"), 0)


if __name__ == "__main__":
    unittest.main()
