import logging
from pathlib import Path

from gi.repository import Gtk, Adw

from src import open_file_manager
from src.gtk.settings import RencherSettings
from src.renpy import Game, Mod


@Gtk.Template(filename='src/gtk/ui/window.ui')
class RencherWindow(Adw.ApplicationWindow):
	__gtype_name__ = 'RencherWindow'

	settings_dialog = RencherSettings()

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

		self.update_library_view()
		
		logging.debug('window init')


	def update_library_view(self) -> None:
		games_path = Path.cwd() / 'games'
		mods_path = Path.cwd() / 'mods'
		games = [Game(rpath=path) for path in games_path.glob('*') if path.is_dir()]
		mods = [Mod(rpath=path) for path in mods_path.glob('*') if path.is_dir()]
		games += mods

		for game in games:
			button = Adw.ButtonRow(title=game.name)
			button.game = game
			button.connect('activated', self.on_game_activated)
			self.library_list_box.append(button)

		if not games:  # ps5 view
			self.library_view_stack.set_visible_child_name('empty')
			self.split_view.set_show_sidebar(False)


	@Gtk.Template.Callback()
	def on_import_clicked(self, _widget: Gtk.Button) -> None:
		print('not implemented!')


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
