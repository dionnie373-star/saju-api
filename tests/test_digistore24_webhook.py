"""Digistore24 웹훅(/webhooks/digistore24) 회귀 테스트.

Paddle 웹훅 테스트(test_paddle_webhook.py)와 같은 방식 — 표준 라이브러리
unittest만 사용, report_pipeline의 run_*_signup을 monkeypatch해서 외부
서비스(Anthropic/Brevo) 호출 없이 "웹훅 라우팅/검증 로직"만 검증한다.

실행: cd /home/claude/saju-api && python3 -m unittest discover tests -v
"""
import hashlib
import os
import unittest

os.environ.setdefault("PADDLE_WEBHOOK_SECRET", "test_secret_for_pytest")
os.environ.setdefault("DIGISTORE24_SHA_PASSPHRASE", "test_ds24_passphrase")
os.environ.setdefault("ANTHROPIC_API_KEY", "test-not-used")
os.environ.setdefault("BREVO_API_KEY", "test-not-used")
os.environ.setdefault("FROM_EMAIL", "test@example.com")
os.environ.setdefault("FROM_NAME", "Palja Test")

import app as app_module  # noqa: E402
import report_pipeline  # noqa: E402

PASSPHRASE = os.environ["DIGISTORE24_SHA_PASSPHRASE"]
PAID_PRODUCT_ID = "740708"


def _sign(form: dict, passphrase: str = PASSPHRASE) -> str:
    """Digistore24 공식 레퍼런스 구현(digistore24.com/download/ipn/examples/ipn/sha_sign.php의
    digistore_signature() 함수)을 독립적으로 재구현한 것 — app._verify_digistore24_signature와
    같은 로직이어야 서명이 맞는다. (처음엔 digistore_ipn.pdf 기반 알고리즘을 썼었는데 실제 IPN
    호출과 서명이 안 맞아서, 실제 캡처한 test IPN 페이로드로 역산해 이 알고리즘으로 교체함:
    sha_sign/빈 값 제외 → 키 대소문자 구분 정렬 → "key=value+passphrase"를 구분자 없이 연결.)
    """
    items = [
        (k, v)
        for k, v in form.items()
        if k.lower() not in ("sha_sign", "shasign") and v not in (None, "", False)
    ]
    items.sort(key=lambda kv: kv[0])
    sha_string = "".join(f"{k}={v}{passphrase}" for k, v in items)
    return hashlib.sha512(sha_string.encode("utf-8")).hexdigest()


def _base64url_encode_json(data: dict) -> str:
    """static_site/index.html의 base64UrlEncodeJson()과 독립적으로 동일한 로직을
    재구현(app._decode_digistore24_custom과 짝 맞는 인코더) — Digistore24가 "custom"
    파라미터 값의 큰따옴표(")를 전부 제거해버리는 걸 실제 테스트 구매로 확인해서,
    큰따옴표가 전혀 없는 base64url로 바꿔 보내기로 함(패딩 "=" 제거).
    """
    import base64
    import json

    raw = base64.urlsafe_b64encode(json.dumps(data).encode("utf-8")).decode("ascii")
    return raw.rstrip("=")


def _valid_paid_custom_data_json():
    return _base64url_encode_json({
        "name": "Test Kunde",
        "birth_date": "1990-05-15",
        "birth_time": "14:30",
        "birth_city": "Berlin",
        "withdrawal_consent": True,
    })


def _base_form(order_id, product_id, email, custom_json, event="on_payment"):
    form = {
        "event": event,
        "order_id": order_id,
        "product_id": product_id,
        "email": email,
        "custom": custom_json,
    }
    form["sha_sign"] = _sign(form)
    return form


class Digistore24WebhookTests(unittest.TestCase):
    def setUp(self):
        app_module.app.config["TESTING"] = True
        app_module._PROCESSED_DIGISTORE24_ORDERS.clear()
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

    def _post_webhook(self, form):
        return self.client.post("/webhooks/digistore24", data=form)

    def test_missing_signature_rejected(self):
        form = _base_form("ds24_no_sig", PAID_PRODUCT_ID, "kunde@example.com", _valid_paid_custom_data_json())
        form["sha_sign"] = ""
        resp = self._post_webhook(form)
        self.assertEqual(resp.status_code, 401)

    def test_wrong_passphrase_rejected(self):
        form = _base_form("ds24_bad_sig", PAID_PRODUCT_ID, "kunde@example.com", _valid_paid_custom_data_json())
        form["sha_sign"] = _sign(form, passphrase="wrong_passphrase")
        resp = self._post_webhook(form)
        self.assertEqual(resp.status_code, 401)

    def test_non_payment_event_ignored_with_200(self):
        form = _base_form(
            "ds24_refund", PAID_PRODUCT_ID, "kunde@example.com", _valid_paid_custom_data_json(), event="on_refund"
        )
        resp = self._post_webhook(form)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json()["ignored"], "on_refund")

    def test_missing_withdrawal_consent_rejected(self):
        calls = []
        self._patch(report_pipeline, "run_paid_signup", lambda **kw: calls.append(kw))

        custom = {
            "name": "Test Kunde",
            "birth_date": "1990-05-15",
            "birth_time": "14:30",
            "birth_city": "Berlin",
        }
        form = _base_form("ds24_no_consent", PAID_PRODUCT_ID, "kunde@example.com", _base64url_encode_json(custom))
        resp = self._post_webhook(form)

        self.assertEqual(resp.status_code, 400)
        self.assertIn("withdrawal_consent", resp.get_json()["error"])
        self.assertEqual(len(calls), 0, "동의 없이는 리포트 파이프라인이 절대 호출되면 안 된다")

    def test_missing_email_rejected(self):
        form = _base_form("ds24_no_email", PAID_PRODUCT_ID, "", _valid_paid_custom_data_json())
        resp = self._post_webhook(form)
        self.assertEqual(resp.status_code, 400)

    def test_unknown_product_id_rejected(self):
        form = _base_form("ds24_unknown_product", "999999999", "kunde@example.com", _valid_paid_custom_data_json())
        resp = self._post_webhook(form)
        self.assertEqual(resp.status_code, 400)
        self.assertIn("product_id", resp.get_json()["error"])

    def test_malformed_custom_json_rejected(self):
        form = _base_form("ds24_bad_json", PAID_PRODUCT_ID, "kunde@example.com", "{not valid json")
        resp = self._post_webhook(form)
        self.assertEqual(resp.status_code, 400)

    def test_valid_paid_order_triggers_pipeline_once(self):
        calls = []
        self._patch(report_pipeline, "run_paid_signup", lambda **kw: calls.append(kw))

        form = _base_form("ds24_valid_paid", PAID_PRODUCT_ID, "kunde@example.com", _valid_paid_custom_data_json())
        resp = self._post_webhook(form)

        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.get_json()["ok"])
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]["payload"]["email"], "kunde@example.com")
        self.assertEqual(calls[0]["payload"]["tier"], "paid")

    def test_duplicate_order_id_does_not_resend_report(self):
        """Digistore24도 Paddle처럼 응답이 늦으면 같은 IPN을 재전송할 수 있다 —
        order_id 기준 중복 방지가 지켜지는지 확인."""
        calls = []
        self._patch(report_pipeline, "run_paid_signup", lambda **kw: calls.append(kw))

        form = _base_form("ds24_dup_test", PAID_PRODUCT_ID, "kunde@example.com", _valid_paid_custom_data_json())

        first = self._post_webhook(form)
        self.assertEqual(first.status_code, 200)
        self.assertEqual(len(calls), 1)

        second = self._post_webhook(form)
        self.assertEqual(second.status_code, 200)
        self.assertTrue(second.get_json().get("duplicate"))
        self.assertEqual(len(calls), 1, "중복 전송 시 리포트 파이프라인이 다시 호출되면 안 된다")

    def test_failed_pipeline_unmarks_order_for_retry(self):
        def _boom(**kw):
            raise report_pipeline.PipelineError("이메일 발송 실패 (테스트)", status=502)

        self._patch(report_pipeline, "run_paid_signup", _boom)

        form = _base_form("ds24_retry_test", PAID_PRODUCT_ID, "kunde@example.com", _valid_paid_custom_data_json())
        first = self._post_webhook(form)
        self.assertEqual(first.status_code, 502)

        self.assertNotIn("ds24_retry_test", app_module._PROCESSED_DIGISTORE24_ORDERS)

    def test_worker_timeout_systemexit_still_unmarks_order_for_retry(self):
        """실제 테스트 구매로 발견된 버그 재현: gunicorn 워커가 --timeout을 넘기면
        SIGALRM 핸들러가 sys.exit(1)로 SystemExit을 던진다. SystemExit은
        BaseException만 상속하고 Exception은 상속하지 않으므로, 예전처럼
        "except Exception: _unmark_order(); raise" 구조였다면 이 경우
        _unmark_order()가 호출되지 않아 order_id가 영원히 "처리 완료"로 남고
        Digistore24의 재전송 IPN도 전부 무시돼 고객이 리포트를 영영 못 받는
        치명적인 버그가 생긴다. finally 기반 구조로 고쳤으니 SystemExit이 나도
        반드시 unmark돼야 한다."""

        def _timeout(**kw):
            raise SystemExit(1)

        self._patch(report_pipeline, "run_paid_signup", _timeout)

        form = _base_form("ds24_worker_timeout", PAID_PRODUCT_ID, "kunde@example.com", _valid_paid_custom_data_json())
        with self.assertRaises(SystemExit):
            self._post_webhook(form)

        self.assertNotIn(
            "ds24_worker_timeout",
            app_module._PROCESSED_DIGISTORE24_ORDERS,
            "SystemExit(워커 타임아웃)이 나도 주문은 반드시 재시도 가능하게 unmark돼야 한다",
        )

    def test_premium_requires_gender(self):
        if "premium" not in app_module.DIGISTORE24_PRODUCT_TIER_MAP.values():
            self.skipTest("DIGISTORE24_PRODUCT_ID_PREMIUM env var가 설정 안 된 환경(premium tier 비활성)")

        premium_product_id = next(
            pid for pid, tier in app_module.DIGISTORE24_PRODUCT_TIER_MAP.items() if tier == "premium"
        )
        form = _base_form(
            "ds24_premium_no_gender", premium_product_id, "kunde@example.com", _valid_paid_custom_data_json()
        )
        resp = self._post_webhook(form)
        self.assertEqual(resp.status_code, 400)
        self.assertIn("gender", resp.get_json()["error"])


if __name__ == "__main__":
    unittest.main()
