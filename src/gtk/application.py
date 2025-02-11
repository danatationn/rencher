import logging

import gi

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


	def do_startup(self):
		Gtk.Application.do_startup(self)


	def do_activate(self):
		Gtk.Application.do_activate(self)

		self.window = RencherWindow(application=self)
		self.window.present()
		logging.debug('app activate')
