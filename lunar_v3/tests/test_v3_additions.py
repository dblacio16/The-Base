"""New V3 checks: user-supplied music, astronaut redesign and intact backgrounds."""
from pathlib import Path
from unittest.mock import Mock
from hashlib import sha256
import unittest
import struct
from lunar_v3.settings import ASSETS, ROOM_VIDEOS, SAVE, ROOT
from lunar_v3.audio_manager import AudioManager

EXPECTED_BG_HASHES = {
    'hub.png': 'e66cd20a88a19364cd132bff95e4b779ecddd02359a9506dfb4275bedde4d2b4',
    'life.png': 'b7807b2046d6107e3c1e106dacfafc8e4447a22b6d24cc611cbd7b3c29f03b35',
}


class AssetTests(unittest.TestCase):
    def test_original_mission_control_and_life_support_images_unchanged(self):
        for filename, digest in EXPECTED_BG_HASHES.items():
            source=(ASSETS/'backgrounds'/filename).read_bytes()
            self.assertEqual(sha256(source).hexdigest(), digest)
        self.assertNotIn('hub', ROOM_VIDEOS)
        self.assertNotIn('life', ROOM_VIDEOS)

    def test_all_twelve_redesigned_astronaut_images_have_alpha(self):
        sprites=list((ASSETS/'astronaut').glob('*.png'))
        self.assertEqual(len(sprites), 12)
        for p in sprites:
            raw=p.read_bytes()
            self.assertEqual(raw[:8], b'\x89PNG\r\n\x1a\n')
            w,h,bit_depth,color_type=struct.unpack('>IIBB',raw[16:26])
            self.assertEqual((w,h),(96,96),p.name)
            self.assertEqual(color_type,6,p.name) # RGBA PNG

    def test_music_asset_is_mp3_and_separate_from_sfx(self):
        p=ASSETS/'music'/'Surface_Tension.mp3'
        self.assertTrue(p.is_file())
        self.assertGreater(p.stat().st_size,1_000_000)
        self.assertIn(p.read_bytes()[:3],(b'ID3',b'\xff\xfb\x90'))

    def test_v3_save_is_independent(self):
        self.assertEqual(SAVE.name,'save_v3.json')
        self.assertEqual(SAVE.parent,ROOT/'lunar_v3'/'user_data')


class _FakeMusic:
    def __init__(self):
        self.calls=[]
        self.loaded=None
        self.isbusy=True
    def load(self,p):self.loaded=p;self.calls.append('load')
    def set_volume(self,v):self.calls.append(('volume',v))
    def play(self,*args,**kwargs):self.calls.append('play')
    def pause(self):self.calls.append('pause')
    def unpause(self):self.calls.append('unpause')
    def stop(self):self.calls.append('stop')
    def get_busy(self):return self.isbusy


class MusicControlsTests(unittest.TestCase):
    def make_music(self):
        m=_FakeMusic()
        pg=Mock()
        pg.error=RuntimeError
        pg.mixer.get_init.return_value=(44100,-16,2)
        pg.mixer.music=m
        pg.mixer.Sound=lambda buffer:Mock()
        a=AudioManager(pg)
        return a,m

    def test_music_starts_in_loop_and_at_low_volume(self):
        audio,music=self.make_music()
        self.assertTrue(audio.music_available)
        self.assertEqual(music.loaded,str(ASSETS/'music'/'Surface_Tension.mp3'))
        self.assertIn('play',music.calls)
        self.assertIn(('volume',0.28),music.calls)
        self.assertTrue(audio.enabled)

    def test_music_can_pause_resume_toggle_without_restarting(self):
        audio,music=self.make_music()
        audio.pause_music()
        self.assertTrue(audio.music_paused)
        audio.resume_music()
        self.assertFalse(audio.music_paused)
        audio.toggle_music()
        self.assertFalse(audio.music_enabled)
        audio.toggle_music()
        self.assertTrue(audio.music_enabled)
        self.assertEqual(music.calls.count('play'),1)
        self.assertGreaterEqual(music.calls.count('unpause'),2)

    def test_sfx_toggle_independent_from_background_music(self):
        audio,music=self.make_music()
        self.assertFalse(audio.toggle())
        self.assertTrue(audio.music_enabled)
        self.assertTrue(audio.music_available)
        self.assertEqual(audio.adjust_music_volume(+1),1.0)
        self.assertEqual(audio.adjust_music_volume(-2),0.0)
        audio.stop()
        self.assertIn('stop',music.calls)


if __name__ == '__main__':unittest.main()
