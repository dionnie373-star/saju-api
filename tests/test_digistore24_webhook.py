"""Digistore24 웹훅(/webhooks/digistore24) 및 /orders/pending 회귀 테스트.

Paddle 웹훅 테스트(test_paddle_webhook.py)와 같은 방식 — 표준 라이브러리
unittest만 사용, report_pipeline의 run_*_signup을 monkeypatch해서 외부
서비스(Anthropic/Brevo) 호출 없이 "웹훅 라우팅/검증 로직"만 검증한다.

2026-10-03: custom 파라미터에 생년월일/이메일을 base64url로 직접 실어 보내던
방식은 개인정보가 URL에 평문으로 노출되는 문제(외부 코드 리뷰로 지적됨)가 있어,
/orders/pending에서 먼저 토큰을 발급받고 그 토큰만 custom에 싣는 방식으로
바뀌었다 - 아래 테스트도 그 흐름에 맞춰 토큰을 발급받아 사용한다.

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
import orders_store  # noqa: E402
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


def _valid_paid_order_data():
    return {
        "email": "kunde@example.com",
        "name": "Test Kunde",
        "birth_date": "1990-05-15",
        "birth_time": "14:30",
        "birth_city": "Berlin",
        "withdrawal_consent": True,
    }


def _base_form(order_id, product_id, email, custom_token, event="on_payment"):
    form = {
        "event": event,
        "order_id": order_id,
        "product_id": product_id,
        "email": email,
        "custom": custom_token,
    }
    form["sha_sign"] = _sign(form)
    return form


class Digistore24WebhookTests(unittest.TestCase):
    def setUp(self):
        app_module.app.config["TESTING"] = True
        orders_store.reset_for_tests()
        app_module._RATE_LIMIT_HISTORY.clear()
        self.client = app_module.app.test_client()
        self._patches = []

    def tearDown(self):
        # LIFO로 복원해야 한다 - 같은 (target, name)을 한 테스트 안에서 두 번
        # patch하는 경우(예: 재전송 시뮬레이션 테스트), 순서대로 복원하면 중간에
        # 저장된 "original"이 사실은 이전 patch의 대체 함수라서 최종 상태가
        # 진짜 원본이 아니라 마지막 대체 함수로 남는 버그가 있었다(실제로
        # test_failed_pipeline_unmarks_order_and_keeps_token_for_retry가
        # run_paid_signup을 두 번 patch하면서 이 버그를 드러냈고, 이후 다른
        # 테스트 파일까지 오염시켰다).
        for target, name, original in reversed(self._patches):
            setattr(target, name, original)
        self._patches = []
        orders_store.reset_for_tests()

    def _patch(self, target, name, replacement):
        original = getattr(target, name)
        self._patches.append((target, name, original))
        setattr(target, name, replacement)

    def _post_webhook(self, form):
        return self.client.post("/webhooks/digistore24", data=form)

    def _create_pending_order(self, data):
        """실제 /orders/pending 엔드포인트를 통해 토큰을 발급받는다 (정상 체크아웃 흐름)."""
        resp = self.client.post("/orders/pending", json=data)
        self.assertEqual(resp.status_code, 200, resp.get_json())
        return resp.get_json()["token"]

    def _stash_pending_order(self, token, data):
        """엔드포인트의 자체 검증(withdrawal_consent 등)을 우회해서 직접 pending
        store에 꽂아넣는다 — 체크아웃을 건너뛴 위조 요청을 흉내내서, 웹훅 쪽
        방어선(서버 재확인)을 테스트하기 위함."""
        orders_store.store_pending_order(token, data)

    def test_missing_signature_rejected(self):
        token = self._create_pending_order(_valid_paid_order_data())
        form = _base_form("ds24_no_sig", PAID_PRODUCT_ID, "kunde@example.com", token)
        form["sha_sign"] = ""
        resp = self._post_webhook(form)
        self.assertEqual(resp.status_code, 401)

    def test_wrong_passphrase_rejected(self):
        token = self._create_pending_order(_valid_paid_order_data())
        form = _base_form("ds24_bad_sig", PAID_PRODUCT_ID, "kunde@example.com", token)
        form["sha_sign"] = _sign(form, passphrase="wrong_passphrase")
        resp = self._post_webhook(form)
        self.assertEqual(resp.status_code, 401)

    def test_non_payment_event_ignored_with_200(self):
        token = self._create_pending_order(_valid_paid_order_data())
        form = _base_form("ds24_refund", PAID_PRODUCT_ID, "kunde@example.com", token, event="on_refund")
        resp = self._post_webhook(form)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_data(as_text=True), "OK")

    def test_missing_withdrawal_consent_rejected(self):
        calls = []
        self._patch(report_pipeline, "run_paid_signup", lambda **kw: calls.append(kw))

        # 체크아웃을 우회해서 동의 없이 custom 데이터를 만든 경우를 흉내낸다
        # (/orders/pending 자체는 동의 없이는 토큰을 내주지 않으므로, 웹훅이
        # 독립적으로 재확인하는지가 여기서 검증 대상).
        token = "forged_token_no_consent"
        self._stash_pending_order(token, {
            "name": "Test Kunde",
            "birth_date": "1990-05-15",
            "birth_time": "14:30",
            "birth_city": "Berlin",
        })
        form = _base_form("ds24_no_consent", PAID_PRODUCT_ID, "kunde@example.com", token)
        resp = self._post_webhook(form)

        self.assertEqual(resp.status_code, 400)
        self.assertIn("withdrawal_consent", resp.get_data(as_text=True))
        self.assertEqual(len(calls), 0, "동의 없이는 리포트 파이프라인이 절대 호출되면 안 된다")

    def test_missing_email_rejected(self):
        # /orders/pending 자체는 email을 필수로 요구하므로(정상 체크아웃이라면
        # 항상 있음), "저장된 custom_data에도 email이 아예 없는" 상황은 체크아웃을
        # 우회한 위조 요청으로만 재현 가능하다 - 웹훅이 독립적으로 거부하는지 확인.
        token = "forged_token_no_email"
        self._stash_pending_order(token, {
            "name": "Test Kunde",
            "birth_date": "1990-05-15",
            "birth_time": "14:30",
            "birth_city": "Berlin",
            "withdrawal_consent": True,
        })
        form = _base_form("ds24_no_email", PAID_PRODUCT_ID, "", token)
        resp = self._post_webhook(form)
        self.assertEqual(resp.status_code, 400)

    def test_unknown_product_id_rejected(self):
        token = self._create_pending_order(_valid_paid_order_data())
        form = _base_form("ds24_unknown_product", "999999999", "kunde@example.com", token)
        resp = self._post_webhook(form)
        self.assertEqual(resp.status_code, 400)
        self.assertIn("product_id", resp.get_data(as_text=True))

    def test_unknown_or_expired_token_rejected(self):
        """custom이 /orders/pending에서 발급된 적 없는(또는 이미 소비/만료된) 토큰이면
        거부해야 한다 — 예전의 "malformed JSON" 케이스를 토큰 체계로 대체."""
        form = _base_form("ds24_bad_token", PAID_PRODUCT_ID, "kunde@example.com", "totally_made_up_token")
        resp = self._post_webhook(form)
        self.assertEqual(resp.status_code, 400)
        self.assertIn("토큰", resp.get_data(as_text=True))

    def test_valid_paid_order_triggers_pipeline_once(self):
        calls = []
        self._patch(report_pipeline, "run_paid_signup", lambda **kw: calls.append(kw))

        token = self._create_pending_order(_valid_paid_order_data())
        form = _base_form("ds24_valid_paid", PAID_PRODUCT_ID, "kunde@example.com", token)
        resp = self._post_webhook(form)

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_data(as_text=True), "OK")
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]["payload"]["email"], "kunde@example.com")
        self.assertEqual(calls[0]["payload"]["tier"], "paid")

    def test_token_is_consumed_after_successful_processing(self):
        """성공적으로 처리된 토큰은 pending store에서 제거돼야 한다(재사용 방지)."""
        self._patch(report_pipeline, "run_paid_signup", lambda **kw: None)

        token = self._create_pending_order(_valid_paid_order_data())
        self.assertTrue(orders_store.pending_token_exists(token))

        form = _base_form("ds24_consume_test", PAID_PRODUCT_ID, "kunde@example.com", token)
        resp = self._post_webhook(form)

        self.assertEqual(resp.status_code, 200)
        self.assertFalse(orders_store.pending_token_exists(token))

    def test_duplicate_order_id_does_not_resend_report(self):
        """Digistore24도 Paddle처럼 응답이 늦으면 같은 IPN을 재전송할 수 있다 —
        order_id 기준 중복 방지가 지켜지는지 확인."""
        calls = []
        self._patch(report_pipeline, "run_paid_signup", lambda **kw: calls.append(kw))

        token = self._create_pending_order(_valid_paid_order_data())
        form = _base_form("ds24_dup_test", PAID_PRODUCT_ID, "kunde@example.com", token)

        first = self._post_webhook(form)
        self.assertEqual(first.status_code, 200)
        self.assertEqual(len(calls), 1)

        second = self._post_webhook(form)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(second.get_data(as_text=True), "OK")
        self.assertEqual(len(calls), 1, "중복 전송 시 리포트 파이프라인이 다시 호출되면 안 된다")

    def test_failed_pipeline_unmarks_order_and_keeps_token_for_retry(self):
        def _boom(**kw):
            raise report_pipeline.PipelineError("이메일 발송 실패 (테스트)", status=502)

        self._patch(report_pipeline, "run_paid_signup", _boom)

        token = self._create_pending_order(_valid_paid_order_data())
        form = _base_form("ds24_retry_test", PAID_PRODUCT_ID, "kunde@example.com", token)
        first = self._post_webhook(form)
        self.assertEqual(first.status_code, 502)

        self.assertFalse(orders_store.is_marked_processed("digistore24", "ds24_retry_test"))
        # 실패했으니 토큰은 지워지면 안 된다 - Digistore24가 IPN을 재전송하면
        # 같은 토큰으로 다시 조회할 수 있어야 한다.
        self.assertTrue(orders_store.pending_token_exists(token))

        # 재전송 시뮬레이션: 이번엔 성공하도록 바꾸고 같은 토큰으로 다시 호출.
        calls = []
        self._patch(report_pipeline, "run_paid_signup", lambda **kw: calls.append(kw))
        second = self._post_webhook(form)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(len(calls), 1)

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

        token = self._create_pending_order(_valid_paid_order_data())
        form = _base_form("ds24_worker_timeout", PAID_PRODUCT_ID, "kunde@example.com", token)
        with self.assertRaises(SystemExit):
            self._post_webhook(form)

        self.assertFalse(
            orders_store.is_marked_processed("digistore24", "ds24_worker_timeout"),
            "SystemExit(워커 타임아웃)이 나도 주문은 반드시 재시도 가능하게 unmark돼야 한다",
        )

    def test_premium_requires_gender(self):
        if "premium" not in app_module.DIGISTORE24_PRODUCT_TIER_MAP.values():
            self.skipTest("DIGISTORE24_PRODUCT_ID_PREMIUM env var가 설정 안 된 환경(premium tier 비활성)")

        premium_product_id = next(
            pid for pid, tier in app_module.DIGISTORE24_PRODUCT_TIER_MAP.items() if tier == "premium"
        )
        token = self._create_pending_order(_valid_paid_order_data())  # gender 없음
        form = _base_form("ds24_premium_no_gender", premium_product_id, "kunde@example.com", token)
        resp = self._post_webhook(form)
        self.assertEqual(resp.status_code, 400)
        self.assertIn("gender", resp.get_data(as_text=True))


class PendingOrderEndpointTests(unittest.TestCase):
    """/orders/pending 자체의 입력 검증 + 레이트리밋 테스트."""

    def setUp(self):
        app_module.app.config["TESTING"] = True
        orders_store.reset_for_tests()
        app_module._RATE_LIMIT_HISTORY.clear()
        self.client = app_module.app.test_client()

    def tearDown(self):
        orders_store.reset_for_tests()
        app_module._RATE_LIMIT_HISTORY.clear()

    def test_valid_order_returns_token_and_stores_no_pii_response(self):
        resp = self.client.post("/orders/pending", json=_valid_paid_order_data())
        self.assertEqual(resp.status_code, 200)
        body = resp.get_json()
        self.assertTrue(body["ok"])
        self.assertIsInstance(body["token"], str)
        self.assertGreater(len(body["token"]), 16)
        # 응답 자체에 생년월일 등 원본 개인정보를 되돌려주지 않는다(토큰만).
        self.assertNotIn("birth_date", body)

    def test_missing_email_rejected(self):
        data = _valid_paid_order_data()
        del data["email"]
        resp = self.client.post("/orders/pending", json=data)
        self.assertEqual(resp.status_code, 400)

    def test_missing_withdrawal_consent_rejected(self):
        data = _valid_paid_order_data()
        data["withdrawal_consent"] = False
        resp = self.client.post("/orders/pending", json=data)
        self.assertEqual(resp.status_code, 400)

    def test_tokens_are_unique_across_calls(self):
        t1 = self.client.post("/orders/pending", json=_valid_paid_order_data()).get_json()["token"]
        t2 = self.client.post("/orders/pending", json=_valid_paid_order_data()).get_json()["token"]
        self.assertNotEqual(t1, t2)

    def test_rate_limit_blocks_excessive_requests_from_same_ip(self):
        for i in range(20):
            resp = self.client.post(
                "/orders/pending", json=_valid_paid_order_data(),
                headers={"X-Forwarded-For": "5.5.5.5"},
            )
            self.assertEqual(resp.status_code, 200, f"request {i} should pass")

        blocked = self.client.post(
            "/orders/pending", json=_valid_paid_order_data(),
            headers={"X-Forwarded-For": "5.5.5.5"},
        )
        self.assertEqual(blocked.status_code, 429)


if __name__ == "__main__":
    unittest.main()
