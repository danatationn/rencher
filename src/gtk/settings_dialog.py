from gi.repository import Gtk, Adw

from src import tmp_path


filename = tmp_path / 'src' / 'gtk' / 'ui' / 'settings.ui'
@Gtk.Template(filename=str(filename))
class RencherSettings(Adw.PreferencesDialog):
	__gtype_name__ = 'RencherSettings'

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
