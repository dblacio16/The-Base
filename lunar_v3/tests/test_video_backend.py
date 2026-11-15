"""Test real bundled MP4 decoding independently of the Pygame display."""
from pathlib import Path
import sys
import time
import unittest

from lunar_v3.video_background import VideoBackground
from lunar_v3.settings import ASSETS, ROOM_VIDEOS, SAVE, ROOT


class VideoBackendTests(unittest.TestCase):
    def test_mp4_files_present(self):
        self.assertEqual(set(ROOM_VIDEOS), {'generator','radiation','hydro'})
        for scene, file in ROOM_VIDEOS.items():
            with self.subTest(scene=scene):
                self.assertTrue((ASSETS/'video'/file).is_file())

    def test_playback_releases_decoder(self):
        try:import cv2  # noqa
        except ImportError:self.skipTest('opencv-python not installed')
        for scene, filename in ROOM_VIDEOS.items():
            player=VideoBackground()
            with self.subTest(scene=scene):
                try:
                    player.open(ASSETS/'video'/filename)
                    stop=time.monotonic()+2
                    while player.sequence<2 and not player.error and time.monotonic()<stop:
                        time.sleep(.04)
                    self.assertTrue(player.loaded,player.error)
                    self.assertGreaterEqual(player.sequence,2,player.error)
                    self.assertEqual(player.latest[1],(1280,720))
                finally:player.close()
                self.assertIsNone(player.active_path)
                self.assertIsNone(player.thread)

    def test_video_end_can_seek_to_beginning(self):
        try:import cv2
        except ImportError:self.skipTest('opencv-python not installed')
        path=ASSETS/'video'/ROOM_VIDEOS['hydro']
        cap=cv2.VideoCapture(str(path))
        try:
            count=int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            self.assertGreater(count,10)
            cap.set(cv2.CAP_PROP_POS_FRAMES,count-1)
            self.assertTrue(cap.read()[0])
            self.assertFalse(cap.read()[0])
            cap.set(cv2.CAP_PROP_POS_FRAMES,0)
            self.assertTrue(cap.read()[0])
        finally:cap.release()

    def test_overlay_does_not_replace_v1_files(self):
        addon=ROOT
        for protected in ('main.py','game.py','settings.py','requirements.txt','game_state.py'):
            self.assertFalse((addon/protected).exists(),f'V1 protected file bundled: {protected}')
        self.assertTrue((addon/'run_v3.py').is_file())
        self.assertTrue((addon/'requirements-v3.txt').is_file())

    def test_savedata_is_not_in_v1_path(self):
        self.assertEqual(SAVE.parent,ASSETS.parent/'user_data')
        self.assertNotEqual(SAVE,ROOT/'data'/'savegame.json')


if __name__=='__main__':unittest.main()
