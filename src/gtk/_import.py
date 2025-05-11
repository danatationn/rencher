import shutil

from src import local_path
from src.renpy import Game, Mod

import patoolib


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

	rpath = local_path / ('mods' if is_mod else 'games') / name

	patoolib.extract_archive(str(path), 0, str(rpath))

	self.update_progress(0.5 if is_mod else 1)
	if is_mod:
		mod = Mod(rpath=rpath)
		game = game_to_mod.game
		
		files = game.apath.rglob('*')
		sorted_files = sorted(files)
		length = len(sorted_files)
		
		count = 0
		for file in sorted_files:
			
			relative_path = file.relative_to(game.apath)
			target_path = mod.apath / relative_path
			
			if not target_path.exists():
				if file.is_file():
					shutil.copy(file, target_path)
				else:
					target_path.mkdir()
					
			count += 1
			self.update_progress(0.5 + count / length)
			
	game = Game(rpath=rpath)
	game.raw_config['info']['nickname'] = name
	game.setup()

	self.close()