import sys
import logging

from gi.repository import Gtk, Adw

from src.gtk import open_file_manager
from src.gtk.settings_dialog import RencherSettings
from src.gtk.import_dialog import RencherImport
from src.gtk._library import update_library_view
from src.renpy import Game, Mod


@Gtk.Template(filename='src/gtk/ui/window.ui')
class RencherWindow(Adw.ApplicationWindow):
	__gtype_name__ = 'RencherWindow'

	""" variables """
	projects: list[Game] = []

	""" classes """
	settings_dialog: Adw.PreferencesDialog = RencherSettings()
	# import_dialog: Adw.Dialog = RencherImport(projects)

	""" templates """
	split_view: Adw.OverlaySplitView = Gtk.Template.Child()
	library_list_box: Gtk.ListBox = Gtk.Template.Child()

	library_view_stack: Adw.ViewStack = Gtk.Template.Child()
	# selected_status_page: Adw.ViewStackPage = Gtk.Template.Child()

	# last_played_row: Adw.ActionRow = Gtk.Template.Child()
	# playtime_row: Adw.ActionRow = Gtk.Template.Child()
	# size_row: Adw.ActionRow = Gtk.Template.Child()
	# added_on_row: Adw.ActionRow = Gtk.Template.Child()
	# rpath_row: Adw.ActionRow = Gtk.Template.Child()
	# version_row: Adw.ActionRow = Gtk.Template.Child()
	# codename_row: Adw.ActionRow = Gtk.Template.Child()

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

		if getattr(sys, 'frozen', True):
			self.get_style_context().add_class('devel')

		update_library_view(self)
		
		logging.debug('window init')


	@Gtk.Template.Callback()
	def on_import_clicked(self, _widget: Gtk.Button) -> None:
		dialog = RencherImport(self.projects)
		dialog.present(self)
		# self.import_dialog.present(self)


	@Gtk.Template.Callback()
	def on_settings_clicked(self, _widget: Gtk.Button) -> None:
		self.settings_dialog.present(self)


	@Gtk.Template.Callback()
	def on_play_clicked(self, _widget: Gtk.Button) -> None:
		selected_button_row = self.library_list_box.get_selected_rows()[0]
		game = getattr(selected_button_row, 'game', None)
		if game:
			game.run()


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
