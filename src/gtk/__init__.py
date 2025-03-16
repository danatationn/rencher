import logging
import platform
import subprocess
import shutil
import sys
from pathlib import Path

from src import root_path

import gi
gi.require_version('Gtk', '4.0')
from gi.repository import GLib, Gio, GObject  # noqa: E402


def blp2ui() -> None:
	"""
		converts all .blp files in usable .ui files using blueprint-compiler (provided you have it installed)
	"""

	if getattr(sys, 'frozen', False):
		return  # you can't build blp files if they don't exist 🤷

	comp_path = shutil.which('blueprint-compiler')
	if not comp_path:
		raise FileNotFoundError('blueprint-compiler is not installed. Exiting...')

	ui_path = root_path / 'src' / 'gtk' / 'ui'
	blp_paths = ui_path.glob('*.blp')
	args = [comp_path, 'batch-compile', ui_path, ui_path]

	for path in blp_paths:
		args.extend([path])

	subprocess.run(args)


def format_gdatetime(date: GLib.DateTime, style: str) -> str:
	"""
	nice little helper function for dates :)

	dates are utc

	styles can be:

	* 'detailed' - Monday, 23 December 2024, 13:23:20 (%A, %d %B %Y, %H:%M:%S)
	* 'neat' - 23 Dec 2024, 01:23 PM (%d %b %Y, %I:%M %p)
	"""

	if style not in ['detailed', 'neat']:
		raise NotImplementedError('fucking idiot. choose something else')

	formatted_date = ''
	if style == 'neat':
		formatted_date = date.format('%d %b %Y, %I:%M %p')
	if style == 'detailed':
		formatted_date = date.format('%A, %d %B %Y, %H:%M:%S')

	return formatted_date


def open_file_manager(path: str):
	if platform.system() == 'Linux':
		Gio.AppInfo.launch_default_for_uri('file:///' + path)


class GameItem(GObject.Object):
	__gtype_name__ = 'GameItem'
	
	name = GObject.Property(type=str)
	
	def __init__(self, name, game):
		super().__init__()
		self.name = name
		self.game = game
