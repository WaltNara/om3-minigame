import json
from pathlib import Path
import struct
import unittest

from bank import RATE
from prepare_presets import camera_edit, burst_preview


class Presets(unittest.TestCase):
    def test_silent_catalog_entry_has_no_bank_and_is_default(self):
        cat = json.loads(Path(__file__).with_name('presets.json').read_text())
        self.assertEqual(cat['default'], 'silent')
        self.assertIsNone(cat['silent']['bank'])

    def test_burst_edit_onset_duration_headroom_and_edges(self):
        pcm = bytes(9600*4)+struct.pack('<hh', 30000, -30000)*9600
        edited, start = camera_edit(pcm, 60)
        self.assertAlmostEqual(start, 0.199)
        self.assertEqual(len(edited), 2880*4)
        values = struct.unpack('<'+'h'*(len(edited)//2), edited)
        self.assertLessEqual(max(map(abs, values)), 16384)
        self.assertEqual(values[:2], (0,0))
        self.assertEqual(values[-2:], (0,0))

    def test_ten_fps_keeps_40ms_gap_after_60ms_click(self):
        pcm = struct.pack('<hh', 1000, -1000)*2880
        got = burst_preview(pcm,10,10)
        self.assertEqual(len(got), RATE*4)
        for i in range(10):
            segment = got[i*19200:(i+1)*19200]
            self.assertEqual(segment[:11520], pcm)
            self.assertEqual(segment[11520:], bytes(7680))

    def test_twenty_fps_restarts_long_sound_without_mixing(self):
        pcm = b''.join(struct.pack('<hh', i, -i) for i in range(10000))
        got = burst_preview(pcm,20,10)
        for i in range(10):
            self.assertEqual(got[i*9600:(i+1)*9600], pcm[:9600])


if __name__ == '__main__':
    unittest.main()
