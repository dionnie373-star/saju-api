import threading
import time
import unittest
from unittest import mock

import app
import orders_store


class OrderRecoveryTests(unittest.TestCase):
    def setUp(self):
        orders_store.reset_for_tests()
        orders_store.store_pending_order("tok1", {"email": "a@b.de", "birth_date": "1990-01-01"})

    def _claim(self, age, recoveries=0):
        orders_store.claim_pending_order("tok1", {
            "provider": "digistore24", "order_id": "O1", "tier": "paid", "email": "a@b.de",
            "started_at": time.time() - age, "recoveries": recoveries,
        })

    def test_claim_hidden_from_data(self):
        self._claim(0)
        entry = orders_store.get_pending_order("tok1")
        self.assertNotIn("_claim", entry["data"])
        self.assertEqual(entry["claim"]["order_id"], "O1")

    def test_fresh_claim_not_recovered(self):
        self._claim(60)
        with mock.patch.object(app, "_fulfill_with_retry") as f, mock.patch.object(app, "_alert_owner"):
            self.assertEqual(app.recover_stalled_orders(), 0)
            f.assert_not_called()

    def test_stalled_claim_recovered_once_then_capped(self):
        done = threading.Event()
        with mock.patch.object(app, "_fulfill_with_retry", side_effect=lambda *a: done.set()) as f, \
             mock.patch.object(app, "_alert_owner") as alert:
            self._claim(app.RECOVERY_STALE_SECONDS + 5)
            self.assertEqual(app.recover_stalled_orders(), 1)
            self.assertTrue(done.wait(2))
            args = f.call_args[0]
            self.assertEqual(args[:4], ("digistore24", "O1", "tok1", "paid"))
            self.assertNotIn("_claim", args[4])
            self.assertTrue(orders_store.is_marked_processed("digistore24", "O1"))
            # 방금 갱신됐으므로 바로 다시 돌려도 중복 시작하지 않는다
            self.assertEqual(app.recover_stalled_orders(), 0)
            # 복구 횟수 상한: 이미 상한만큼 시도했으면 시작하지 않고 알림만
            orders_store.cas_claim("tok1", orders_store.get_pending_order("tok1")["claim"]["started_at"], {
                "provider": "digistore24", "order_id": "O1", "tier": "paid", "email": "a@b.de",
                "started_at": time.time() - app.RECOVERY_STALE_SECONDS - 5,
                "recoveries": app.RECOVERY_MAX_RECOVERIES,
            })
            f.reset_mock(); alert.reset_mock()
            self.assertEqual(app.recover_stalled_orders(), 0)
            f.assert_not_called()
            self.assertEqual(alert.call_count, 1)
            self.assertEqual(app.recover_stalled_orders(), 0)
            self.assertEqual(alert.call_count, 1)  # 포기 알림은 한 번만

    def test_cas_rejects_stale_expectation(self):
        self._claim(100)
        self.assertFalse(orders_store.cas_claim("tok1", 123.0, {"started_at": 1}))

    def test_start_fulfillment_records_claim(self):
        with mock.patch.object(app, "FULFILL_ASYNC", True), \
             mock.patch.object(app.threading, "Thread") as T:
            app._start_fulfillment("digistore24", "O1", "tok1", "paid", {"email": "a@b.de"}, "a@b.de")
        claim = orders_store.get_pending_order("tok1")["claim"]
        self.assertEqual((claim["order_id"], claim["tier"], claim["recoveries"]), ("O1", "paid", 0))
        T.return_value.start.assert_called_once()


if __name__ == "__main__":
    unittest.main()
