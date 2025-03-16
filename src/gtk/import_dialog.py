import logging
import patoolib
from pathlib import Path

from src.renpy import Game, Mod
from src.gtk._import import import_game

from gi.repository import Gtk, Adw, GObject, Gio


@Gtk.Template(filename='src/gtk/ui/import.ui')
class RencherImport(Adw.PreferencesDialog):
	__gtype_name__ = 'RencherImport'

	import_title: Adw.EntryRow = Gtk.Template.Child()
	import_location: Adw.EntryRow = Gtk.Template.Child()
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
		location_text = entry_row.get_text()
		location_path = Path(location_text)
				
		if location_path.exists() and location_text != '':
			self.import_button.set_sensitive(True)
			if not self.import_title.get_text():
				self.import_title.set_text(location_path.stem)
		else:
			self.import_button.set_sensitive(False)
				
	@Gtk.Template.Callback()
	def on_picker_clicked(self, button: Gtk.Button) -> None:
		dialog = Gtk.FileDialog()
		dialog.open(None, None, self.on_file_selected)
		
	@Gtk.Template.Callback()
	def on_combo_change(self, combo_row: Adw.ComboRow, _param: GObject.ParamSpec) -> None:
		selected_game: GObject.Object | GameItem = self.import_game_combo.get_selected_item()
		logging.debug(vars(selected_game.game))
		
	@Gtk.Template.Callback()
	def on_import_clicked(self, button_row: Adw.ButtonRow) -> None:
		title_text = self.import_title.get_text()
		location_text = self.import_location.get_text()
		is_mod = self.import_game_combo.get_sensitive()
		
		import_game(title_text, Path(location_text), is_mod)
	
	def on_file_selected(self, dialog: Gtk.FileDialog, result):
		file = dialog.open_finish(result)
		self.import_location.set_text(file.get_path())


class GameItem(GObject.Object):
	__gtype_name__ = 'GameItem'
	
	name = GObject.Property(type=str)
	
	def __init__(self, name, game):
		super().__init__()
		self.name = name
		self.game = game