import logging
from pathlib import Path

import gi
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, DirModifiedEvent, FileModifiedEvent

from src import root_path
from src.renpy import Game, Mod

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw  # noqa: E402
Adw.init()

from src.gtk.window import RencherWindow  # noqa: E402


class RencherApplication(Gtk.Application):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs, application_id='com.github.danatationn.rencher')
		self.window: RencherWindow | None = None  # type hinting :)
		logging.basicConfig(format='(%(relativeCreated)d) %(levelname)s: %(msg)s', level=logging.NOTSET)
		logging.debug('app init')
		
		patool_logger = logging.getLogger('patool')
		patool_logger.propagate = False
		watchdog_logger = logging.getLogger('watchdog')
		watchdog_logger.propagate = False


	def do_startup(self):
		Gtk.Application.do_startup(self)


	def do_activate(self):
		Gtk.Application.do_activate(self)

		self.window = RencherWindow(application=self)
		self.window.present()
		logging.debug('app activate')
		
		observer = Observer()
		handler = RencherFSHandler(self)
		observer.schedule(handler, root_path, recursive=True)
		observer.start()


class RencherFSHandler(FileSystemEventHandler):
	def __init__(self, app):
		super().__init__()
		self.app = app
	
	def on_modified(self, event: DirModifiedEvent | FileModifiedEvent) -> None:
		if self.app.window.process:
			return
		
		for project in self.app.window.projects:
			event_path = Path(event.src_path)
			
			if event_path.is_relative_to(project.rpath):
				logging.debug(f'something changed in {project.name} ({project.codename})!')
				
				if isinstance(project, Mod):
					new_project = Mod(rpath=project.rpath)
				else:
					new_project = Game(rpath=project.rpath)

				project.__dict__.update(new_project.__dict__)