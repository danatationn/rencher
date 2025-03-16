import logging
import platform
import subprocess
import shutil
import sys
from pathlib import Path
from typing import List, Union

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


class HumanBytes:  # borrowed from https://stackoverflow.com/a/63839503 :)
	METRIC_LABELS: List[str] = ["B", "kB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"]
	BINARY_LABELS: List[str] = ["B", "KiB", "MiB", "GiB", "TiB", "PiB", "EiB", "ZiB", "YiB"]
	PRECISION_OFFSETS: List[float] = [0.5, 0.05, 0.005, 0.0005] # PREDEFINED FOR SPEED.
	PRECISION_FORMATS: List[str] = ["{}{:.0f} {}", "{}{:.1f} {}", "{}{:.2f} {}", "{}{:.3f} {}"] # PREDEFINED FOR SPEED.

	@staticmethod
	def format(num: Union[int, float], metric: bool=False, precision: int=1) -> str:
		"""
		Human-readable formatting of bytes, using binary (powers of 1024)
		or metric (powers of 1000) representation.
		"""

		assert isinstance(num, (int, float)), "num must be an int or float"
		assert isinstance(metric, bool), "metric must be a bool"
		assert isinstance(precision, int) and precision >= 0 and precision <= 3, "precision must be an int (range 0-3)"

		unit_labels = HumanBytes.METRIC_LABELS if metric else HumanBytes.BINARY_LABELS
		last_label = unit_labels[-1]
		unit_step = 1000 if metric else 1024
		unit_step_thresh = unit_step - HumanBytes.PRECISION_OFFSETS[precision]

		is_negative = num < 0
		if is_negative: # Faster than ternary assignment or always running abs().
			num = abs(num)

		for unit in unit_labels:
			if num < unit_step_thresh:
				# VERY IMPORTANT:
				# Only accepts the CURRENT unit if we're BELOW the threshold where
				# float rounding behavior would place us into the NEXT unit: F.ex.
				# when rounding a float to 1 decimal, any number ">= 1023.95" will
				# be rounded to "1024.0". Obviously we don't want ugly output such
				# as "1024.0 KiB", since the proper term for that is "1.0 MiB".
				break
			if unit != last_label:
				# We only shrink the number if we HAVEN'T reached the last unit.
				# NOTE: These looped divisions accumulate floating point rounding
				# errors, but each new division pushes the rounding errors further
				# and further down in the decimals, so it doesn't matter at all.
				num /= unit_step

		return HumanBytes.PRECISION_FORMATS[precision].format("-" if is_negative else "", num, unit)


def open_file_manager(path: str):
	if platform.system() == 'Linux':
		Gio.AppInfo.launch_default_for_uri('file:///' + path)


class GameItem(GObject.Object):
	__gtype_name__ = 'GameItem'
	
	def __init__(self, name, game):
		super().__init__()
		self.name = name
		self.game = game
