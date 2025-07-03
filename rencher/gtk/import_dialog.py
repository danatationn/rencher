import logging
import threading
import zipfile
from pathlib import Path

from gi.repository import Adw, Gio, Gtk, GLib, GObject
import rarfile

from rencher import tmp_path
from rencher.gtk._import import import_game
from rencher.gtk._library import update_library_sidebar
from rencher.renpy import Game, Mod


class GameItem(GObject.Object):
	__gtype_name__ = 'GameItem'
	
	name = GObject.Property(type=str)
	
	def __init__(self, name, game):
		super().__init__()
		self.name = name
		self.game = game

filename = tmp_path / 'rencher' / 'gtk' / 'ui' / 'import.ui'
@Gtk.Template(filename=str(filename))
class RencherImport(Adw.PreferencesDialog):
	__gtype_name__ = 'RencherImport'

	import_title: Adw.EntryRow = Gtk.Template.Child()
	import_location: Adw.EntryRow = Gtk.Template.Child()
	import_location_picker: Gtk.Button = Gtk.Template.Child()
	# import_type: Adw.ComboRow = Gtk.Template.Child()
	import_game_combo: Adw.ComboRow = Gtk.Template.Child()
	import_button: Adw.ActionRow = Gtk.Template.Child()
	import_progress_bar: Gtk.ProgressBar = Gtk.Template.Child()
	
	thread: threading.Thread = threading.Thread()
	progress: int = 0
	selected_type: str = 'Archive (.zip, .rar)'
	archive_location: str = ''
	folder_location: str = ''

	def __init__(self, window, *args, **kwargs):
		super().__init__(*args, **kwargs)

		self.window = window
		self.cancel_flag = threading.Event()

		list_store = Gio.ListStore.new(GameItem)
		
		for project in window.projects:
			if not isinstance(project, Mod):
				game_item = GameItem(name=project.name, game=project)
				list_store.append(game_item)
			
		self.import_game_combo.set_model(list_store)
		self.import_game_combo.set_expression(
			Gtk.PropertyExpression.new(GameItem, None, 'name')
		)
		
		string_list = Gtk.StringList()
		string_list.append('Archive (.zip, .rar)')
		string_list.append('Folder')
		# self.import_type.set_model(string_list)
		
		GLib.timeout_add(250, self.check_process)
		
	# @Gtk.Template.Callback()
	# def on_type_changed(self, combo_row: Adw.ComboRow, *args):
		# selected_item = self.import_type.get_selected_item()
		# self.selected_type = selected_item.get_string()
		# if self.selected_type == 'Folder':
		# 	self.import_location.set_title('Folder Location')
		# 	self.import_location_picker.set_icon_name('folder-open-symbolic')
		# 	self.import_location.set_text(self.folder_location)
		# else:
		# 	self.import_location.set_title('Archive Location')
		# 	self.import_location_picker.set_icon_name('file-cabinet-symbolic')
		# 	self.import_location.set_text(self.archive_location)
		
	@Gtk.Template.Callback()
	def on_location_changed(self, entry_row: Adw.EntryRow):
		location_text = entry_row.get_text()
		if self.selected_type == 'Folder':
			self.folder_location = location_text
		else:
			self.archive_location = location_text
			
		try:	
			if Path(location_text).suffix == '.zip':
				zipfile.ZipFile(location_text, 'r')
			if Path(location_text).suffix == '.rar':
				rarfile.RarFile(location_text, 'r')
		except (rarfile.BadRarFile, rarfile.NotRarFile, zipfile.BadZipFile, FileNotFoundError):
			self.import_button.set_sensitive(False)
		else:
			self.import_button.set_sensitive(True)
			if not self.import_title.get_text():
				if Path(location_text).is_file():
					name = Path(location_text).stem
				else:
					name = Path(location_text).name
				self.import_title.set_text(name)
				
	@Gtk.Template.Callback()
	def on_picker_clicked(self, button: Gtk.Button) -> None:
		dialog = Gtk.FileDialog()
		if self.selected_type == 'Folder':
			dialog.select_folder(self.window, None, self.on_file_selected)
		else:
			dialog.open(self.window, None, self.on_file_selected)

	def on_file_selected(self, dialog: Gtk.FileDialog, result):
		try:
			if self.selected_type == 'Folder':
				file = dialog.select_folder_finish(result)
			else:
				file = dialog.open_finish(result)
			self.import_location.set_text(file.get_path())
		except GLib.GError:
			pass  # dialog was dismissed by user

	@Gtk.Template.Callback()
	def on_import_clicked(self, button_row: Adw.ButtonRow) -> None:
		def import_thread():
			import_game(self)
			GLib.idle_add(lambda: (
				self.import_progress_bar.set_visible(False),
				update_library_sidebar(self.window),
				self.close(),
				
			))
		
		if self.import_button.get_style_context().has_class('destructive-action'):
			self.cancel_flag.set()
			self.thread.join()
			self.close()
		else:
			self.thread = threading.Thread(target=import_thread)
			self.thread.start()
		
	def check_process(self):
		if self.thread.is_alive():
			self.import_button.get_style_context().add_class('destructive-action')
			self.import_button.set_title('Cancel')
		else:
			self.import_button.get_style_context().remove_class('destructive-action')
			self.import_button.set_title('Import')
			
		return True