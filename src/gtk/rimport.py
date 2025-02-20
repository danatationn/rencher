from gi.repository import Gtk, Adw


@Gtk.Template(filename='src/gtk/ui/import.ui')
class RencherImport(Adw.Dialog):
	__gtype_name__ = 'RencherImport'

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
