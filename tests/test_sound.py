import unittest
import sys
import os
import shutil
import tempfile

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from nous_anki.sound import NousSoundPlayer


class TestSoundPlayer(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_audio_generation(self):
        player = NousSoundPlayer(self.test_dir)
        self.assertTrue(os.path.exists(player.bell_path))
        self.assertTrue(os.path.exists(player.chime_path))
        self.assertGreater(os.path.getsize(player.bell_path), 50000)
        self.assertGreater(os.path.getsize(player.chime_path), 50000)

    def test_mute_toggle(self):
        player = NousSoundPlayer(self.test_dir)
        self.assertFalse(player.muted)
        player.muted = True
        self.assertTrue(player.muted)


if __name__ == "__main__":
    unittest.main()
