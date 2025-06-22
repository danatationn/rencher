import logging
import shutil
import zipfile
from pathlib import Path
import secrets

from src import local_path
from src.gtk import windowficate_file
from src.renpy import Game
from src.renpy.paths import find_absolute_path

from gi.repository import GLib
import rarfile

def import_game(self):
	game_name = self.import_title.get_text()
	location = Path(self.import_location.get_text())
	is_mod = self.import_game_combo.get_sensitive()
	game_to_mod = self.import_game_combo.get_selected_item()
	
	try:
		dir_name = windowficate_file(self.import_title.get_text())
	except ValueError:
		rpath = Path()  # so it shuts up
		try:
			dir_name = windowficate_file(Path(self.import_location.get_text())).stem
		except ValueError:
			rpath = Path()  # so it shuts up
	else:
		rpath = local_path / ('mods' if is_mod else 'games') / dir_name
	
	while True:
		if rpath.is_dir():
			dir_name = secrets.token_urlsafe(4)  # simple random string like 'vRDQzw' so it's not difficult to remember
			rpath = local_path / ('mods' if is_mod else 'games') / dir_name
		else:
			break
		
	if location.suffix == '.zip':
		archive = zipfile.ZipFile(location, 'r')
	else:
		archive = rarfile.RarFile(location, 'r')

	self.import_progress_bar.set_visible(True)
	total_extract = len(archive.namelist())
	total_copy = sum(1 for file in game_to_mod.game.rpath.rglob('*') if file.is_file()) if is_mod else 0
	total_work = total_extract + total_copy
	
	for i, file in enumerate(archive.namelist(), 1):
		if not self.cancel_flag.is_set():
			archive.extract(file, rpath)
			GLib.idle_add(self.import_progress_bar.set_fraction, i / total_work)

	archive.close()

	if is_mod and not self.cancel_flag.is_set():
		game = game_to_mod.game
		target_dir = local_path / 'mods' / game_name
		
		if find_absolute_path(rpath) == local_path / 'mods':
			rpa_path = target_dir / 'game'
			for file in rpath.glob('*'):
				rpa_path.mkdir(exist_ok=True, parents=True)
				file.replace(rpa_path / file.name)

		# we already did find_absolute_path, and it's possible that the directory has now changed completely
		# we need to clear the cache in order for it to not return the same thing
		find_absolute_path.cache_clear()
		apath = find_absolute_path(rpath)
			
		for i, file in enumerate(game.apath.rglob('*'), 1):
			if not self.cancel_flag.is_set():
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
					
				GLib.idle_add(self.import_progress_bar.set_fraction, (total_extract + i) / total_work)
		
	if not self.cancel_flag.is_set():
		find_absolute_path.cache_clear()
		game = Game(rpath=rpath)
		game.config['info']['nickname'] = game_name
	
		game_codename = game_to_mod.game.codename
		py_names = [py_path.stem for py_path in sorted(game.apath.glob('*.py'))]
	
		if len(py_names) == 2:
			py_names.remove(game_codename)
			game.config['info']['codename'] = py_names[0]
	
		game.config.write_config()
	else:
		shutil.rmtree(rpath, ignore_errors=True)
		