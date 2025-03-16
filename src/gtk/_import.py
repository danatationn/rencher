import logging
import shutil
from pathlib import Path

from src import root_path
from src.renpy import Game, Mod
from src.gtk import GameItem

import patoolib


def import_game(self):
	name = self.import_title.get_text()
	path = self.import_location.get_text()
	is_mod = self.import_game_combo.get_sensitive()
	game_to_mod = self.import_game_combo.get_selected_item()
	
	if name == '':
		name = path.stem

	if not is_mod:
		target_path = root_path / 'games' / name
	else:
		target_path = root_path / 'mods' / name

	patoolib.extract_archive(str(path), 0, str(target_path))

	if is_mod:
		mod = Mod(rpath=target_path)
		game = game_to_mod.game
		
		files = game.apath.rglob('*')
		
		for file in sorted(files):
			relative_path = file.relative_to(game.apath)
			target_path = mod.apath / relative_path
			
			if not target_path.exists():
				logging.debug(target_path)
				if target_path.is_file():
					shutil.copy(file, target_path)
				else:
					target_path.mkdir()