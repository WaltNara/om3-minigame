import unittest

from retrigger import Command, Retrigger


class RetriggerTests(unittest.TestCase):
    def test_shot_before_long_clip_ends_stops_then_restarts_at_zero(self):
        worker = Retrigger(enabled=True)
        self.assertEqual(worker.shot(), [Command('play', 1, 0)])
        # The first clip is still playing; no end callback has occurred.
        self.assertEqual(worker.shot(), [Command('stop', 1)])
        self.assertEqual(worker.ended(1), [Command('play', 2, 0)])

    def test_rapid_shots_coalesce_to_latest_without_stop_queue(self):
        worker = Retrigger(enabled=True)
        worker.shot()
        self.assertEqual(worker.shot(), [Command('stop', 1)])
        for _ in range(100):
            self.assertEqual(worker.shot(), [])
        self.assertEqual(worker.ended(1), [Command('play', 102, 0)])
        self.assertIsNone(worker.pending)

    def test_late_completion_cannot_stop_new_sound(self):
        worker = Retrigger(enabled=True)
        worker.shot()
        worker.shot()
        worker.ended(1)
        self.assertEqual(worker.ended(1), [])
        self.assertEqual(worker.active, 2)
        self.assertEqual(worker.shot(), [Command('stop', 2)])

    def test_end_racing_with_stop_starts_pending_once(self):
        worker = Retrigger(enabled=True)
        worker.shot()
        worker.shot()
        self.assertEqual(worker.ended(1), [Command('play', 2)])
        self.assertEqual(worker.ended(1), [])

    def test_cancel_during_stop_discards_pending_restart(self):
        worker = Retrigger(enabled=True)
        worker.shot()
        worker.shot()
        self.assertEqual(worker.cancel(), [])
        self.assertEqual(worker.ended(1), [])
        self.assertIsNone(worker.active)

    def test_completed_sound_and_repeated_cancel(self):
        worker = Retrigger(enabled=True)
        worker.shot()
        self.assertEqual(worker.ended(1), [])
        self.assertEqual(worker.shot(), [Command('play', 2)])
        self.assertEqual(worker.cancel(), [Command('stop', 2)])
        self.assertEqual(worker.cancel(), [])
        self.assertEqual(worker.ended(2), [])

    def test_original_silent_default_never_requests_audio(self):
        worker = Retrigger()
        for _ in range(100):
            self.assertEqual(worker.shot(), [])
        self.assertIsNone(worker.active)
        self.assertEqual(worker.sequence, 0)

    def test_switching_off_stops_current_and_blocks_later_shots(self):
        worker = Retrigger(enabled=True)
        worker.shot()
        self.assertEqual(worker.set_enabled(False), [Command('stop', 1)])
        self.assertEqual(worker.shot(), [])
        self.assertEqual(worker.ended(1), [])
        self.assertIsNone(worker.active)

    def test_off_during_retrigger_cannot_start_pending_sound(self):
        worker = Retrigger(enabled=True)
        worker.shot()
        worker.shot()
        self.assertEqual(worker.set_enabled(False), [])
        self.assertEqual(worker.ended(1), [])
        worker.set_enabled(True)
        self.assertEqual(worker.shot(), [Command('play', 3)])


if __name__ == '__main__':
    unittest.main()
