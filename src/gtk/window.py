from gi.repository import Gtk, GLib, Adw


@Gtk.Template(filename='src/gtk/ui/window.ui')
class RencherWindow(Gtk.ApplicationWindow):
	__gtype_name__ = 'RencherWindow'

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

		headerbar = Gtk.HeaderBar()
		self.set_titlebar(titlebar=headerbar)
		button = Gtk.Button(label='hi')
		headerbar.pack_end(button)