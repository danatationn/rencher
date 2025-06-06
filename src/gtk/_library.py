import logging
from itertools import chain
from configparser import NoOptionError

from gi.repository import Adw, GLib

from src import local_path
from src.renpy import Game, Mod
from src.gtk import format_gdatetime
from src.gtk.codename_dialog import RencherCodename


def return_projects(self) -> list[Game]:
	games_path = local_path / 'games'
	mods_path = local_path / 'mods'

	projects: list[Game] = []
	for path in chain(games_path.glob('*'), mods_path.glob('*')):
		try:
			if path.parent == games_path:
				projects.append(Game(rpath=path))
			else:
				projects.append(Mod(rpath=path))
		except FileNotFoundError:
			pass
		except NoOptionError:
			dialog = RencherCodename(path, self)
			dialog.choose(self)

	return projects

def update_library_sidebar(self) -> None:
	projects = return_projects(self)
	
	added_projects = set(projects) - set(self.projects)
	removed_projects = set(self.projects) - set(projects)
	# assuming that all the projects are changed is simpler and IS NOT O(n^2) !!!!!!!!!
	# will there be false positives? yeah. i need to alter watchdog to hand out the changed projects
	changed_projects = set(projects) - added_projects

	log = ''
	for project in removed_projects:
		log += f'-{project.name} '
	for project in changed_projects:
		log += f'~{project.name} '
	for project in added_projects:
		log += f'+{project.name} '

	if log != '':
		logging.debug(log)

	buttons = {}
	for i, project in enumerate(self.projects):
		button = self.library_list_box.get_row_at_index(i)
		buttons[i] = button

	for button in buttons.values():
		if button.game in removed_projects:
			self.library_list_box.remove(button)

	for project in added_projects:
		button = Adw.ButtonRow(title=project.name)
		button.game = project
		self.library_list_box.append(button)
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

	# for i in range(self.log_row.get_n_rows()):
	# 	row = self.log_row.get_row_at_index(i)
	# 	self.log_row.remove(row)
	#
	# log_path = project.apath / 'log.txt'
	# if log_path.exists():
	# 	with open(log_path, 'r') as f:
	# 		log = f.read()
	#
	# 	row = Adw.ActionRow(title='Log File', subtitle=log)
	# 	row.get_style_context().add_class('monospace')
	# 	self.log_row.add_row(row)

	# try:
	# 	size = project.config['info']['size']
	# 	formatted_size = HumanBytes.format(int(size), metric=True)
	# 	self.size_row.set_subtitle(formatted_size)
	# except KeyError:
	# 	self.size_row.set_subtitle('N/A')

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
	