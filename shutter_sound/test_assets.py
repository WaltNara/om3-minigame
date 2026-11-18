import hashlib
import struct
import unittest

from bank import HEADER, MAGIC, MAX_FRAMES, decode, encode, make_wav
from convert import click, convert
from audit import audit


class Assets(unittest.TestCase):
    def test_exact_pcm_and_alignment(self):
        for n in [1, 4800, MAX_FRAMES]:
            pcm = struct.pack('<hh', -2345, 6789)*n
            info = decode(encode(pcm))
            self.assertEqual(info['pcm'], pcm)
            self.assertEqual(info['frames'], n)
            self.assertEqual(info['data_offset'] % 16, 0)

    def test_rejects_truncation_corruption_and_trailing_data(self):
        bank = encode(click())
        for invalid in [bank[:8], bank[:-1], bank+b'x', bank[:70]+bytes([bank[70]^1])+bank[71:]]:
            with self.assertRaises(ValueError):
                decode(invalid)

    def test_rejects_wrong_format_with_valid_checksum(self):
        wav = bytearray(make_wav(click()))
        struct.pack_into('<I', wav, 24, 44100)
        bank = HEADER.pack(MAGIC, 1, len(wav), hashlib.sha256(wav).digest())+wav
        with self.assertRaisesRegex(ValueError, 'format'):
            decode(bank)

    def test_rejects_duration_and_partial_frames(self):
        for pcm in [b'', b'\0'*3, b'\0'*((MAX_FRAMES+1)*4)]:
            with self.assertRaises(ValueError):
                encode(pcm)

    def test_rejects_bad_header_version(self):
        bank = bytearray(encode(click()))
        struct.pack_into('<I', bank, 8, 2)
        with self.assertRaisesRegex(ValueError, 'header'):
            decode(bank)

    def test_rejects_changed_key_even_with_valid_checksum(self):
        wav = make_wav(click()).replace(b'CSHUT1', b'CSHUT2')
        bank = HEADER.pack(MAGIC, 1, len(wav), hashlib.sha256(wav).digest())+wav
        with self.assertRaisesRegex(ValueError, 'metadata'):
            decode(bank)

    def test_rejects_silent_input(self):
        with self.assertRaisesRegex(ValueError, 'silent'):
            convert(make_wav(b'\0'*400))

    def test_preserves_long_clip_without_truncation(self):
        pcm = struct.pack('<hh', 1000, -1000)*72000  # 1.5 seconds
        converted = convert(make_wav(pcm))
        self.assertEqual(len(converted), len(pcm))
        self.assertEqual(decode(encode(converted))['frames'], 72000)

    def test_convert_mono_resample_and_headroom(self):
        pcm = struct.pack('<h', 30000)*2205
        fmt = struct.pack('<HHIIHH', 1, 1, 22050, 44100, 2, 16)
        body = b'WAVEfmt '+struct.pack('<I',16)+fmt+b'data'+struct.pack('<I',len(pcm))+pcm
        got = convert(b'RIFF'+struct.pack('<I',len(body))+body)
        values = struct.unpack('<'+'h'*(len(got)//2), got)
        self.assertEqual(len(got), 4800*4)
        self.assertTrue(all(values[i] == values[i+1] for i in range(0,len(values),2)))
        self.assertLessEqual(max(values), 16384)

    def test_audit_rejects_overlapping_candidate(self):
        stock = b'\x12\x34'+b'\xff'*30
        baseline = stock[:16]+b'x'+stock[17:]
        layout = {'stock_main_sha256': hashlib.sha256(stock).hexdigest(),
                  'r5_main_sha256': hashlib.sha256(baseline).hexdigest(),
                  'notation_base':'0x50000000','runtime_base':'0x60021020',
                  'functions':{'test':{'notation':'0x50000000','expected':'1234'}},
                  'candidate_region':{'offset_start':'0x10','offset_end':'0x20'},'globals':{}}
        with self.assertRaisesRegex(ValueError,'occupied'):
            audit(stock,baseline,layout)


if __name__ == '__main__':
    unittest.main()
