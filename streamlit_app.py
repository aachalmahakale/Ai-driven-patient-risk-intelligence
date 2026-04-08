from pathlib import Path
import runpy
import sys

ROOT_DIR = Path(__file__).resolve().parent
SRC_DIR = ROOT_DIR / "src"
APP_PATH = SRC_DIR / "app.py"

if str(SRC_DIR) not in sys.path:
	sys.path.insert(0, str(SRC_DIR))

runpy.run_path(str(APP_PATH), run_name="__main__")
