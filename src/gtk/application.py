import logging
import platform
from pathlib import Path
from configparser import ConfigParser 

import gi
from watchdog.events import DirModifiedEvent, FileModifiedEvent, FileSystemEventHandler
from watchdog.observers import Observer

from src import local_path
from src.renpy.config import create_config

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Adw, Gtk  # noqa: E402

Adw.init()

from src.gtk.window import RencherWindow  # noqa: E402
from src.gtk._library import update_library_sidebar, update_library_view  # noqa: E402


class RencherApplication(Gtk.Application):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs, application_id='com.github.danatationn.rencher')
		self.config: dict | None = None
		self.window: RencherWindow | None = None
		logging.basicConfig(format='(%(relativeCreated)d) %(levelname)s: %(msg)s', level=logging.NOTSET)

		patool_logger = logging.getLogger('patool')
		patool_logger.propagate = False
		watchdog_logger = logging.getLogger('watchdog')
		watchdog_logger.propagate = False

	def do_startup(self):
		Gtk.Application.do_startup(self)

	def do_activate(self):
		Gtk.Application.do_activate(self)

		if platform.system() == 'Linux':
			config_path = Path.home() / '.config' / 'rencher.ini'
		else:
			config_path = Path.home() / 'AppData' / 'Local' / 'Rencher' / 'config.ini'

		if not config_path.exists():
			create_config()

		with open(config_path, 'r') as f:
			self.config = ConfigParser()
			self.config.read(f)

		self.window = RencherWindow(application=self)
		self.window.present()

		observer = Observer()
		handler = RencherFSHandler(self)
		local_path.mkdir(exist_ok=True)
		observer.schedule(handler, local_path, recursive=True)
		observer.start()

	# def do_shutdown(self):
	# 	Gtk.Application.do_activate(self)

class RencherFSHandler(FileSystemEventHandler):
	def __init__(self, app):
		super().__init__()
		self.app = app
		self.mtimes: list[int] = []  # for debouncing :)
	
	def on_modified(self, event: DirModifiedEvent | FileModifiedEvent) -> None:
		if self.app.window.process:
			return
		if self.app.window.import_dialog.thread.is_alive():
			return

		src_path = Path(event.src_path)
		games_path = local_path / 'games'
		mods_path = local_path / 'mods'

		if not src_path.is_relative_to(games_path) and not src_path.is_relative_to(mods_path):
			return

		try:
			mtime = int(src_path.stat().st_mtime)
		except FileNotFoundError:
			# something got deleted 🤷‍
			if src_path.parent == games_path:
				update_library_sidebar(self.app.window)
			mtime = 0

		if mtime in self.mtimes:
			return
		else:
			self.mtimes.append(mtime)
			update_library_sidebar(self.app.window)
			row = self.app.window.library_list_box.get_selected_row()
			if row:
				update_library_view(self.app.window, row.game)

		if src_path.is_relative_to(games_path) or src_path.is_relative_to(mods_path):
			pass