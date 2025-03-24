import logging
from itertools import chain

from gi.repository import Adw, GLib

from src import root_path
from src.renpy import Game, Mod
from src.gtk import format_gdatetime, HumanBytes


def return_projects() -> list[Game]:
	games_path = root_path / 'games'
	mods_path = root_path / 'mods'

	projects: list[Game] = []
	for path in chain(games_path.glob('*'), mods_path.glob('*')):
		try:
			if path.parent == games_path:
				project = Game(rpath=path)
			else:
				project = Mod(rpath=path)
			projects.append(project)
		except FileNotFoundError:
			logging.debug(f'{path.stem} is not a valid project!')
	
	return projects


def update_library_sidebar(self) -> None:
	projects = return_projects()
	
	unchanged_projects = set(projects) & set(self.projects)
	added_projects = set(projects) - set(self.projects)
	removed_projects = set(self.projects) - set(projects)
	changed_projects = set(projects) - unchanged_projects - added_projects

	logging.debug(
		'\n'
		f'unchanged_projects: {unchanged_projects}\n'
		f'added_projects: {added_projects}\n'
		f'removed_projects: {removed_projects}\n'
		f'changed_projects: {changed_projects}\n'
	)

	buttons: list[Adw.ButtonRow] = []
	for i, project in enumerate(self.projects):
		button = self.library_list_box.get_row_at_index(i)
		buttons.append(button)

	for project in self.projects:
		if project in removed_projects:
			logging.debug(f'project    : {project.codename}')
			for button in buttons:
				logging.debug(f'button.game: {button.game.codename}')
				logging.debug(f'eq         : {project.__eq__(button.game)}')
				logging.debug(f'hash       : {project.__hash__()} vs {button.game.__hash__()}')
				if project == button.game:
					buttons.remove(button)
					self.library_list_box.remove(button)
					logging.debug(f'{project.name} has been found')
					break
			continue

	for project in projects:
		if project in added_projects:
			button = Adw.ButtonRow(title=project.name)
			button.game = project
			button.connect('activated', self.on_game_activated)
			buttons.append(button)
			self.library_list_box.append(button)
			continue

		if project in changed_projects:
			for button in buttons:
				if button.game == project or button.name == project.name:
					button.game = project
					button.name = project.name
					break
			continue

	if not projects:  # ps5 view
		self.library_view_stack.set_visible_child_name('empty')
		self.split_view.set_show_sidebar(False)
	else:
		self.library_view_stack.set_visible_child_name('selected')
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
		last_played = format_gdatetime(project.config['info']['last_played'], 'neat')
		self.last_played_row.set_subtitle(last_played)
	except KeyError:
		self.last_played_row.set_subtitle('N/A')

	try:
		self.playtime_row.set_subtitle(project.config['info']['playtime'])
	except KeyError:
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