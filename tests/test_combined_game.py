"""All registered game checks against the combined image; never packages."""

import sys as _sys
from pathlib import Path as _Path
_sys.path[:0] = [str(_Path(__file__).resolve().parents[1] / "native"), str(_Path(__file__).resolve().parents[1] / "tests")]
import os,subprocess,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]
env=dict(os.environ,OM3_GAME_BUILD='work/combined-game')
for script in ['test_mario_core.py','test_mario_render.py','test_mario_game.py','test_mines_core.py','test_mines_render.py','test_mines_game.py']:
    print('Checking',script,flush=True)
    subprocess.run([sys.executable,str(R/'tests'/script)],cwd=R,env=env,check=True)
