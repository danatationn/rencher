"""
	oh boy the configs

	this will be a pain to implement maybe i think

	! all keys that have nothing as their value in the [options] category actually uses the default from the settings

	# INFO

	the size calculation only happens when the config is created as it's stupid to keep rechecking it methinks

	# OPTIONS

	nothing to comment about here

	maybe don't tick on skip_main_menu if you're not a dev ? idk

	## SAVES

	there are 3 savedir types:

	* 0 - let the game decide what directory it wants to save in
	* 1 - save in apath/game/saves/
	* 2 - use the defined custom save directory

	save slots only work with type no. 1
"""
import platform
from configparser import ConfigParser
from functools import lru_cache
from pathlib import Path

from gi.repository import GLib

from src import config_path


class GameConfig(ConfigParser):
	...

def create_config() -> None:
	config = ConfigParser()

	config['settings'] = {
		'data_dir': '',
		'skip_splash_scr': 'false',
		'skip_main_menu': 'false',
		'discord_rpc': 'true',
		'forced_save_dir': 'false'
	}
	
	with open(config_path, 'w') as f:
		config.write(f)


def create_game_config(self) -> None:
	config = ConfigParser()

	size_bytes = sum(file.stat().st_size for file in self.rpath.rglob('*') if file.exists())
	added_on_date = GLib.DateTime.new_now_utc().to_unix()

	config['info'] = {
		'nickname': '',
		'last_played': '',
		'playtime': 0,
		'added_on': added_on_date,
		'size': size_bytes
	}

	config['options'] = {
		'skip_splash_scr': '',
		'skip_main_menu': '',
		'discord_rpc': ''
	}
	config['options.saves'] = {
		'forced_save_dir': '',
		'save_slot': 1
	}

	game_config_path = self.apath / 'game' / 'rencher.ini'
	game_config_path.touch()
	with open(game_config_path, 'w') as f:
		config.write(f)


@lru_cache
def read_game_config(self) -> dict:
	if not config_path.exists():
		create_config()
	with open(config_path, 'r') as f:
		config = ConfigParser()
		config.read_file(f)
	
	game_config_path = self.apath / 'game' / 'rencher.ini'
	if not game_config_path.exists():
		create_game_config(self)
	with open(game_config_path, 'r') as f:
		game_config = ConfigParser()
		game_config.read_file(f)

	for key in ['skip_splash_scr', 'skip_main_menu', 'discord_rpc']:
		if game_config.get('options', key) == '':
			game_config.set('options', key, config.get('settings', key))

	if game_config.get('options.saves', 'forced_save_dir'):
		game_config.set('options.saves', 'forced_save_dir', config.get('settings', 'forced_save_dir'))

	return game_config


def write_game_config(self) -> None:
	game_config_path = self.apath / 'game' / 'rencher.ini'
	if not game_config_path.exists():
		create_game_config(self)

	config = ConfigParser()
	for section, options in self.config.items():
		config[section] = options

	with open(game_config_path, 'w') as f:
		config.write(f)