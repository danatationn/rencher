from gi.repository import Gtk, Adw

from .settings import RencherPreferences


@Gtk.Template(filename='src/gtk/ui/window.ui')
class RencherWindow(Adw.ApplicationWindow):
	__gtype_name__ = 'RencherWindow'

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.preferences_dialog = RencherPreferences()

	@Gtk.Template.Callback()
	def on_import_clicked(self, _widget: Gtk.Widget):
		print('not implemented!')

	@Gtk.Template.Callback()
	def on_settings_clicked(self, _widget: Gtk.Widget) -> None:
		self.preferences_dialog.present(self)