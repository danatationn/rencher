import logging
import pprint

from src.renpy import Game, Mod

from gi.repository import Gtk, Adw, GObject, Gio


@Gtk.Template(filename='src/gtk/ui/import.ui')
class RencherImport(Adw.PreferencesDialog):
	__gtype_name__ = 'RencherImport'

	import_game_combo: Adw.ComboRow = Gtk.Template.Child()

	def __init__(self, projects: list[Game], *args, **kwargs):
		super().__init__(*args, **kwargs)
		
		string_list = Gio.ListStore.new(GameItem)
		
		for game in projects:
			if not isinstance(game, Mod):
				game_item = GameItem(name=game.name, game=game)
				string_list.append(game_item)
			
		self.import_game_combo.set_model(string_list)
		self.import_game_combo.set_expression(
			Gtk.PropertyExpression.new(GameItem, None, 'name')
		)
		
	@Gtk.Template.Callback()
	def on_picker_clicked(self, button: Gtk.Button) -> None:
		dialog = Gtk.FileDialog()
		dialog.open()

	@Gtk.Template.Callback()
	def on_combo_change(self, combo_row: Adw.ComboRow, _param: GObject.ParamSpec) -> None:
		selected_game: GObject.Object | GameItem = self.import_game_combo.get_selected_item()
		logging.debug(vars(selected_game.game))


class GameItem(GObject.Object):
	__gtype_name__ = 'GameItem'
	
	name = GObject.Property(type=str)
	
	def __init__(self, name, game):
		super().__init__()
		self.name = name
		self.game = game