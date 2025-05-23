import logging
import subprocess
import time
from enum import Enum

from gi.repository import Adw, Gtk, GLib
from thefuzz.fuzz import partial_token_sort_ratio

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
	filter_text: str = ''
	combo_index: int = 0
	ascending_order: bool = False

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
	# size_row: Adw.ActionRow = Gtk.Template.Child()
	added_on_row: Adw.ActionRow = Gtk.Template.Child()

	# log_row: Adw.ExpanderRow = Gtk.Template.Child()
	rpath_row: Adw.ActionRow = Gtk.Template.Child()
	version_row: Adw.ActionRow = Gtk.Template.Child()
	codename_row: Adw.ActionRow = Gtk.Template.Child()

	play_button: Gtk.Button = Gtk.Template.Child()

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

		if '__compiled__' not in globals():
			self.get_style_context().add_class('devel')

		update_library_sidebar(self)
		self.import_dialog = RencherImport(self)
		self.library_list_box.set_sort_func(self.sort_func)
		self.library_list_box.set_filter_func(self.filter_func)

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
		project = getattr(selected_button_row, 'game', None)

		if _widget.get_style_context().has_class('suggested-action'):
			self.toggle_play_button('stop')
			self.process = project.run()
			self.process_time = time.time()
			GLib.timeout_add_seconds(1, self.check_process)
		else:
			self.toggle_play_button('play')
			if self.process:
				self.process.terminate()


	@Gtk.Template.Callback()
	def on_dir_clicked(self, _widget: Gtk.Button) -> None:
		selected_button_row = self.library_list_box.get_selected_rows()[0]
		project = getattr(selected_button_row, 'game', None)
		if project.apath:
			open_file_manager(str(project.apath))

	@Gtk.Template.Callback()
	def on_game_selected(self, _widget: Gtk.ListBox, row: Gtk.ListBoxRow) -> None:
		project = getattr(row, 'game', None)
		if project:
			self.library_view_stack.set_visible_child_name('selected')

			update_library_view(self, project)
			
	@Gtk.Template.Callback()
	def on_search_changed(self, _widget: Gtk.SearchEntry):
		self.filter_text = _widget.get_text()
		self.library_list_box.invalidate_filter()

	@Gtk.Template.Callback()
	def on_combo_changed(self, _widget: Gtk.DropDown, _):
		self.combo_index = _widget.get_selected()
		self.library_list_box.invalidate_sort()
		
	@Gtk.Template.Callback()
	def on_order_changed(self, _widget: Gtk.ToggleButton):
		self.ascending_order = _widget.get_active()
		self.library_list_box.invalidate_sort()
			
	@Gtk.Template.Callback()
	def on_options_clicked(self, _widget: Gtk.Button):
		selected_button_row = self.library_list_box.get_selected_row()
		project = getattr(selected_button_row, 'game', None)
		
		project.config['info']['codename'] = ''
		project.config.write_config()
	
			
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
			self.play_button.set_label('Play')
			self.play_button.get_style_context().remove_class('destructive-action')
			self.play_button.get_style_context().add_class('suggested-action')
		elif state == 'stop':
			self.play_button.set_label('Stop')
			self.play_button.get_style_context().remove_class('suggested-action')
			self.play_button.get_style_context().add_class('destructive-action')

	def filter_func(self, widget: Gtk.ListBoxRow) -> bool:
		if not self.filter_text:
			return True
		
		fuzz = partial_token_sort_ratio(widget.game.name, self.filter_text)
		if fuzz > 90:
			return True
		return False
		
	def sort_func(self, one: Adw.ActionRow, two: Adw.ActionRow) -> int:
		if self.combo_index == 0:
			# b > a so we invert these
			game_one = two.game.name.lower() 
			game_two = one.game.name.lower()
		elif self.combo_index == 1:
			game_one = one.game.config['info'].get('last_played', 0)
			game_two = two.game.config['info'].get('last_played', 0)
		elif self.combo_index == 2:
			game_one = float(one.game.config['info'].get('playtime', 0))
			game_two = float(two.game.config['info'].get('playtime', 0))
		else:
			game_one = one.game.config['info'].get('added_on', 0)
			game_two = two.game.config['info'].get('added_on', 0)
		# else:
		# 	game_one = one.game.config['info'].get('size', 0)
		# 	game_two = two.game.config['info'].get('size', 0)
			
		if game_one < game_two:
			res = 1
		elif game_one > game_two:
			res = -1
		else:
			res = 0
			
		if self.ascending_order:
			return -res
		else:
			return res