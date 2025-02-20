from gi.repository import Gtk, Adw


@Gtk.Template(filename='src/gtk/ui/settings.ui')
class RencherSettings(Adw.PreferencesDialog):
	__gtype_name__ = 'RencherSettings'

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
