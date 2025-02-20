from src.renpy import Game, Mod

from gi.repository import Gtk, Adw





@Gtk.Template(filename='src/gtk/ui/import.ui')
class RencherImport(Adw.PreferencesDialog):
	__gtype_name__ = 'RencherImport'

	import_game_combo: Adw.ComboRow = Gtk.Template.Child()

	def __init__(self, projects: list[Game], *args, **kwargs):
		super().__init__(*args, **kwargs)
		
		string_list = Gtk.MapListModel()
		
		for game in projects:
			if not isinstance(game, Mod):
				string_list.append(game)
			
		self.import_game_combo.set_model(string_list)
		

	@Gtk.Template.Callback()
	def on_picker_clicked(self, _widget: Gtk.Widget) -> None:
		dialog = Gtk.FileDialog()
		dialog.open()
