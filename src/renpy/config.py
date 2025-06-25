import time
from configparser import ConfigParser
from pathlib import Path
import logging

from src import config_path


class GameConfig(ConfigParser):
	game_config_path: Path
	
	def __init__(self, game_config_path: Path):
		super().__init__()
		
		self.game_config_path = game_config_path
		self.read(game_config_path)
		
	def read(self, filenames=None, encoding=None):
		if not filenames:
			filenames = self.game_config_path
		super().read(filenames)
		self.validate_config()
	
	def validate_config(self):
		structure = {
			'info': {
				'nickname': '',
				'last_played': '',
				'playtime': 0.0,
				'added_on': int(time.time()),
				#'size': int(),
				'codename': ''
			},
			
			'options': {
				'skip_splash_scr': '',
				'skip_main_menu': '',
				'forced_save_dir': '',
				'save_slot': 1
			},
			
			'overwritten': {
				'skip_splash_scr': '',
				'skip_main_menu': '',
				'forced_save_dir': ''
			}
		}
		
		with open(config_path, 'r') as f:
			rencher_config = ConfigParser()
			rencher_config.read_file(f)
		
		for section, keys in structure.items():
			if section not in self:
				self.add_section(section)
				
			for key, values in keys.items():
				if key not in self[section]:
					self[section][key] = str(values)
					
				if values and self[section][key]:
					if isinstance(values, bool):
						value = self.getboolean(section, key, fallback='')
					elif isinstance(values, int):
						value = self.getint(section, key, fallback=values)
					elif isinstance(values, float):
						value = self.getfloat(section, key, fallback=values)
					else:
						value = ''
						
					self[section][key] = str(value)
					
		for key, values in structure['overwritten'].items():
			if self['options'][key]:
				self['overwritten'][key] = self['options'][key]
			else:
				self['overwritten'][key] = rencher_config['settings'][key]
			
	def write(self, fp=None, space_around_delimiters=True):
		new_config = ConfigParser()
		for section in ['info', 'options']:
			new_config.add_section(section)
			for key, values in self[section].items():
				new_config[section][key] = values

		if not fp:
			fp = open(self.game_config_path, 'w')
		new_config.write(fp, space_around_delimiters)

def create_config() -> None:
	config = ConfigParser()

	config['settings'] = {
		'data_dir': '',
		'skip_splash_scr': 'false',
		'skip_main_menu': 'false',
		'discord_rpc': 'true',
		'forced_save_dir': 'false'
	}
	
	config_path.parent.mkdir(exist_ok=True)
	# config_path.touch(exist_ok=True)
	config.write()
		