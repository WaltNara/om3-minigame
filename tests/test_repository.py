"""Meaningful integrity failures must remain failures in both build and packaging."""
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'build'))
import manifest
import package


class Reports(unittest.TestCase):
    def test_known_formats(self):
        for status, key in [('passed', 'image_sha256'), ('PASS emulator only', 'candidate_sha256'),
                            ('PASS emulator native application/GUI protocol', 'candidate_sha256')]:
            manifest.check_report({'status': status, key: 'abc'}, 'abc')

    def test_missing_stale_or_conflicting_hash(self):
        for report in [{'status': 'passed'}, {'status': 'passed', 'candidate_sha256': 'old'},
                       {'status': 'passed', 'candidate_sha256': 'abc', 'image_sha256': 'old'}]:
            with self.assertRaises(ValueError):
                manifest.check_report(report, 'abc')

    def test_reject_nonpass(self):
        for status in ['failed', 'PASS but failed afterwards', 'pending', None]:
            with self.assertRaises(ValueError):
                manifest.check_report({'status': status, 'candidate_sha256': 'abc'}, 'abc')

    def test_package_readme_current_touch(self):
        data = manifest.load()
        text = package.readme(data, {'extension_used_bytes': 237568,
            'linked_blob_bytes': 235140, 'main_image_sha256': 'test'}, {})
        self.assertIn('Flappy owns touch', text)
        self.assertNotIn('never tested on a physical camera', text)
        self.assertNotIn('All game touch interception', text)


if __name__ == '__main__':
    unittest.main()
