"""/signup 엔드포인트의 레이트리밋 회귀 테스트.

배경: /signup은 인증도 결제도 없는 완전 공개 엔드포인트라서, 방어가 없으면
스크립트로 반복 호출해 (1) Anthropic API 비용을 계속 발생시키거나 (2) 제3자
이메일 주소로 원치 않는 메일을 계속 보내는 스팸 도구로 악용될 수 있다.
`app._rate_limited()`로 같은 이메일은 10분에 1번, 같은 IP는 1시간에 5번까지만
허용하도록 막았다.

이 테스트는 실제 계산/Anthropic/Brevo 호출 없이 run_calculation과
report_pipeline.run_free_signup을 monkeypatch해서 라우트 자체의 레이트리밋
로직만 검증한다. 매 테스트 전에 _RATE_LIMIT_HISTORY를 초기화해서 테스트끼리
서로 간섭하지 않게 한다.

실행: cd /home/claude/saju-api && python3 -m unittest discover tests -v
"""
import os
import unittest

os.environ.setdefault("ANTHROPIC_API_KEY", "test-not-used")
os.environ.setdefault("BREVO_API_KEY", "test-not-used")
os.environ.setdefault("FROM_EMAIL", "test@example.com")
os.environ.setdefault("FROM_NAME", "Palja Test")

import app as app_module  # noqa: E402
import report_pipeline as rp  # noqa: E402


class SignupRateLimitTests(unittest.TestCase):
    def setUp(self):
        app_module._RATE_LIMIT_HISTORY.clear()
        self.client = app_module.app.test_client()

        self._orig_run_calculation = app_module.run_calculation
        self._orig_run_free_signup = rp.run_free_signup
        app_module.run_calculation = lambda payload: {"compact": "테스트 사주 데이터"}
        rp.run_free_signup = lambda *, payload, calc_result: {"ok": True}

    def tearDown(self):
        app_module.run_calculation = self._orig_run_calculation
        rp.run_free_signup = self._orig_run_free_signup
        app_module._RATE_LIMIT_HISTORY.clear()

    def _signup(self, email, ip="1.2.3.4"):
        return self.client.post(
            "/signup",
            json={"email": email, "birth_date": "1990-01-01"},
            headers={"X-Forwarded-For": ip},
        )

    def test_first_signup_for_an_email_succeeds(self):
        resp = self._signup("anna@example.com")
        self.assertEqual(resp.status_code, 200)

    def test_second_signup_for_same_email_within_window_is_rate_limited(self):
        first = self._signup("anna@example.com")
        second = self._signup("anna@example.com")
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 429)

    def test_email_rate_limit_is_case_insensitive(self):
        first = self._signup("Anna@Example.com")
        second = self._signup("anna@example.com")
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 429)

    def test_different_emails_from_same_ip_are_each_allowed_until_ip_limit(self):
        for i in range(5):
            resp = self._signup(f"user{i}@example.com", ip="9.9.9.9")
            self.assertEqual(resp.status_code, 200, f"request {i} should pass")

        # 같은 IP로 6번째 요청(다른 이메일이라도) -> IP 레이트리밋에 걸림
        sixth = self._signup("user6@example.com", ip="9.9.9.9")
        self.assertEqual(sixth.status_code, 429)

    def test_same_email_from_different_ip_still_blocked_by_email_limit(self):
        first = self._signup("bob@example.com", ip="1.1.1.1")
        second = self._signup("bob@example.com", ip="2.2.2.2")
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 429)


if __name__ == "__main__":
    unittest.main()
