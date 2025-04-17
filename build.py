import sys
from pathlib import Path

from src.gtk import blp2ui
from nuitka import __main__ as nuitka

blp2ui()
ui_path = Path(sys.executable).parents[2] / 'src' / 'gtk' / 'ui'

args = [
	'--main=main.py',
	'--standalone',
	'--onefile',
	f'--include-data-dir={ui_path}=src/gtk/ui'
]

sys.argv = sys.argv + args

nuitka.main()