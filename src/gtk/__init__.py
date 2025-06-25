import platform
import subprocess
import shutil
from pathlib import Path

import gi
gi.require_version('Gtk', '4.0')
from gi.repository import GLib, Gio  # noqa: E402


def return_comp(name: str) -> str:
	if platform.system() == 'Linux':
		comp_path = shutil.which(name)
	else:  # Windows
		result = subprocess.run(
			['cygpath', '-m', f'/ucrt64/bin/{name}'],
			capture_output=True,
			text=True,
			check=True
		)
		comp_path = result.stdout.strip()
	if not comp_path:
		raise FileNotFoundError(f'{name} is not installed. Exiting...')

	return comp_path

def compile_data() -> None:
	"""
		converts all .blp files in usable .ui files using blueprint-compiler (provided you have it installed)
	"""

	if '__compiled__' in globals():
		return  # you can't build blp files if they don't exist 🤷

	blpc_path = return_comp('blueprint-compiler')
	resc_path = return_comp('glib-compile-resources')

	ui_dir = Path(__file__).parents[2] / 'src' / 'gtk' / 'ui'
	blp_files = ui_dir.glob('*.blp')
	args = ['python', blpc_path, 'batch-compile', ui_dir, ui_dir]

	for file in blp_files:
		args.extend([file])

	subprocess.run(args)
	
	res_dir = Path(__file__).parents[2] / 'src' / 'gtk' / 'res'
	xml_file = res_dir / 'resources.gresource.xml'
	if not xml_file.exists():
		raise FileNotFoundError(f'resources.gresource.xml is not present in {res_dir}. redownload rencher and try again')
	
	subprocess.run([resc_path, xml_file], cwd=res_dir)

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
		