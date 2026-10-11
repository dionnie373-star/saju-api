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

    def test_schicksal_surviving_all_retries_is_scrubbed_from_final_text(self):
        # 실제로 발견된 사례(2026-09-27): 자동 재생성 2회를 다 써도 모델이
        # "Dies ist kein Schicksal, das über dich verhängt wird." 같은 부정문으로
        # 금지 단어를 계속 재도입했다. 이 테스트는 그 상황을 그대로 재현해서,
        # 최종 리포트에는 "Schicksal"이 남아있으면 안 된다는 걸 보장한다.
        draft_with_schicksal = (
            "Der Sommer bringt neue Energie. Dies ist kein Schicksal, das über "
            "dich verhängt wird, sondern ein Muster, das du erkennen kannst."
        )
        rp.call_claude = lambda *a, **kw: draft_with_schicksal
        # 재시도해도 똑같이 "Schicksal"이 다시 나오는 최악의 경우를 시뮬레이션.
        rp.validate_report_consistency = lambda *a, **kw: {"consistent": True, "issues": []}

        with patch("report_pipeline.requests.post") as mock_post:
            mock_post.return_value = _fake_messages_response(draft_with_schicksal)
            text, validation = rp.generate_verified_report(
                "paid_report_prompt.json",
                {"compact": "x", "monthly_compact": "y"},
                source_data="y",
                min_words=0,
                max_retries=2,
            )

        # 재시도(mechanical 검사가 매번 "Schicksal" 감지 -> 재생성 호출)는
        # max_retries(2)번 소진됐어야 한다.
        self.assertEqual(mock_post.call_count, 2)
        # 그래도 남아있던 "Schicksal"은 최종 방어선에서 제거되어야 한다.
        self.assertNotIn("Schicksal", text)
        self.assertNotIn("schicksal", text.lower())
        # 나머지 문장(관련 없는 내용)은 그대로 남아있어야 한다.
        self.assertIn("Der Sommer bringt neue Energie.", text)
        # 스크럽 이후에는 (다른 문제가 없었으므로) consistent==True가 되어야 한다.
        self.assertTrue(validation["consistent"])
        self.assertFalse(
            any("Schicksal" in issue.get("problem", "") for issue in validation["issues"])
        )


class StripSchicksalSentencesTests(unittest.TestCase):
    """_strip_schicksal_sentences 단위 테스트 - 문장 단위 제거 로직 자체를 확인."""

    def test_removes_negated_schicksal_sentence_but_keeps_rest_of_paragraph(self):
        text = (
            "Der Sommer bringt neue Energie. Dies ist kein Schicksal, das über "
            "dich verhängt wird. Du kannst diese Energie aktiv nutzen."
        )
        result = rp._strip_schicksal_sentences(text)
        self.assertNotIn("Schicksal", result)
        self.assertIn("Der Sommer bringt neue Energie.", result)
        self.assertIn("Du kannst diese Energie aktiv nutzen.", result)

    def test_catches_inflected_and_lowercase_forms(self):
        for word in ("Schicksal", "Schicksals", "Schicksale", "schicksalhaft", "SCHICKSAL"):
            text = f"Ein Satz. Etwas {word} hier. Ein weiterer Satz."
            result = rp._strip_schicksal_sentences(text)
            self.assertNotIn("Schicksal", result, msg=f"failed for {word}")
            self.assertNotIn("schicksal", result.lower(), msg=f"failed for {word}")

    def test_heading_line_that_becomes_empty_is_dropped_not_left_blank(self):
        text = "## Schicksal und Wandel\n\nText danach."
        result = rp._strip_schicksal_sentences(text)
        self.assertNotIn("Schicksal", result)
        self.assertNotIn("##", result)
        self.assertIn("Text danach.", result)

    def test_text_without_schicksal_is_returned_unchanged(self):
        text = "Ein ganz normaler Satz ohne das verbotene Wort."
        self.assertEqual(rp._strip_schicksal_sentences(text), text)


if __name__ == "__main__":
    unittest.main()


class AnthropicRetryTests(unittest.TestCase):
    def setUp(self):
        self._base = rp.ANTHROPIC_RETRY_BASE_SECONDS
        rp.ANTHROPIC_RETRY_BASE_SECONDS = 0

    def tearDown(self):
        rp.ANTHROPIC_RETRY_BASE_SECONDS = self._base

    def _resp(self, status):
        r = MagicMock()
        r.status_code = status
        r.headers = {}
        return r

    def test_retries_overloaded_then_succeeds(self):
        with patch("report_pipeline.requests.post", side_effect=[self._resp(529), self._resp(429), self._resp(200)]) as m:
            r = rp._post_anthropic({}, {}, 5)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(m.call_count, 3)

    def test_does_not_retry_client_errors(self):
        with patch("report_pipeline.requests.post", side_effect=[self._resp(400)]) as m:
            r = rp._post_anthropic({}, {}, 5)
        self.assertEqual(r.status_code, 400)
        self.assertEqual(m.call_count, 1)

    def test_gives_up_after_max_attempts(self):
        with patch("report_pipeline.requests.post", return_value=self._resp(529)) as m:
            r = rp._post_anthropic({}, {}, 5)
        self.assertEqual(r.status_code, 529)
        self.assertEqual(m.call_count, rp.ANTHROPIC_HTTP_ATTEMPTS)
