"""자동 검증(validate_report_consistency) + 자동 재생성(generate_verified_report) 테스트.

배경: GPT 피드백 라운드에서 여러 번 반복된 오류 패턴(오행/축 등장 횟수를 실제 데이터와
다르게 서술하는 것)은 프롬프트 지시만으로는 완전히 막지 못한다는 것을 실제
ANTHROPIC_API_KEY로 확인했다. 그래서 리포트 생성 직후 두 번째(저렴한) Claude 호출로
자동 검증하고, 문제가 발견되면 한 번 자동으로 재생성하는 단계를 파이프라인에 추가했다
(report_pipeline.generate_verified_report). 이 테스트는 실제 네트워크 호출 없이
requests.post를 mock으로 대체해서 그 로직만 검증한다.

실행: cd /home/claude/saju-api && python3 -m unittest discover tests -v
"""
import json
import os
import unittest
from unittest.mock import patch, MagicMock

os.environ.setdefault("ANTHROPIC_API_KEY", "test-key-for-verification-tests")

import report_pipeline as rp  # noqa: E402


def _fake_messages_response(text):
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = {"content": [{"type": "text", "text": text}]}
    resp.raise_for_status.return_value = None
    return resp


class ValidateReportConsistencyTests(unittest.TestCase):
    def test_no_api_key_skips_validation_gracefully(self):
        with patch.dict(os.environ, {}, clear=False):
            del os.environ["ANTHROPIC_API_KEY"]
            result = rp.validate_report_consistency("아무 텍스트", "아무 데이터")
        self.assertTrue(result["consistent"])
        self.assertEqual(result["issues"], [])
        self.assertIn("error", result)

    @patch("report_pipeline.requests.post")
    def test_parses_consistent_json_response(self, mock_post):
        mock_post.return_value = _fake_messages_response(
            json.dumps({"consistent": True, "issues": []})
        )
        result = rp.validate_report_consistency("리포트 텍스트", "원본 데이터")
        self.assertTrue(result["consistent"])
        self.assertEqual(result["issues"], [])

    @patch("report_pipeline.requests.post")
    def test_parses_inconsistent_json_response_with_code_fence(self, mock_post):
        # Claude가 ```json ... ``` 코드펜스로 감싸서 응답하는 경우도 처리해야 한다.
        payload = json.dumps(
            {
                "consistent": False,
                "issues": [{"claim": "화는 두 번만 등장", "problem": "실제로는 세 번 등장"}],
            }
        )
        mock_post.return_value = _fake_messages_response(f"```json\n{payload}\n```")
        result = rp.validate_report_consistency("리포트 텍스트", "원본 데이터")
        self.assertFalse(result["consistent"])
        self.assertEqual(len(result["issues"]), 1)
        self.assertIn("화는 두 번만 등장", result["issues"][0]["claim"])

    @patch("report_pipeline.requests.post", side_effect=Exception("network boom"))
    def test_network_failure_does_not_raise(self, mock_post):
        # 검증 인프라 자체가 실패해도 예외를 삼키고 발송을 막지 않아야 한다.
        result = rp.validate_report_consistency("리포트 텍스트", "원본 데이터")
        self.assertTrue(result["consistent"])
        self.assertIn("error", result)


class GenerateVerifiedReportTests(unittest.TestCase):
    def setUp(self):
        self._orig_call_claude = rp.call_claude
        self._orig_validate = rp.validate_report_consistency

    def tearDown(self):
        rp.call_claude = self._orig_call_claude
        rp.validate_report_consistency = self._orig_validate

    def test_returns_first_draft_when_already_consistent(self):
        rp.call_claude = lambda *a, **kw: "첫 초안"
        rp.validate_report_consistency = lambda *a, **kw: {"consistent": True, "issues": []}

        with patch("report_pipeline.requests.post") as mock_post:
            text, validation = rp.generate_verified_report(
                "paid_report_prompt.json",
                {"compact": "x", "monthly_compact": "y"},
                source_data="y",
            )
            # 일관성이 확인되면 재생성 API를 호출하지 않아야 한다.
            mock_post.assert_not_called()

        self.assertEqual(text, "첫 초안")
        self.assertTrue(validation["consistent"])

    def test_retries_once_and_uses_corrected_text_when_inconsistent(self):
        rp.call_claude = lambda *a, **kw: "틀린 초안 (화는 두 번만 등장)"

        validate_calls = []

        def fake_validate(report_text, source_data, **kw):
            validate_calls.append(report_text)
            if report_text == "틀린 초안 (화는 두 번만 등장)":
                return {
                    "consistent": False,
                    "issues": [{"claim": "화는 두 번만 등장", "problem": "실제로는 세 번 등장"}],
                }
            return {"consistent": True, "issues": []}

        rp.validate_report_consistency = fake_validate

        with patch("report_pipeline.requests.post") as mock_post:
            mock_post.return_value = _fake_messages_response("고쳐진 리포트 (화는 세 번 등장)")
            text, validation = rp.generate_verified_report(
                "paid_report_prompt.json",
                {"compact": "x", "monthly_compact": "y"},
                source_data="y",
            )
            mock_post.assert_called_once()

        self.assertEqual(text, "고쳐진 리포트 (화는 세 번 등장)")
        self.assertTrue(validation["consistent"])
        self.assertEqual(len(validate_calls), 2)


if __name__ == "__main__":
    unittest.main()
