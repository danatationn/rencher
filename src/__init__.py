"""
	random functions that are not either ren'py or gtk related
"""

import logging

from pathlib import Path

from watchdog.events import FileSystemEvent, FileSystemEventHandler, DirModifiedEvent, FileModifiedEvent
from watchdog.observers import Observer
from gi.repository import GLib


class GameEventHandler(FileSystemEventHandler):
	def on_modified(self, event: DirModifiedEvent | FileModifiedEvent) -> None:
		logging.info('game was modified ..')


class GameUpdater:
	game_path = Path.cwd() / 'games'
	mod_path = Path.cwd() / 'mods'
	event_handler = GameEventHandler()
	observer = Observer()

	def __init__(self):
		self.observer.schedule(self.event_handler, )


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
