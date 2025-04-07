import sys

from src.gtk import blp2ui
from nuitka.__main__ import main as build

args = [
	'--main=main.py',
	'--standalone',
	'--onefile'
]

sys.argv = sys.argv + args

blp2ui()
build()