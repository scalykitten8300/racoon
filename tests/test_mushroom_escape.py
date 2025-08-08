import os
import subprocess
import sys


def test_mushroom_escape_runs():
    env = os.environ.copy()
    env["SDL_VIDEODRIVER"] = "dummy"
    env["HEADLESS_TEST"] = "1"
    result = subprocess.run([sys.executable, "mushroom_escape.py"], env=env, check=True, capture_output=True)
    assert result.returncode == 0
