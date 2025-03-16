import logging
import shutil
import time
from pathlib import Path

from src import root_path
from src.renpy import Game, Mod
from src.gtk import GameItem

import patoolib
from gi.repository import GLib


def import_game(self):
	name = self.import_title.get_text()
	path = self.import_location.get_text()
	is_mod = self.import_game_combo.get_sensitive()
	game_to_mod = self.import_game_combo.get_selected_item()
	
	self.import_progress_bar.set_show_text(True)
	
	patoolib.test_archive(path)
	self.update_progress(0.1)
	
	if name == '':
		name = path.stem

	if not is_mod:
		target_path = root_path / 'games' / name
	else:
		target_path = root_path / 'mods' / name

	patoolib.extract_archive(str(path), 0, str(target_path))

	if not is_mod:
		self.update_progress(1)
	else:
		self.update_progress(0.5)
		
		mod = Mod(rpath=target_path)
		game = game_to_mod.game
		
		files = game.apath.rglob('*')
		sorted_files = sorted(files)
		length = len(sorted_files)
		
		count = 0
		for file in sorted_files:
			
			relative_path = file.relative_to(game.apath)
			target_path = mod.apath / relative_path
			
			if not target_path.exists():
				# logging.debug(target_path)
				if file.is_file():
					shutil.copy(file, target_path)
				else:
					target_path.mkdir()
					
			count += 1
			self.update_progress(0.5 + count / length)
		
	self.close()		