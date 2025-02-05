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

import configparser
from gi.repository import GLib
from pathlib import Path

def create_config() -> None:
	config = configparser.ConfigParser()

	config['options'] = {
		'skip_splash_scr': 'false',
		'skip_main_menu': 'false',
		'enable_discord_rpc': 'true'
	}
	config['options.saves'] = {
		'save_dir_type': '1'
	}


def create_game_config(self) -> None:
	config = configparser.ConfigParser()

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
		'enable_discord_rpc': ''
	}
	config['options.saves'] = {
		'save_slot': 1,
		'save_dir_type': '',
		'custom_save_dir': ''
	}

	config_path = self.apath / 'game' / 'rencher.ini'
	config_path.touch()
	with open(config_path, 'w') as f:
		config.write(f)


def read_game_config(self) -> dict:
	config_path = self.apath / 'game' / 'rencher.ini'
	if not config_path.exists():
		create_game_config(self)

	with open(config_path, 'r') as f:
		config = configparser.ConfigParser()
		config.read_file(f)

	return config