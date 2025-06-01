import shutil
import zipfile
from pathlib import Path
import logging

from src import local_path
from src.renpy import Game, Mod
from src.renpy.paths import find_absolute_path

from gi.repository import GLib
import rarfile


def import_game(self):
	game_name = self.import_title.get_text()
	location = Path(self.import_location.get_text())
	is_mod = self.import_game_combo.get_sensitive()
	game_to_mod = self.import_game_combo.get_selected_item()
	rpath = local_path / ('mods' if is_mod else 'games') / game_name
	
		
	if location.suffix == '.zip':
		archive = zipfile.ZipFile(location, 'r')
	else:
		archive = rarfile.RarFile(location, 'r')

	self.import_progress_bar.set_show_text(True)
	total_extract = len(archive.namelist())
	total_copy = sum(1 for file in game_to_mod.game.rpath.rglob('*') if file.is_file()) if is_mod else 0
	total_work = total_extract + total_copy
	
	for i, file in enumerate(archive.namelist(), 1):
		archive.extract(file, rpath)
		GLib.idle_add(self.update_progress, i / total_work)

	archive.close()

	if is_mod:
		game = game_to_mod.game
		target_dir = local_path / 'mods' / game_name
		
		if find_absolute_path(rpath) == local_path / 'mods':
			rpa_path = target_dir / 'game'
			for file in rpath.glob('*'):
				rpa_path.mkdir(exist_ok=True, parents=True)
				file.replace(rpa_path / file.name)

		find_absolute_path.cache_clear()
		apath = find_absolute_path(rpath)
			
		for i, file in enumerate(game.apath.rglob('*'), 1):
			relative_path = file.relative_to(game.apath)
			target_path = apath / relative_path

			if target_path.exists():
				continue
			if target_path.name == 'rencher.ini':
				continue

			target_path.parent.mkdir(exist_ok=True, parents=True)

			if file.is_dir():
				target_path.mkdir(exist_ok=True, parents=True)
			else:
				shutil.copy(file, target_path)
				
			GLib.idle_add(self.update_progress, (total_extract + i) / total_work)
				
	find_absolute_path.cache_clear()
	game = Game(rpath=rpath)
	game.config['info']['nickname'] = game.name

	game_codename = game_to_mod.game.codename
	py_names = [py_path.stem for py_path in sorted(game.apath.glob('*.py'))]

	if len(py_names) == 2:
		py_names.remove(game_codename)
		game.config['info']['codename'] = py_names[0]

	game.config.write_config()
	