import logging
from pathlib import Path

from gi.repository import Adw

from src import root_path
from src.renpy import Game, Mod


def update_library_view(self) -> None:
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