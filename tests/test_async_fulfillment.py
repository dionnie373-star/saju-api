"""비동기 리포트 생성(_start_fulfillment) 테스트: 즉시 응답, 성공 시 토큰 삭제, 실패 시 unmark+알림, 재시도."""
import os
import threading
import unittest

os.environ.setdefault("ANTHROPIC_API_KEY", "test-not-used")
os.environ.setdefault("BREVO_API_KEY", "test-not-used")
os.environ.setdefault("FROM_EMAIL", "test@example.com")

import app as app_module  # noqa: E402
import orders_store  # noqa: E402
import report_pipeline  # noqa: E402


class AsyncFulfillmentTests(unittest.TestCase):
    def setUp(self):
        orders_store.reset_for_tests()
        self._saved = (app_module.FULFILL_ASYNC, app_module.FULFILL_RETRY_DELAY_SECONDS,
                       app_module._alert_owner, app_module._fulfill_report_order)
        app_module.FULFILL_ASYNC = True
        app_module.FULFILL_RETRY_DELAY_SECONDS = 0
        self.alerts = []
        app_module._alert_owner = lambda subject, body: self.alerts.append((subject, body))
        orders_store.store_pending_order("tok", {"email": "k@example.com"})
        orders_store.try_mark_processed("fungies", "o1")

    def tearDown(self):
        (app_module.FULFILL_ASYNC, app_module.FULFILL_RETRY_DELAY_SECONDS,
         app_module._alert_owner, app_module._fulfill_report_order) = self._saved
        orders_store.reset_for_tests()

    def _start_and_join(self):
        before = set(threading.enumerate())
        resp, status = app_module._start_fulfillment("fungies", "o1", "tok", "paid", {}, "k@example.com")
        for t in set(threading.enumerate()) - before:
            t.join(5)
        return resp, status

    def test_responds_before_pipeline_finishes(self):
        gate = threading.Event()
        done = threading.Event()

        def slow(*a, **k):
            gate.wait(5)
            done.set()
            return {}, 200
        app_module._fulfill_report_order = slow
        resp, status = app_module._start_fulfillment("fungies", "o1", "tok", "paid", {}, "k@example.com")
        self.assertEqual(status, 200)
        self.assertTrue(resp["accepted"])
        self.assertFalse(done.is_set())  # 응답 시점엔 아직 생성 중
        gate.set()
        self.assertTrue(done.wait(5))

    def test_success_deletes_pending_token(self):
        app_module._fulfill_report_order = lambda *a, **k: ({}, 200)
        self._start_and_join()
        self.assertFalse(orders_store.pending_token_exists("tok"))
        self.assertEqual(self.alerts, [])

    def test_failure_unmarks_keeps_token_and_alerts(self):
        def boom(*a, **k):
            raise report_pipeline.PipelineError("down", 502)
        app_module._fulfill_report_order = boom
        self._start_and_join()
        self.assertTrue(orders_store.pending_token_exists("tok"))
        self.assertTrue(orders_store.try_mark_processed("fungies", "o1"))  # unmark됨 -> 다시 표시 가능
        self.assertEqual(len(self.alerts), 1)
        self.assertIn("k@example.com", self.alerts[0][1])

    def test_retries_on_server_error_then_succeeds(self):
        calls = []

        def flaky(*a, **k):
            calls.append(1)
            if len(calls) == 1:
                raise report_pipeline.PipelineError("overloaded", 529)
            return {}, 200
        app_module._fulfill_report_order = flaky
        self._start_and_join()
        self.assertEqual(len(calls), 2)
        self.assertFalse(orders_store.pending_token_exists("tok"))
        self.assertEqual(self.alerts, [])

    def test_input_error_not_retried(self):
        calls = []

        def bad(*a, **k):
            calls.append(1)
            raise report_pipeline.PipelineError("bad input", 400)
        app_module._fulfill_report_order = bad
        self._start_and_join()
        self.assertEqual(len(calls), 1)
        self.assertEqual(len(self.alerts), 1)


if __name__ == "__main__":
    unittest.main()
