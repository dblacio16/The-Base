"""Desktop Lunar Outpost 2.0 settings. All in-game text is English."""
from pathlib import Path
PACKAGE_ROOT=Path(__file__).resolve().parent
ROOT=PACKAGE_ROOT.parent  # existing V1 repository root; never overwrite its files
ASSETS=PACKAGE_ROOT/'assets'
DATA=PACKAGE_ROOT/'user_data'
SAVE=DATA/'save_v3.json'
NASA_CACHE=DATA/'donki_cache_v3.json'
WIDTH, HEIGHT, FPS=1280, 720, 60
GROUND=552
CYAN=(75,221,246)
WHITE=(236,245,252)
MUTED=(160,181,196)
YELLOW=(247,199,90)
GREEN=(90,224,156)
RED=(251,99,103)
PURPLE=(178,156,245)
DARK=(8,20,33)
PANEL=(13,30,46)
EDGE=(77,106,128)
ROOMS=('life','generator','radiation','hydro')
NAMES={'life':'LIFE SUPPORT','generator':'POWER GENERATOR','radiation':'RADIATION SHIELD','hydro':'HYDROPONIC DOME'}
RESOURCES=('life','energy','food','integrity')
RES_NAMES={'life':'LIFE SUPPORT','energy':'ENERGY','food':'FOOD','integrity':'INTEGRITY'}
COLORS={'life':CYAN,'energy':YELLOW,'food':GREEN,'integrity':PURPLE}
ROOM_VIDEOS={'generator':'gemini_generated_video_75342023.mp4','radiation':'gemini_generated_video_33587f4c.mp4','hydro':'gemini_generated_video_1bcd337a.mp4'}

# V3 keeps the existing hub/life PNG backgrounds; videos remain limited to V2's three rooms.
