import threading
from pathlib import Path

import patoolib
from gi.repository import Adw, Gio, GObject, Gtk, GLib

from src import tmp_path
from src.gtk import GameItem
from src.gtk._import import import_game
from src.renpy import Mod

filename = tmp_path / 'src' / 'gtk' / 'ui' / 'import.ui'
@Gtk.Template(filename=str(filename))
class RencherImport(Adw.PreferencesDialog):
	__gtype_name__ = 'RencherImport'

	import_title: Adw.EntryRow = Gtk.Template.Child()
	import_location: Adw.EntryRow = Gtk.Template.Child()
	import_game_combo: Adw.ComboRow = Gtk.Template.Child()
	import_button: Adw.ActionRow = Gtk.Template.Child()
	import_progress_bar: Gtk.ProgressBar = Gtk.Template.Child()
	
	thread: threading.Thread = threading.Thread()
	progress: int = 0

	def __init__(self, window, *args, **kwargs):
		super().__init__(*args, **kwargs)
		
		string_list = Gio.ListStore.new(GameItem)
		
		for game in window.projects:
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
				
		if patoolib.is_archive(location_text) and location_text != '':
			self.import_button.set_sensitive(True)
			if not self.import_title.get_text():
				name = Path(location_text).stem
				self.import_title.set_text(name)
		else:
			self.import_button.set_sensitive(False)
				
	@Gtk.Template.Callback()
	def on_picker_clicked(self, button: Gtk.Button) -> None:
		dialog = Gtk.FileDialog()
		dialog.open(None, None, self.on_file_selected)

	@Gtk.Template.Callback()
	def on_combo_change(self, combo_row: Adw.ComboRow, _param: GObject.ParamSpec) -> None:
		# selected_game: GObject.Object | GameItem = self.import_game_combo.get_selected_item()
		...
		
	@Gtk.Template.Callback()
	def on_import_clicked(self, button_row: Adw.ButtonRow) -> None:
		def import_thread():
			try:
				import_game(self)
			except patoolib.util.PatoolError:
				dialog = Adw.AlertDialog(
					heading=f'Error importing {self.import_title.get_text()}',
					body='The archive supplied is not valid. Please re-download the file and try again.',
					close_response='okay'
				)
				dialog.add_response('okay', 'Okay')
				dialog.choose()
		
		self.thread = threading.Thread(target=import_thread)
		self.thread.start()

	
	def update_progress(self, i) -> bool:
		self.import_progress_bar.set_fraction(i)
	
	def on_file_selected(self, dialog: Gtk.FileDialog, result):
		try:
			file = dialog.open_finish(result)
			self.import_location.set_text(file.get_path())
		except GLib.GError:
			pass  # dialog was dismissed by user