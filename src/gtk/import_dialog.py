import threading
import zipfile
from pathlib import Path

from gi.repository import Adw, Gio, GObject, Gtk, GLib
import rarfile

from src import tmp_path
from src.gtk import GameItem
from src.gtk._import import import_game
from src.gtk._library import update_library_sidebar
from src.renpy import Game, Mod


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

		self.window = window

		string_list = Gio.ListStore.new(GameItem)
		
		for project in window.projects:
			if not isinstance(project, Mod):
				game_item = GameItem(name=project.name, game=project)
				string_list.append(game_item)
			
		self.import_game_combo.set_model(string_list)
		self.import_game_combo.set_expression(
			Gtk.PropertyExpression.new(GameItem, None, 'name')
		)

	@Gtk.Template.Callback()
	def on_location_changed(self, entry_row: Adw.EntryRow):
		location_text = entry_row.get_text()
			
		try:	
			if Path(location_text).suffix == '.zip':
				zipfile.ZipFile(location_text, 'r')
			if Path(location_text).suffix == '.rar':
				rarfile.RarFile(location_text, 'r')
		except (rarfile.BadRarFile, rarfile.NotRarFile, zipfile.BadZipFile):
			self.import_button.set_sensitive(False)
		else:
			self.import_button.set_sensitive(True)
			if not self.import_title.get_text():
				name = Path(location_text).stem
				self.import_title.set_text(name)
				
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
			import_game(self)
			GLib.idle_add(lambda: (
				update_library_sidebar(self.window),
				self.close()
			))
		
		self.thread = threading.Thread(target=import_thread)
		self.thread.start()

	
	def update_progress(self, i) -> None:
		self.import_progress_bar.set_fraction(i)
	
	def on_file_selected(self, dialog: Gtk.FileDialog, result):
		try:
			file = dialog.open_finish(result)
			self.import_location.set_text(file.get_path())
		except GLib.GError:
			pass  # dialog was dismissed by user