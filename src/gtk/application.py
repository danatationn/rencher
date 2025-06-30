import logging
import threading
import tomllib

import requests
from pathlib import Path

import gi
from watchdog.events import DirModifiedEvent, FileModifiedEvent, FileSystemEventHandler
from watchdog.observers import Observer

from src import local_path, config_path, tmp_path
from src.renpy.config import RencherConfig

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Adw, Gtk, GLib, Gdk  # noqa: E402

Adw.init()

from src.gtk.window import RencherWindow  # noqa: E402
from src.gtk._library import update_library_sidebar, update_library_view  # noqa: E402


class RencherApplication(Gtk.Application):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs, application_id='com.github.danatationn.rencher')
		self.config: dict | None = None
		self.window: RencherWindow | None = None
		logging.basicConfig(format='(%(relativeCreated)d) %(levelname)s: %(msg)s', level=logging.NOTSET)

		watchdog_logger = logging.getLogger('watchdog')
		watchdog_logger.propagate = False
		urllib3_logger = logging.getLogger('urllib3')
		urllib3_logger.setLevel(logging.WARNING)

	def do_startup(self):
		Gtk.Application.do_startup(self)

	def do_activate(self):
		Gtk.Application.do_activate(self)

		self.config = RencherConfig()
		self.window = RencherWindow(application=self)
		self.window.present()

		observer = Observer()
		handler = RencherFSHandler(self)
		local_path.mkdir(exist_ok=True)
		observer.schedule(handler, local_path, recursive=True)
		observer.start()

		version_thread = threading.Thread(target=self.check_version)
		version_thread.run()
		
	def check_version(self):
		# if '__compiled__' not in globals():
		# 	return
		if self.config['settings']['surpress_updates'] == 'true':
			return
		
		try:
			response = requests.get('https://api.github.com/repos/danatationn/rencher/releases/latest')
		except requests.exceptions.ConnectionError:
			return
		else:
			if response.status_code == 404:
				return
			version = response.json()['tag_name'].replace('v', '')

			with open(tmp_path / 'pyproject.toml', 'r') as f:
				project = tomllib.loads(f.read())
			
			if version > project['project']['version']:
				if 'assets' in response.json() and len(response.json()['assets']) > 0:
					download_url = response.json()['html_url']
				else:
					return
				
				logging.info(f'A new update is available! (v{version})')
				logging.info(download_url)
				toast = Adw.Toast(
					title=f'A new update is available! (v{version})',
					timeout=5,
					button_label='Download'
				)
				toast.connect('button-clicked', lambda *_: (
					Gtk.show_uri(self.window, download_url, Gdk.CURRENT_TIME)
				))
				
				self.window.toast_overlay.add_toast(toast)
			else:
				logging.info(f'You\'re up to date! (v{project['project']['version']})')

	# def do_shutdown(self):
	# 	Gtk.Application.do_activate(self)
		
		
class RencherFSHandler(FileSystemEventHandler):
	
	app: Adw.ApplicationWindow = None
	mtimes: list[int] = []  # for debouncing :)
	config: RencherConfig = RencherConfig()
	
	def __init__(self, app):
		super().__init__()
		self.app = app
		self.mtimes: list[int] = []
	
	def on_modified(self, event: DirModifiedEvent | FileModifiedEvent) -> None:
		if self.app.window.process:
			return
		if self.app.window.import_dialog.thread.is_alive():
			return
		if self.app.window.pause_fs:
			return

		src_path = Path(event.src_path)
		if src_path == config_path:
			self.config.read()

		data_dir = self.config.get_data_dir()
		games_path = data_dir / 'games'
		mods_path = data_dir / 'mods'

		if not src_path.is_relative_to(games_path) and not src_path.is_relative_to(mods_path):
			return
		
		try:
			mtime = int(src_path.stat().st_mtime)
		except FileNotFoundError:
			# something got deleted 🤷‍
			if src_path.parent.is_relative_to(games_path) or src_path.parent.is_relative_to(mods_path):
				GLib.idle_add(update_library_sidebar, self.app.window)
			mtime = 0

		# if src_path.name == 'rencher.ini':
		# 	GLib.idle_add(update_library_sidebar, self.app.window)			
		if mtime in self.mtimes:
			return
		else:
			self.mtimes.append(mtime)
			GLib.idle_add(update_library_sidebar, self.app.window)
			row = self.app.window.library_list_box.get_selected_row()
			if row:
				GLib.idle_add(update_library_view, self.app.window, row.game)

		# if src_path.is_relative_to(games_path) or src_path.is_relative_to(mods_path):
		# 	pass