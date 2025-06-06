import platform
import subprocess
import shutil
from pathlib import Path

import gi
gi.require_version('Gtk', '4.0')
from gi.repository import GLib, Gio, GObject  # noqa: E402


def blp2ui() -> None:
	"""
		converts all .blp files in usable .ui files using blueprint-compiler (provided you have it installed)
	"""

	if '__compiled__' in globals():
		return  # you can't build blp files if they don't exist 🤷

	if platform.system() == 'Linux':
		comp_path = shutil.which('blueprint-compiler')
	else:  # Windows
		result = subprocess.run(
			['cygpath', '-m', '/ucrt64/bin/blueprint-compiler'],
			capture_output=True,
			text=True,
			check=True
		)
		comp_path = result.stdout.strip()
	if not comp_path:
		raise FileNotFoundError('blueprint-compiler is not installed. Exiting...')

	ui_path = Path(__file__).parents[2] / 'src' / 'gtk' / 'ui'
	blp_paths = ui_path.glob('*.blp')
	args = ['python', comp_path, 'batch-compile', ui_path, ui_path]

	for path in blp_paths:
		args.extend([path])

	subprocess.run(args)

def format_gdatetime(date: GLib.DateTime, style: str) -> str:
	"""
	dates are utc

	Args:
		date: made from glib cause it's easier to work with

		style: can be:
		 * 'detailed': 'Monday, 23 December 2024, 13:23:20 (%A, %d %B %Y, %H:%M:%S)
		 * 'neat': 23 Dec 2024, 01:23 PM (%d %b %Y, %I:%M %p)
		 * 'runtime': 30:15:06 (hours:minutes:seconds)
	"""

	if style not in ['detailed', 'neat', 'runtime']:
		raise NotImplementedError('fucking idiot. choose something else')

	formatted_date = ''
	if style == 'neat':
		formatted_date = date.format('%d %b %Y, %I:%M %p')
	elif style == 'detailed':
		formatted_date = date.format('%A, %d %B %Y, %H:%M:%S')
	else:
		time = date.to_unix()
		hours = int(time / 3600)
		minutes = int((time % 3600) / 60)
		seconds = int((time % 3600) % 60)

		formatted_date = f'{hours:02}:{minutes:02}:{seconds:02}'

		if formatted_date == '00:00:00':
			return 'N/A'

	return formatted_date

def open_file_manager(path: str):
	if platform.system() == 'Linux':
		Gio.AppInfo.launch_default_for_uri('file:///' + path)

def windowficate_file(file: Path | str) -> Path | str:
	"""
	returns a file that abides by the windows file naming conventions
	
	Args:
		file (Path | str): is used
	Returns:
		Path: the new path
	"""
	forbidden_characters = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
	forbidden_names = ['CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'COM¹', 'COM²', 'COM³', 'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9', 'LPT¹', 'LPT²', 'LPT³']
	
	if isinstance(file, Path):
		name = file.stem
	elif isinstance(file, str):
		name = file
	else:
		raise TypeError()
	
	new_name = ''
	for character in name:
		if character in forbidden_characters:
			new_name += '_'
		else:
			new_name += character
	if name in forbidden_names:
			raise ValueError()

	if isinstance(file, Path):
		return file.with_stem(new_name)
	else:
		return new_name
		
class GameItem(GObject.Object):
	__gtype_name__ = 'GameItem'
	
	name = GObject.Property(type=str)
	
	def __init__(self, name, game):
		super().__init__()
		self.name = name
		self.game = game
