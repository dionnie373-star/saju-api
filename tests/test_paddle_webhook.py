"""Paddle 웹훅(/webhooks/paddle) 회귀 테스트 (표준 라이브러리 unittest만 사용
— 이 환경에서 pytest를 pip로 설치할 수 없어서, 의존성 없이 항상 돌아가게 만듦).

과거에 실제로 발생했던 문제들(서명 검증, 동의 체크 우회, 중복 결제 재전송으로
인한 리포트 중복 발송)이 다시 생기지 않도록 지키는 최소한의 안전망이다.
외부 서비스(Anthropic/Brevo)는 절대 호출하지 않는다 — report_pipeline의
run_*_signup 함수들을 monkeypatch로 가짜 함수로 바꿔서 "웹훅 라우팅/검증
로직"만 검증한다. run_calculation()은 순수 계산(캘린더/오행)이라 실제로
호출해도 네트워크 요청이 없다.

실행: cd /home/claude/saju-api && python3 -m unittest discover tests -v
"""
import hashlib
import hmac
import json
import os
import time
import unittest

os.environ.setdefault("PADDLE_WEBHOOK_SECRET", "test_secret_for_pytest")
os.environ.setdefault("ANTHROPIC_API_KEY", "test-not-used")
os.environ.setdefault("BREVO_API_KEY", "test-not-used")
os.environ.setdefault("FROM_EMAIL", "test@example.com")
os.environ.setdefault("FROM_NAME", "Palja Test")

import app as app_module  # noqa: E402
import report_pipeline  # noqa: E402

WEBHOOK_SECRET = os.environ["PADDLE_WEBHOOK_SECRET"]
PAID_PRICE_ID = "pri_01m3f98f0s27hjx0xy4bc9em4d"
PREMIUM_PRICE_ID = "pri_01m3f9bjxx7sgpr1wvm5g8k61r"


def _sign(raw_body: bytes, secret: str = WEBHOOK_SECRET) -> str:
    ts = str(int(time.time()))
    signed_payload = f"{ts}:{raw_body.decode('utf-8')}"
    h1 = hmac.new(secret.encode("utf-8"), signed_payload.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"ts={ts};h1={h1}"


def _base_transaction_event(transaction_id, price_id, custom_data):
    return {
        "event_type": "transaction.completed",
        "data": {
            "id": transaction_id,
            "items": [{"price": {"id": price_id}}],
            "custom_data": custom_data,
        },
    }


class PaddleWebhookTests(unittest.TestCase):
    def setUp(self):
        app_module.app.config["TESTING"] = True
        app_module._PROCESSED_PADDLE_TRANSACTIONS.clear()
        self.client = app_module.app.test_client()
        self._patches = []

    def tearDown(self):
        for target, name, original in self._patches:
            setattr(target, name, original)
        self._patches = []

    def _patch(self, target, name, replacement):
        original = getattr(target, name)
        self._patches.append((target, name, original))
        setattr(target, name, replacement)

    def _post_webhook(self, event, secret=WEBHOOK_SECRET, with_signature=True):
        raw_body = json.dumps(event).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if with_signature:
            headers["Paddle-Signature"] = _sign(raw_body, secret)
        return self.client.post("/webhooks/paddle", data=raw_body, headers=headers)

    def _valid_paid_custom_data(self):
        return {
            "email": "kunde@example.com",
            "name": "Test Kunde",
            "birth_date": "1990-05-15",
            "birth_time": "14:30",
            "birth_city": "Berlin",
            "withdrawal_consent": True,
        }

    def test_missing_signature_rejected(self):
        event = _base_transaction_event("txn_no_sig", PAID_PRICE_ID, self._valid_paid_custom_data())
        resp = self._post_webhook(event, with_signature=False)
        self.assertEqual(resp.status_code, 401)

    def test_wrong_signature_secret_rejected(self):
        event = _base_transaction_event("txn_bad_sig", PAID_PRICE_ID, self._valid_paid_custom_data())
        resp = self._post_webhook(event, secret="wrong_secret")
        self.assertEqual(resp.status_code, 401)

    def test_non_transaction_completed_event_ignored_with_200(self):
        event = {"event_type": "subscription.created", "data": {}}
        resp = self._post_webhook(event)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json()["ignored"], "subscription.created")

    def test_missing_withdrawal_consent_rejected(self):
        calls = []
        self._patch(report_pipeline, "run_paid_signup", lambda **kw: calls.append(kw))

        custom_data = self._valid_paid_custom_data()
        del custom_data["withdrawal_consent"]
        event = _base_transaction_event("txn_no_consent", PAID_PRICE_ID, custom_data)
        resp = self._post_webhook(event)

        self.assertEqual(resp.status_code, 400)
        self.assertIn("withdrawal_consent", resp.get_json()["error"])
        self.assertEqual(len(calls), 0, "동의 없이는 리포트 파이프라인이 절대 호출되면 안 된다")

    def test_missing_email_rejected(self):
        custom_data = self._valid_paid_custom_data()
        del custom_data["email"]
        event = _base_transaction_event("txn_no_email", PAID_PRICE_ID, custom_data)
        resp = self._post_webhook(event)
        self.assertEqual(resp.status_code, 400)

    def test_unknown_price_id_rejected(self):
        event = _base_transaction_event("txn_unknown_price", "pri_unknown_does_not_exist", self._valid_paid_custom_data())
        resp = self._post_webhook(event)
        self.assertEqual(resp.status_code, 400)
        self.assertIn("price_id", resp.get_json()["error"])

    def test_premium_requires_gender(self):
        event = _base_transaction_event("txn_premium_no_gender", PREMIUM_PRICE_ID, self._valid_paid_custom_data())
        resp = self._post_webhook(event)
        self.assertEqual(resp.status_code, 400)
        self.assertIn("gender", resp.get_json()["error"])

    def test_valid_paid_transaction_triggers_pipeline_once(self):
        calls = []
        self._patch(report_pipeline, "run_paid_signup", lambda **kw: calls.append(kw))

        event = _base_transaction_event("txn_valid_paid", PAID_PRICE_ID, self._valid_paid_custom_data())
        resp = self._post_webhook(event)

        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.get_json()["ok"])
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]["payload"]["email"], "kunde@example.com")
        self.assertEqual(calls[0]["payload"]["tier"], "paid")

    def test_duplicate_transaction_id_does_not_resend_report(self):
        """과거 실제 버그: Paddle이 같은 결제를 재전송하면 리포트가 여러 번 발송됐음.
        트랜잭션 ID 기준 중복 방지 로직이 계속 지켜지는지 확인한다."""
        calls = []
        self._patch(report_pipeline, "run_paid_signup", lambda **kw: calls.append(kw))

        event = _base_transaction_event("txn_dup_test", PAID_PRICE_ID, self._valid_paid_custom_data())

        first = self._post_webhook(event)
        self.assertEqual(first.status_code, 200)
        self.assertEqual(len(calls), 1)

        # Paddle이 같은 트랜잭션을 재전송하는 상황 재현
        second = self._post_webhook(event)
        self.assertEqual(second.status_code, 200)
        self.assertTrue(second.get_json().get("duplicate"))
        self.assertEqual(len(calls), 1, "중복 전송 시 리포트 파이프라인이 다시 호출되면 안 된다")

    def test_failed_pipeline_unmarks_transaction_for_retry(self):
        """리포트 발송이 실패하면(예: 이메일 API 에러), 같은 트랜잭션 ID로 Paddle이
        재시도했을 때 '이미 처리됨'으로 잘못 무시하지 않고 다시 시도할 수 있어야 한다."""

        def _boom(**kw):
            raise report_pipeline.PipelineError("이메일 발송 실패 (테스트)", status=502)

        self._patch(report_pipeline, "run_paid_signup", _boom)

        event = _base_transaction_event("txn_retry_test", PAID_PRICE_ID, self._valid_paid_custom_data())
        first = self._post_webhook(event)
        self.assertEqual(first.status_code, 502)

        # 실패 후에는 트랜잭션이 "처리 완료" 목록에서 빠져 있어야 재시도가 가능하다
        self.assertNotIn("txn_retry_test", app_module._PROCESSED_PADDLE_TRANSACTIONS)

    def test_compatibility_requires_both_persons_birth_data(self):
        if "compatibility" not in app_module.PADDLE_PRICE_TIER_MAP.values():
            self.skipTest("COMPATIBILITY_PADDLE_PRICE_ID env var가 설정 안 된 환경(compatibility tier 비활성)")

        compat_price_id = next(
            pid for pid, tier in app_module.PADDLE_PRICE_TIER_MAP.items() if tier == "compatibility"
        )
        custom_data = {
            "email": "paar@example.com",
            "withdrawal_consent": True,
            "name_a": "Anna",
            "birth_date_a": "1990-01-01",
            "birth_city_a": "Berlin",
            # birth_date_b / birth_city_b 없음 -> 거부돼야 함
        }
        event = _base_transaction_event("txn_compat_incomplete", compat_price_id, custom_data)
        resp = self._post_webhook(event)
        self.assertEqual(resp.status_code, 400)
        self.assertIn("Kompatibilität", resp.get_json()["error"])

    def test_valid_compatibility_transaction_triggers_pipeline_once(self):
        if "compatibility" not in app_module.PADDLE_PRICE_TIER_MAP.values():
            self.skipTest("COMPATIBILITY_PADDLE_PRICE_ID env var가 설정 안 된 환경(compatibility tier 비활성)")

        compat_price_id = next(
            pid for pid, tier in app_module.PADDLE_PRICE_TIER_MAP.items() if tier == "compatibility"
        )
        calls = []
        self._patch(report_pipeline, "run_compatibility_signup", lambda **kw: calls.append(kw))

        custom_data = {
            "email": "paar@example.com",
            "withdrawal_consent": True,
            "name_a": "Anna",
            "birth_date_a": "1990-01-01",
            "birth_city_a": "Berlin",
            "name_b": "Ben",
            "birth_date_b": "1988-07-20",
            "birth_city_b": "Hamburg",
        }
        event = _base_transaction_event("txn_compat_valid", compat_price_id, custom_data)
        resp = self._post_webhook(event)

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(calls), 1)


if __name__ == "__main__":
    unittest.main()
