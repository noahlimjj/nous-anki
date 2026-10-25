import unittest
import sys
import os
import shutil
import tempfile
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from nous_anki.sync import TimeAccumulator, NousSyncService


class TestSync(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_accumulator_bounded_duration(self):
        acc = TimeAccumulator(max_card_seconds=60.0)
        # Add 3 cards: 5s, 10s, and a long 120s card (capped to 60s)
        acc.add_card_time(5000)
        acc.add_card_time(10000)
        acc.add_card_time(120000)

        self.assertEqual(acc.current_cards, 3)
        # Expected: 5s + 10s + 60s = 75s = 75000 ms
        self.assertEqual(acc.current_duration_ms, 75000)

        # Drain session
        session = acc.drain_session(min_ms=1000)
        self.assertIsNotNone(session)
        self.assertEqual(session["durationMs"], 75000)
        self.assertEqual(session["cardsCount"], 3)
        self.assertIn("startTime", session)
        self.assertIn("endTime", session)

        # After drain, accumulator is reset
        self.assertEqual(acc.current_duration_ms, 0)
        self.assertEqual(acc.current_cards, 0)

    def test_offline_queue(self):
        service = NousSyncService(self.test_dir)
        self.assertEqual(len(service.get_pending_queue()), 0)

        fake_session = {
            "startTime": "2026-10-25T10:00:00Z",
            "endTime": "2026-10-25T10:10:00Z",
            "durationMs": 600000,
            "cardsCount": 20,
            "createdAt": "2026-10-25T10:10:00Z"
        }
        service.enqueue_session(fake_session)

        queue = service.get_pending_queue()
        self.assertEqual(len(queue), 1)
        self.assertEqual(queue[0]["durationMs"], 600000)


if __name__ == "__main__":
    unittest.main()
