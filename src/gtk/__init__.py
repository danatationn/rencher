import subprocess, shutil
from pathlib import Path

import gi
gi.require_version('Gtk', '4.0')
from gi.repository import GObject

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


class GameInfo(GObject.Object):
	"""
		gobject please implement Path please plz pl0x
	"""
	name = GObject.Property(type=str, default=None)
	codename = GObject.Property(type=str, default=None)
	rpath = GObject.Property(type=str, default=None)
	apath = GObject.Property(type=str, default=None)
	version = GObject.Property(type=str, default=None)

	def __init__(self, game: Game | None = None):
		super().__init__()

		if game:
			self.change_game(game)

	def change_game(self, game: Game | None):
		if game:
			self.name = game.name
			self.codename = game.codename
			self.rpath = str(game.rpath)
			self.apath = str(game.apath)
			self.version = game.version
		else:
			properties = self.get_properties()
			for prop in properties:
				prop = None