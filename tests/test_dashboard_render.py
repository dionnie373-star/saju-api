"""대시보드가 에러 없이 렌더되고, 결제 완료가 상품별로 나뉘어 보이며, '구매 시도 인원'으로 오해될 라벨이 없는지 확인."""
import base64
import os
import unittest

os.environ.setdefault("ADMIN_DASH_PASSWORD", "dash_test_pw")
os.environ.setdefault("ANTHROPIC_API_KEY", "test-not-used")

import app as app_module  # noqa: E402
import orders_store  # noqa: E402


class DashboardRenderTests(unittest.TestCase):
    def setUp(self):
        app_module.app.config["TESTING"] = True
        orders_store.reset_for_tests()
        self.client = app_module.app.test_client()
        pw = os.environ["ADMIN_DASH_PASSWORD"]
        self.hdr = {"Authorization": "Basic " + base64.b64encode(f"u:{pw}".encode()).decode()}

    def tearDown(self):
        orders_store.reset_for_tests()

    def test_dashboard_renders_with_tier_rows(self):
        for ev in ("order_paid", "order_paid_annual", "order_paid", "order_paid_lifetime", "buy_open", "res_up_paid"):
            orders_store.record_event("none", ev, "de")
        r = self.client.get("/admin/dashboard", headers=self.hdr)
        self.assertEqual(r.status_code, 200)
        body = r.get_data(as_text=True)
        for label in ("└ 연간 리포트", "└ 일생(프리미엄)", "└ 궁합", "상품 구분 도입 전 결제"):
            self.assertIn(label, body)
        self.assertIn("구매 관련 이벤트 횟수(중복 포함)", body)
        self.assertNotIn("<th>구매 클릭</th>", body)
