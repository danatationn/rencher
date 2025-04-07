import logging
import time
from itertools import chain
from pathlib import Path
import os

from gi.repository import Adw, GLib

from src import root_path
from src.renpy import Game, Mod
from src.gtk import format_gdatetime, HumanBytes


def return_projects() -> list[Game]:
	s = time.perf_counter()

	games_path = root_path / 'games'
	mods_path = root_path / 'mods'

	projects: list[Game] = []
	for path in chain(games_path.glob('*'), mods_path.glob('*')):
		try:
			if path.parent == games_path:
				projects.append(Game(rpath=path))
			else:
				projects.append(Mod(rpath=path))
		except FileNotFoundError:
			pass

	runtime = time.perf_counter() - s
	logging.debug(f'{round(runtime, 3)}s')
	return projects

def update_library_sidebar(self) -> None:
	projects = return_projects()
	
	added_projects = set(projects) - set(self.projects)
	removed_projects = set(self.projects) - set(projects)
	changed_projects = set()

	for project in projects:
		if project in self.projects:
			for old_project in self.projects:
				if project == old_project and project.config != old_project.config:
					changed_projects.add(project)
					break

	if True:  # 😁😁
		logging.debug(f'added_projects: {added_projects}')
		logging.debug(f'removed_projects: {removed_projects}')
		logging.debug(f'changed_projects: {changed_projects}')

	buttons: list[Adw.ButtonRow] = []
	for i, project in enumerate(self.projects):
		button = self.library_list_box.get_row_at_index(i)
		buttons.append(button)

	for project in self.projects:
		if project in removed_projects:
			for button in buttons:
				if project == button.game:
					buttons.remove(button)
					self.library_list_box.remove(button)
					break
			continue

	for project in projects:
		if project in added_projects:
			button = Adw.ButtonRow(title=project.name)
			button.game = project
			buttons.append(button)
			self.library_list_box.append(button)
			continue

		if project in changed_projects:
			for button in buttons:
				if button.game == project:
					button.game = project
					button.name = project.name
					if self.library_list_box.get_selected_row().game == project:
						update_library_view(self, project)
					break
			continue

	if not projects:  # ps5 view
		self.library_view_stack.set_visible_child_name('empty')
		self.split_view.set_show_sidebar(False)
	else:
		if not self.library_list_box.get_selected_row():
			self.library_view_stack.set_visible_child_name('game-select')
		self.split_view.set_show_sidebar(True)
	
	self.projects = projects


def update_library_view(self, project: Game) -> None:
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