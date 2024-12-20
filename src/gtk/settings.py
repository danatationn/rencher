from gi.repository import Gtk, Adw


@Gtk.Template(filename='src/gtk/ui/preferences.ui')
class RencherPreferences(Adw.PreferencesDialog):
	__gtype_name__ = 'RencherPreferences'

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
