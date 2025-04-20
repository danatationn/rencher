import logging
import time
from itertools import chain
from pathlib import Path

from gi.repository import Adw, GLib

from src import root_path
from src.renpy import Game
from src.renpy.paths import find_absolute_path
from src.gtk import format_gdatetime, HumanBytes


def return_paths(self) -> list[Path]:
	s = time.perf_counter()

	games_path = root_path / 'games'
	mods_path = root_path / 'mods'

	paths: list[Path] = []
	for path in chain(games_path.glob('*'), mods_path.glob('*')):
		if find_absolute_path(path) is not None:
			paths.append(path)

	runtime = time.perf_counter() - s
	logging.debug(f'{round(runtime, 3)}s')
	return paths

def update_library_sidebar(self) -> None:
	paths = return_paths(self)
	
	added_paths = set(paths) - set(self.paths)
	removed_paths = set(self.paths) - set(paths)

	if True:  # 😁😁
		logging.debug(f'added_paths: {added_paths}')
		logging.debug(f'removed_paths: {removed_paths}')

	buttons = {}
	for i, path in enumerate(self.paths):
		button = self.library_list_box.get_row_at_index(i)
		buttons[i] = button

	for button in buttons.values():
		if button.path in removed_paths:
			self.library_list_box.remove(button)

	for path in added_paths:
		button = Adw.ButtonRow(title=path.name)
		button.path = path
		self.library_list_box.append(button)
		continue

	if not paths:  # ps5 view
		self.library_view_stack.set_visible_child_name('empty')
		self.split_view.set_show_sidebar(False)
	else:
		if not self.library_list_box.get_selected_row():
			self.library_view_stack.set_visible_child_name('game-select')
		self.split_view.set_show_sidebar(True)
	
	self.paths = paths


def update_library_view(self, path: Path) -> None:
	project = Game(path)
	self.selected_status_page.set_title(project.name)

	try:
		size = project.config['info']['size']
		formatted_size = HumanBytes.format(int(size), metric=True)
		self.size_row.set_subtitle(formatted_size)
	except KeyError:
		self.size_row.set_subtitle('N/A')

	try:
		last_played = int(float(project.config['info']['last_played']))
		datetime = GLib.DateTime.new_from_unix_utc(last_played)
		formatted_last_played = format_gdatetime(datetime, 'neat')
		self.last_played_row.set_subtitle(formatted_last_played)
	except KeyError:
		self.last_played_row.set_subtitle('N/A')
	except ValueError:
		self.last_played_row.set_subtitle('Never')

	try:
		playtime = int(float(project.config['info']['playtime']))
		datetime = GLib.DateTime.new_from_unix_utc(playtime)
		formatted_playtime = format_gdatetime(datetime, 'runtime')

		self.playtime_row.set_subtitle(formatted_playtime)
	except KeyError:
		self.playtime_row.set_subtitle('N/A')
	except ValueError:
		self.playtime_row.set_subtitle('N/A')

	try:
		added_on = int(project.config['info']['added_on'])
		datetime = GLib.DateTime.new_from_unix_utc(added_on)
		formatted_datetime = format_gdatetime(datetime, 'neat')
		self.added_on_row.set_subtitle(formatted_datetime)
	except KeyError:
		self.added_on_row.set_subtitle('N/A')

	self.version_row.set_subtitle(project.version if project.version else 'N/A')
	self.rpath_row.set_subtitle(str(project.rpath))
	self.codename_row.set_subtitle(project.codename)