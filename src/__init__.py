"""
	random functions that are not either ren'py or gtk related
"""

import platform

from gi.repository import GLib, Gio


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