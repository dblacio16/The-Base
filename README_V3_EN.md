# LUNAR OUTPOST V3.0 — Improved Astronaut & Surface Tension Edition

A standalone V3 expansion based on the independent V2 Pygame game. **V1 and V2 are left untouched.**

## Changes relative to V2

- Includes your improved set of **twelve 96×96 pixel-art astronaut sprites** with transparent backgrounds, normalized to a shared boots anchor in `lunar_v3/graphics.py`. No redesign of A.R.I.A.
- Includes your supplied `Surface_Tension.mp3`. It plays from the menu using `pygame.mixer.music` with an endless loop, at 28% starting volume. A separate volume control and music toggle are available in Pause. Music pauses on game pause, resumes on continue, and continues between rooms.
- All game language remains English.
- **Mission Control and Life Support PNG backgrounds are identical to V2**. No new MP4 backgrounds were created for these scenes.
- The three existing MP4s remain enabled for Generator, Radiation Shield, and Hydroponics; PNG fallback is retained.
- V3 save file and NASA cache are separate from V1/V2. Basic read-only migration is available.
- Existing gameplay, tools, ARIA expressions, NASA telemetry, four minigames, 30-sol mission remain from V2.

## Run on Windows (Python 3.10+)

```powershell
py -m pip install -r requirements-v3.txt
py CHECK_V3.py
py run_v3.py
```

## Controls

| Key | Action |
|---|---|
| A / D | Move |
| Space | Jump |
| E | Interact |
| F | Use equipped tool |
| TAB | Inventory |
| Q / R | Previous / next tool |
| H | ARIA hint |
| T | NASA telemetry |
| N (hub) | Advance one sol |
| M | Toggle music |
| B | Toggle sound effects |
| ESC | Pause, then adjust music volume and preferences |

## Project layout

- `run_v3.py`: V3 entrypoint, not `main.py`.
- `lunar_v3/game.py`: game and scene controller.
- `lunar_v3/graphics.py`: old environment graphics + new improved astronaut sprites.
- `lunar_v3/audio_manager.py`: MP3 streaming and independent short sound effects.
- `lunar_v3/assets/music/Surface_Tension.mp3`: the user-provided MP3.
- `lunar_v3/assets/astronaut/`: twelve new 96px pose PNGs.
- `lunar_v3/assets/astronaut_sheets/`: original spritesheets supplied, optional future reference.
- `lunar_v3/assets/backgrounds/{hub,life}.png`: V2 images preserved byte-for-byte.
- `lunar_v3/assets/video/`: three original V2 MP4s.
- `lunar_v3/user_data/`: separate saved games, excluded from Git.
- `requirements-v3.txt`: V3-specific dependencies.

## Tests

```powershell
py -m unittest discover -s lunar_v3/tests -v
```

37 automated tests cover core gameplay, asset identity, user sprite validation, video decoding, MP3 presence, music controls, and independence of saved games.

## Background music redistribution

The music was supplied by the project user. Including a file here does not establish the right to redistribute it publicly. The included `lunar_v3/.gitignore` excludes the MP3 by default. Please check its license before publishing your game or soundtrack online. The V3 game runs locally with the included MP3; after cloning a public GitHub repo, users will need an authorized copy of the soundtrack in `lunar_v3/assets/music/` or can play without it.

## Limits

The MP4s were decoded by automated test tools. Real Pygame window interaction and actual audible playback could not be verified in this build environment (Pygame itself was unavailable). Video and MP3 decoding on your computer depend on the local graphics/audio setup.
