import time
from configparser import ConfigParser
from functools import lru_cache
from pathlib import Path

from src import config_path


@lru_cache
class GameConfig(ConfigParser):
	def __init__(self, game_config_path: Path):
		super().__init__()
		
		self.game_config_path = game_config_path
		
		self.read(game_config_path)
		self.validate_config()
		
	def validate_config(self):
		structure = {
			'info': {
				'nickname': '',
				'last_played': '',
				'playtime': 0.0,
				'added_on': int(time.time()),
				'size': int(),
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
			if rencher_config['settings'][key] != '':
				self['overwritten'][key] = rencher_config['settings'][key]
					
	def write_config(self):
		new_config = ConfigParser()
		for section in ['info', 'options']:
			new_config.add_section(section)
			for key, values in self[section].items():
				new_config[section][key] = values

		with open(self.game_config_path, 'w') as f:
			new_config.write(f)

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
		