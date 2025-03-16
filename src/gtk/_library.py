import logging
from pathlib import Path

from gi.repository import Adw, GObject, Gtk

from src import root_path
from src.renpy import Game, Mod
from src.gtk import format_gdatetime, HumanBytes


def update_library_sidebar(self) -> None:
	games_path = root_path / 'games'
	mods_path = root_path / 'mods'
	games = [Game(rpath=path) for path in games_path.glob('*') if path.is_dir()]
	mods = [Mod(rpath=path) for path in mods_path.glob('*') if path.is_dir()]
	self.projects = games
	self.projects += mods

	for game in self.projects:
		button = Adw.ButtonRow(title=game.name)
		button.game = game
		button.connect('activated', self.on_game_activated)
		self.library_list_box.append(button)

	if not self.projects:  # ps5 view
		self.library_view_stack.set_visible_child_name('empty')
		self.split_view.set_show_sidebar(False)


def update_library_view(self, project: Game) -> None:
	self.selected_status_page.set_title(project.name)
	
	last_played = format_gdatetime(project.config['info']['last_played'], 'neat')
	size = project.config['info']['size']
	formatted_size = HumanBytes.format(int(size))
	
	self.last_played_row.set_subtitle(last_played)
	self.playtime_row.set_subtitle(project.config['info']['playtime'])
	self.added_on_row.set_subtitle(project.config['info']['added_on'])
	self.size_row.set_subtitle(formatted_size)

	self.version_row.set_subtitle(project.version)
	self.rpath_row.set_subtitle(str(project.rpath))
	self.codename_row.set_subtitle(project.codename)