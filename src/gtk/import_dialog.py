import logging
import patoolib
from pathlib import Path

from src.renpy import Game, Mod

from gi.repository import Gtk, Adw, GObject, Gio


@Gtk.Template(filename='src/gtk/ui/import.ui')
class RencherImport(Adw.PreferencesDialog):
	__gtype_name__ = 'RencherImport'

	import_game_combo: Adw.ComboRow = Gtk.Template.Child()
	import_button: Adw.ActionRow = Gtk.Template.Child()

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
	def on_location_changed(self, entry_row: Adw.EntryRow):
		location_path = entry_row.get_text()
		if patoolib.is_archive(location_path) or Path(location_path).is_dir() and Path(location_path).exists():
			self.import_button.set_sensitive(True)
		else:
			self.import_button.set_sensitive(False)
		logging.debug(self.import_button.get_sensitive())
	
	@Gtk.Template.Callback()
	def on_picker_clicked(self, button: Gtk.Button) -> None:
		dialog = Gtk.FileDialog()
		dialog.open()

	@Gtk.Template.Callback()
	def on_combo_change(self, combo_row: Adw.ComboRow, _param: GObject.ParamSpec) -> None:
		selected_game: GObject.Object | GameItem = self.import_game_combo.get_selected_item()
		logging.debug(vars(selected_game.game))
		
	@Gtk.Template.Callback()
	def on_import_clicked(self, button_row: Adw.ButtonRow) -> None:
		pass


class GameItem(GObject.Object):
	__gtype_name__ = 'GameItem'
	
	name = GObject.Property(type=str)
	
	def __init__(self, name, game):
		super().__init__()
		self.name = name
		self.game = game