"""Anthropic 스트리밍(SSE) 수신 테스트 — 긴 프리미엄 리포트가 280초 읽기 타임아웃에 걸리지 않게 하는 경로."""
import json
import unittest
from unittest.mock import patch

import requests

import report_pipeline as rp


def sse(*events):
    lines = []
    for et, data in events:
        lines.append(f"event: {et}")
        lines.append("data: " + json.dumps(data, ensure_ascii=False))
        lines.append("")
    return lines


class FakeStreamResp(requests.Response):
    def __init__(self, lines, status=200, text=""):
        super().__init__()
        self.status_code = status
        self._lines = lines
        self._content = text.encode()
        self.headers = {}

    def iter_lines(self, decode_unicode=False, **kw):
        yield from self._lines

    @property
    def text(self):
        return self._content.decode()


GOOD = sse(
    ("message_start", {"type": "message_start", "message": {"id": "m1", "model": "claude-sonnet-5-5", "role": "assistant", "content": [], "usage": {"input_tokens": 10, "output_tokens": 1}}}),
    ("content_block_start", {"type": "content_block_start", "index": 0, "content_block": {"type": "thinking", "thinking": ""}}),
    ("ping", {"type": "ping"}),
    ("content_block_delta", {"type": "content_block_delta", "index": 0, "delta": {"type": "thinking_delta", "thinking": "denke..."}}),
    ("content_block_delta", {"type": "content_block_delta", "index": 0, "delta": {"type": "signature_delta", "signature": "sig"}}),
    ("content_block_stop", {"type": "content_block_stop", "index": 0}),
    ("content_block_start", {"type": "content_block_start", "index": 1, "content_block": {"type": "text", "text": ""}}),
    ("content_block_delta", {"type": "content_block_delta", "index": 1, "delta": {"type": "text_delta", "text": "Hallo, "}}),
    ("content_block_delta", {"type": "content_block_delta", "index": 1, "delta": {"type": "text_delta", "text": "Welt – 한글 ü"}}),
    ("content_block_stop", {"type": "content_block_stop", "index": 1}),
    ("message_delta", {"type": "message_delta", "delta": {"stop_reason": "end_turn"}, "usage": {"output_tokens": 42}}),
    ("message_stop", {"type": "message_stop"}),
)


class ConsumeSSE(unittest.TestCase):
    def test_assembles_thinking_and_text(self):
        m = rp._consume_sse(FakeStreamResp(GOOD))
        self.assertEqual([b["type"] for b in m["content"]], ["thinking", "text"])
        self.assertEqual(m["content"][1]["text"], "Hallo, Welt – 한글 ü")
        self.assertEqual(m["content"][0]["thinking"], "denke...")
        self.assertEqual(m["stop_reason"], "end_turn")
        self.assertEqual(m["usage"]["output_tokens"], 42)

    def test_error_event_is_retryable_connection_error(self):
        lines = sse(("message_start", {"type": "message_start", "message": {"id": "m"}}),
                    ("error", {"type": "error", "error": {"type": "overloaded_error", "message": "Overloaded"}}))
        with self.assertRaises(requests.ConnectionError):
            rp._consume_sse(FakeStreamResp(lines))

    def test_empty_stream_is_error(self):
        with self.assertRaises(requests.ConnectionError):
            rp._consume_sse(FakeStreamResp([]))

    def test_total_deadline(self):
        with self.assertRaises(requests.Timeout):
            rp._consume_sse(FakeStreamResp(GOOD), deadline_seconds=-1)


class PostStream(unittest.TestCase):
    def test_stream_request_flags_and_response_shape(self):
        with patch("report_pipeline.requests.post", return_value=FakeStreamResp(GOOD)) as m:
            r = rp._post_anthropic({}, {"model": "x", "messages": []}, 280, stream=True)
        kw = m.call_args.kwargs
        self.assertTrue(kw["json"]["stream"])
        self.assertTrue(kw["stream"])
        self.assertEqual(kw["timeout"], (10, rp.STREAM_READ_TIMEOUT))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["content"][1]["text"], "Hallo, Welt – 한글 ü")

    def test_midstream_error_then_success_retries(self):
        bad = FakeStreamResp(sse(("error", {"type": "error", "error": {"type": "overloaded_error", "message": "x"}})))
        with patch("report_pipeline.requests.post", side_effect=[bad, FakeStreamResp(GOOD)]) as m, \
             patch("time.sleep"):
            r = rp._post_anthropic({}, {}, 280, stream=True)
        self.assertEqual(m.call_count, 2)
        self.assertEqual(r.status_code, 200)

    def test_non_stream_default_unchanged(self):
        class R:
            status_code = 200
        with patch("report_pipeline.requests.post", return_value=R()) as m:
            rp._post_anthropic({}, {"a": 1}, 5)
        self.assertNotIn("stream", m.call_args.kwargs["json"])

    def test_call_claude_uses_stream_and_returns_text(self):
        with patch("report_pipeline.requests.post", return_value=FakeStreamResp(GOOD)):
            txt = rp.call_claude("free_report_prompt.json", {"compact": "x"}, api_key="k")
        self.assertEqual(txt, "Hallo, Welt – 한글 ü")

    def test_http_error_status_still_reported(self):
        r = FakeStreamResp([], status=400, text='{"error":"bad"}')
        with patch("report_pipeline.requests.post", return_value=r):
            with self.assertRaises(rp.PipelineError):
                rp.call_claude("free_report_prompt.json", {"compact": "x"}, api_key="k")


if __name__ == "__main__":
    unittest.main()
