"""Offline V3 preflight: files, intact backgrounds, 3 MP4 decoders, audio and sprites."""
from pathlib import Path
import hashlib
import struct
import sys
import traceback

ROOT=Path(__file__).resolve().parent
ASSETS=ROOT/'lunar_v3'/'assets'
HASHES={
 'hub.png':'e66cd20a88a19364cd132bff95e4b779ecddd02359a9506dfb4275bedde4d2b4',
 'life.png':'b7807b2046d6107e3c1e106dacfafc8e4447a22b6d24cc611cbd7b3c29f03b35',
}
VIDEO_NAMES={
 'generator':'gemini_generated_video_75342023.mp4',
 'radiation':'gemini_generated_video_33587f4c.mp4',
 'hydro':'gemini_generated_video_1bcd337a.mp4',
}

def main():
    failures=[]
    print('LUNAR OUTPOST V3.0 / PRE-FLIGHT CHECK')
    print('-----------------------------------')
    for name,digest in HASHES.items():
        path=ASSETS/'backgrounds'/name
        actual=hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
        ok=actual==digest
        print(f"{'OK  ' if ok else 'FAIL'} Unchanged V2 background: {name}")
        if not ok:failures.append(f'Background altered: {name}')
    print('Hub and life support remain PNG backgrounds, intentionally NOT MP4.')
    sprites=list((ASSETS/'astronaut').glob('*.png'))
    ok=len(sprites)==12
    for path in sprites:
        raw=path.read_bytes()
        ok = ok and raw[:8]==b'\x89PNG\r\n\x1a\n'
        if ok:
            width,height,depth,colortype=struct.unpack('>IIBB',raw[16:26])
            ok=(width,height,colortype)==(96,96,6)
    print(f"{'OK  ' if ok else 'FAIL'} Improved 96px astronaut sprite set: {len(sprites)}/12")
    if not ok:failures.append('Improved sprite set incomplete')
    music=ASSETS/'music'/'Surface_Tension.mp3'
    ok=music.is_file() and music.stat().st_size>1_000_000
    print(f"{'OK  ' if ok else 'FAIL'} Surface Tension MP3 included")
    if not ok:failures.append('Missing Surface Tension MP3')
    try:
        import cv2
        for key,name in VIDEO_NAMES.items():
            p=ASSETS/'video'/name
            cap=cv2.VideoCapture(str(p))
            try:
                result,frame=cap.read()
                ok=result and frame is not None and frame.shape[1]==1280 and frame.shape[0]==720
                print(f"{'OK  ' if ok else 'FAIL'} {key.upper()}: MP4 decoding 1280 x 720")
                if not ok:failures.append(f'MP4 not decodable: {name}')
            finally:cap.release()
    except ImportError:
        print('SKIP MP4 decoding check: install opencv-python first')
    try:
        import pygame
        print('OK   pygame installed:',pygame.version.ver)
    except ImportError:
        print('SKIP pygame run check: install Pygame first')
    if any((ROOT/f).exists() for f in ('main.py','game.py','settings.py','requirements.txt')):
        failures.append('Potential overwrite of protected V1 filenames')
    print('-----------------------------------')
    if failures:
        print('PROBLEMS:')
        for issue in failures: print(' -',issue)
        return 1
    print('SUCCESS: Files and decoders are prepared. Start with: py run_v3.py')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
