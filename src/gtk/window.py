import logging
import subprocess
import time

from gi.repository import Adw, Gtk, GLib

from src import tmp_path
from src.gtk import open_file_manager
from src.gtk._library import update_library_sidebar, update_library_view
from src.gtk.import_dialog import RencherImport
from src.gtk.settings_dialog import RencherSettings
from src.renpy import Game


filename = tmp_path / 'src' / 'gtk' / 'ui' / 'window.ui'
@Gtk.Template(filename=str(filename))
class RencherWindow(Adw.ApplicationWindow):
	__gtype_name__ = 'RencherWindow'

	""" variables """
	projects: list[Game] = []
	process: subprocess.Popen | None = None
	process_time: float | None = None

	""" classes """
	settings_dialog: Adw.PreferencesDialog = RencherSettings()
	import_dialog: Adw.PreferencesDialog = None  # lol

	""" templates """
	split_view: Adw.OverlaySplitView = Gtk.Template.Child()
	library_list_box: Gtk.ListBox = Gtk.Template.Child()
	selected_status_page: Adw.ViewStackPage = Gtk.Template.Child()
	library_view_stack: Adw.ViewStack = Gtk.Template.Child()

	last_played_row: Adw.ActionRow = Gtk.Template.Child()
	playtime_row: Adw.ActionRow = Gtk.Template.Child()
	size_row: Adw.ActionRow = Gtk.Template.Child()
	added_on_row: Adw.ActionRow = Gtk.Template.Child()
	rpath_row: Adw.ActionRow = Gtk.Template.Child()
	version_row: Adw.ActionRow = Gtk.Template.Child()
	codename_row: Adw.ActionRow = Gtk.Template.Child()

	play_split_button: Adw.SplitButton = Gtk.Template.Child()

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

		logging.debug('Window init')

		if '__compiled__' not in globals():
			self.get_style_context().add_class('devel')

		update_library_sidebar(self)
		self.import_dialog = RencherImport(self)

	@Gtk.Template.Callback()
	def on_import_clicked(self, _widget: Adw.ButtonRow) -> None:
		if not self.import_dialog.thread.is_alive():
			self.import_dialog = RencherImport(self)
				
		self.import_dialog.present(self)

	@Gtk.Template.Callback()
	def on_settings_clicked(self, _widget: Gtk.Button) -> None:
		self.settings_dialog.present(self)

	@Gtk.Template.Callback()
	def on_play_clicked(self, _widget: Gtk.Button) -> None:
		selected_button_row = self.library_list_box.get_selected_row()
		game = getattr(selected_button_row, 'game', None)
		
		if _widget.get_style_context().has_class('suggested-action'):
			self.toggle_play_button('stop')
			self.process = game.run()
			self.process_time = time.time()
			GLib.timeout_add_seconds(1, self.check_process)
		else:
			self.toggle_play_button('play')
			if self.process:
				self.process.terminate()

	@Gtk.Template.Callback()
	def on_dir_clicked(self, _widget: Gtk.Button) -> None:
		selected_button_row = self.library_list_box.get_selected_rows()[0]
		game = getattr(selected_button_row, 'game', None)
		if game:
			open_file_manager(str(game.rpath))

	@Gtk.Template.Callback()
	def on_game_selected(self, _widget: Gtk.ListBox, row: Gtk.ListBoxRow) -> None:
		game = getattr(row, 'game', None)
		if game:
			self.library_view_stack.set_visible_child_name('selected')

			update_library_view(self, game)


	def check_process(self) -> bool:
		if not self.process or self.process.poll() is not None:
			self.toggle_play_button('play')

			project = Game(apath=self.process.args[0].parents[2])
			playtime = float(project.config['info']['playtime'])
			if self.process_time:
				playtime += time.time() - self.process_time
			project.cleanup(playtime)
			self.process = None
			return False
		else:
			self.toggle_play_button('stop')
			return True


	def toggle_play_button(self, state: str) -> None:
		"""
		Args:
			state: accepts two values: 'play' and 'stop'
		"""

		if state == 'play':
			self.play_split_button.set_label('Play')
			self.play_split_button.get_style_context().remove_class('destructive-action')
			self.play_split_button.get_style_context().add_class('suggested-action')
		elif state == 'stop':
			self.play_split_button.set_label('Stop')
			self.play_split_button.get_style_context().remove_class('suggested-action')
			self.play_split_button.get_style_context().add_class('destructive-action')
