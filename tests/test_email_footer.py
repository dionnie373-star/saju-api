"""모든 리포트 이메일에 사업자 신원(Impressum 등) 푸터가 포함되는지 확인하는
회귀 테스트.

배경: 독일 소비자에게 보내는 상거래성 이메일은 본문에서 바로 발신자가 누구인지
알 수 있어야 신뢰를 얻기 쉽다. 이메일 본문에만 있고 홈페이지에만 링크가 있으면
사용자가 이메일만 보고는 사업자를 확인할 방법이 없었음 — 그래서 모든 리포트
이메일 템플릿 하단에 Impressum/Datenschutz/Widerruf 링크와 문의 이메일 주소를
넣는 공용 푸터(_EMAIL_FOOTER_HTML)를 추가했다.

이 테스트는 Anthropic/Brevo를 전혀 호출하지 않는다 — call_claude와 send_email을
monkeypatch로 가짜 함수로 바꿔서 실제로 발송되는 html_body만 검증한다.

실행: cd /home/claude/saju-api && python3 -m unittest discover tests -v
"""
import os
import unittest

os.environ.setdefault("ANTHROPIC_API_KEY", "test-not-used")
os.environ.setdefault("BREVO_API_KEY", "test-not-used")
os.environ.setdefault("FROM_EMAIL", "test@example.com")
os.environ.setdefault("FROM_NAME", "Palja Test")

import report_pipeline as rp  # noqa: E402


class EmailFooterTests(unittest.TestCase):
    def setUp(self):
        self._orig_call_claude = rp.call_claude
        self._orig_send_email = rp.send_email
        self.captured_html_body = None
        rp.call_claude = lambda *a, **kw: "Test-Reportinhalt."
        rp.send_email = self._fake_send_email

    def tearDown(self):
        rp.call_claude = self._orig_call_claude
        rp.send_email = self._orig_send_email

    def _fake_send_email(self, *, to_email, subject, html_body, attachment_path=None, attachment_name=None):
        self.captured_html_body = html_body

    def _assert_footer_present(self):
        self.assertIn("Impressum", self.captured_html_body)
        self.assertIn("Datenschutz", self.captured_html_body)
        self.assertIn("Widerruf", self.captured_html_body)
        self.assertIn("dionnie373@gmail.com", self.captured_html_body)

    def test_free_report_email_contains_footer(self):
        rp.run_free_signup(
            payload={"email": "test@example.com", "name": "Anna"},
            calc_result={"compact": "테스트 사주 데이터"},
        )
        self._assert_footer_present()

    def test_paid_report_email_contains_footer(self):
        rp.run_paid_signup(
            payload={"email": "test@example.com", "name": "Anna"},
            calc_result={"compact": "테스트 사주 데이터", "monthly_compact": "테스트 월별 데이터"},
        )
        self._assert_footer_present()

    def test_compatibility_email_contains_footer(self):
        rp.run_compatibility_signup(
            payload={"email": "test@example.com", "name_a": "Anna", "name_b": "Ben"},
            calc_result_a={"compact": "Person A 사주 데이터"},
            calc_result_b={"compact": "Person B 사주 데이터"},
        )
        self._assert_footer_present()


if __name__ == "__main__":
    unittest.main()
