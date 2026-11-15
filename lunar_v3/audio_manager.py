"""Independent music and synthetic SFX playback for Lunar Outpost V3.

This module handles the user-supplied Surface_Tension.mp3, and never reads
it unless installed in the V3 assets/music directory. Audio is optional:
headless systems and unavailable MP3 decoders do not crash the game.
"""
import math
from array import array
from .settings import ASSETS


class AudioManager:
    def __init__(self, pygame):
        self.pg = pygame
        self.enabled = True   # effects on/off, kept for V2 compatibility
        self.music_enabled = True
        self.music_available = False
        self.music_volume = 0.28
        self.music_paused = False
        self.sounds = {}
        self.music_file = ASSETS / 'music' / 'Surface_Tension.mp3'
        self.last_error = ''
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            # Mixer may negotiate a different format; Sound() accepts a generated
            # waveform through array buffers, as in V2. Music is streamed, not fully loaded as a Sound.
            for key, notes in {
                'tap': [(540, 0.05)],
                'collect': [(520, 0.06), (760, 0.09)],
                'success': [(480, 0.12), (620, 0.12), (850, 0.19)],
                'error': [(230, 0.16), (160, 0.14)],
            }.items():
                samples = array('h')
                for freq, seconds in notes:
                    length = int(44100 * seconds)
                    for i in range(length):
                        envelope = min(1.0, i / 600) * max(0.0, 1.0 - i / length)
                        sample = round(9000 * envelope * math.sin(2 * math.pi * freq * i / 44100))
                        # Two channels, matching mixer pre_init, so no playback speed mismatch.
                        samples.extend((sample, sample))
                self.sounds[key] = pygame.mixer.Sound(buffer=samples.tobytes())
        except (pygame.error, AttributeError, ValueError) as exc:
            self.last_error = str(exc)
            self.enabled = False
        self.start_music()

    def start_music(self):
        if not self.music_file.is_file():
            self.music_available = False
            self.last_error = 'Music file not found.'
            return False
        try:
            if not self.pg.mixer.get_init():
                self.pg.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            self.pg.mixer.music.load(str(self.music_file))
            self.pg.mixer.music.set_volume(self.music_volume if self.music_enabled else 0)
            if self.music_enabled:
                self.pg.mixer.music.play(-1, fade_ms=750)
            self.music_available = True
            return True
        except (self.pg.error, AttributeError, OSError, ValueError) as exc:
            self.last_error = f'Music unavailable: {type(exc).__name__}: {exc}'
            self.music_available = False
            return False

    def play(self, key):
        if not self.enabled:
            return
        sound = self.sounds.get(key)
        if sound is not None:
            try:
                sound.play()
            except (self.pg.error, AttributeError):
                pass

    def toggle(self):
        """Toggle short synthesized SFX only. Compatible with V2 toggle action."""
        self.enabled = not self.enabled
        return self.enabled

    def toggle_music(self):
        self.music_enabled = not self.music_enabled
        if self.music_available:
            try:
                if self.music_enabled:
                    if self.music_paused:
                        self.pg.mixer.music.unpause()
                    elif not self.pg.mixer.music.get_busy():
                        self.pg.mixer.music.play(-1, fade_ms=500)
                    self.music_paused = False
                    self.pg.mixer.music.set_volume(self.music_volume)
                else:
                    self.pg.mixer.music.pause()
                    self.music_paused = True
            except (self.pg.error, AttributeError):
                self.music_available = False
        return self.music_enabled

    def adjust_music_volume(self, delta):
        self.music_volume = round(max(0, min(1, self.music_volume + delta)), 2)
        if self.music_available:
            try:
                self.pg.mixer.music.set_volume(self.music_volume)
            except (self.pg.error, AttributeError):
                self.music_available = False
        return self.music_volume

    def pause_music(self):
        if self.music_enabled and self.music_available and not self.music_paused:
            try:
                self.pg.mixer.music.pause()
                self.music_paused = True
            except (self.pg.error, AttributeError):
                self.music_available = False

    def resume_music(self):
        if self.music_enabled and self.music_available and self.music_paused:
            try:
                self.pg.mixer.music.unpause()
                self.music_paused = False
            except (self.pg.error, AttributeError):
                self.music_available = False

    def stop(self):
        try:
            self.pg.mixer.music.stop()
        except (self.pg.error, AttributeError):
            pass
