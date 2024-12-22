import platform

from gi.repository import Gtk, Adw, Gio

from src.gtk.settings import RencherSettings
from src.renpy import return_games, Game
from src.gtk import GameInfo


@Gtk.Template(filename='src/gtk/ui/window.ui')
class RencherWindow(Adw.ApplicationWindow):
	__gtype_name__ = 'RencherWindow'

	split_view: Adw.OverlaySplitView = Gtk.Template.Child()
	library_list_box: Gtk.ListBox = Gtk.Template.Child()

	library_view_stack: Adw.ViewStack = Gtk.Template.Child()
	selected_status_page: Adw.ViewStackPage = Gtk.Template.Child()

	settings_dialog = RencherSettings()
	game_info = GameInfo()

	last_played_row: Adw.ActionRow = Gtk.Template.Child()
	playtime_row: Adw.ActionRow = Gtk.Template.Child()
	size_row: Adw.ActionRow = Gtk.Template.Child()
	rpath_row: Adw.ActionRow = Gtk.Template.Child()
	version_row: Adw.ActionRow = Gtk.Template.Child()
	codename_row: Adw.ActionRow = Gtk.Template.Child()

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

		games = return_games()

		for game in games:
			button = Adw.ButtonRow(title=game.name)
			button.game = game
			button.connect('activated', self.on_game_activated)

			self.library_list_box.append(button)

		selected_view_content = self.selected_status_page
		print(selected_view_content)
		self.game_info.bind_property('name', selected_view_content, 'title')
		self.game_info.bind_property('version', self.version_row, 'subtitle')
		self.game_info.bind_property('rpath', self.rpath_row, 'subtitle')
		self.game_info.bind_property('codename', self.codename_row, 'subtitle')

		if not games:
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
			Gio.AppInfo.launch_default_for_uri('file:///' + str(game.rpath))


	def on_game_activated(self, _widget: Adw.ButtonRow) -> None:
		game = getattr(_widget, 'game', None)
		if game:
			self.game_info.change_game(game)
			self.library_view_stack.set_visible_child_name('selected')
