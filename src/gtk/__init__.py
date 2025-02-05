import subprocess, shutil
from datetime import datetime
from pathlib import Path

import gi

from src import format_gdatetime

gi.require_version('Gtk', '4.0')
from gi.repository import GObject, GLib

from src.renpy import Game


def blp2ui() -> None:
	"""
		converts all .blp files in usable .ui files using blueprint-compiler (provided you have it installed)
	"""

	comp_path = shutil.which('blueprint-compiler')
	if not comp_path:
		raise FileNotFoundError('blueprint-compiler is not installed. Exiting...')

	ui_path = Path.cwd() / 'src' / 'gtk' / 'ui'
	blp_paths = ui_path.glob('*.blp')
	args = [comp_path, 'batch-compile', ui_path, ui_path]

	for path in blp_paths:
		args.extend([path])

	subprocess.run(args)
