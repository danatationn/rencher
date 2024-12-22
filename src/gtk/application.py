import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw
Adw.init()

from src.gtk.window import RencherWindow


class RencherApplication(Gtk.Application):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs, application_id='com.github.danatationn.rencher')
		self.window: RencherWindow | None = None  # type hinting :)

	def do_startup(self):
		Gtk.Application.do_startup(self)

	def do_activate(self):
		Gtk.Application.do_activate(self)
		self.window = RencherWindow(application=self)
		self.window.present()
