import sys
import logging
import subprocess

from gi.repository import Gtk, Adw, GLib

from src.gtk import open_file_manager
from src.gtk.settings_dialog import RencherSettings
from src.gtk.import_dialog import RencherImport
from src.gtk._library import update_library_sidebar, update_library_view
from src.renpy import Game, Mod


@Gtk.Template(filename='src/gtk/ui/window.ui')
class RencherWindow(Adw.ApplicationWindow):
	__gtype_name__ = 'RencherWindow'

	""" variables """
	projects: list[Game] = []
	process: subprocess.Popen | None = None

	""" classes """
	settings_dialog: Adw.PreferencesDialog = RencherSettings()
	import_dialog: Adw.PreferencesDialog = None  # lol

	""" templates """
	last_played_row: Adw.ActionRow = Gtk.Template.Child()
	playtime_row: Adw.ActionRow = Gtk.Template.Child()
	size_row: Adw.ActionRow = Gtk.Template.Child()
	added_on_row: Adw.ActionRow = Gtk.Template.Child()
	rpath_row: Adw.ActionRow = Gtk.Template.Child()
	version_row: Adw.ActionRow = Gtk.Template.Child()
	codename_row: Adw.ActionRow = Gtk.Template.Child()
	
	split_view: Adw.OverlaySplitView = Gtk.Template.Child()
	library_list_box: Gtk.ListBox = Gtk.Template.Child()
	selected_status_page: Adw.ViewStackPage = Gtk.Template.Child()
	library_view_stack: Adw.ViewStack = Gtk.Template.Child()


	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

		if getattr(sys, 'frozen', True):
			self.get_style_context().add_class('devel')

		update_library_sidebar(self)
		logging.debug('window init')
		self.import_dialog = RencherImport(self)


	@Gtk.Template.Callback()
	def on_import_clicked(self, _widget: Gtk.Button) -> None:
		if not self.import_dialog.thread.is_alive():
			self.import_dialog = RencherImport(self)
				
		self.import_dialog.present(self)

	@Gtk.Template.Callback()
	def on_settings_clicked(self, _widget: Gtk.Button) -> None:
		self.settings_dialog.present(self)


	@Gtk.Template.Callback()
	def on_play_clicked(self, _widget: Gtk.Button) -> None:
		selected_button_row = self.library_list_box.get_selected_rows()[0]
		game = getattr(selected_button_row, 'game', None)
		
		if _widget.get_style_context().has_class('suggested-action'):
			_widget.set_label('Stop')
			_widget.get_style_context().remove_class('suggested-action')
			_widget.get_style_context().add_class('destructive-action')
			self.process = game.run()
		else:
			_widget.set_label('Play')
			_widget.get_style_context().remove_class('destructive-action')
			_widget.get_style_context().add_class('suggested-action')
			if self.process:
				self.process.terminate()
			self.process = None
			
		
	@Gtk.Template.Callback()
	def on_dir_clicked(self, _widget: Gtk.Button) -> None:
		selected_button_row = self.library_list_box.get_selected_rows()[0]
		game = getattr(selected_button_row, 'game', None)
		if game:
			open_file_manager(str(game.rpath))


	def on_game_activated(self, _widget: Adw.ButtonRow) -> None:
		game = getattr(_widget, 'game', None)
		if game:
			self.library_view_stack.set_visible_child_name('selected')

			update_library_view(self, game)			
			
