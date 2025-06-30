import time
from configparser import ConfigParser
from pathlib import Path
import logging

from src import config_path, local_path


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
		self.validate()
	
	def validate(self):
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
		
		rencher_config = RencherConfig()
		
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

		self.game_config_path.parent.mkdir(exist_ok=True, parents=True)
		self.game_config_path.touch(exist_ok=True)
		if not fp:
			fp = open(self.game_config_path, 'w')
		new_config.write(fp, space_around_delimiters)

class RencherConfig(ConfigParser):
	def __init__(self):
		super().__init__()
		self.read()
	
	def read(self, filenames=None, encoding=None):
		if not filenames:
			filenames = config_path
		super().read(filenames)
		self.validate()
	
	def validate(self):
		structure = {
			'settings': {
				'data_dir': '',
				'surpress_updates': 'false',
				'delete_on_import': 'false',
				'skip_splash_scr': 'false',
				'skip_main_menu': 'false',
				'forced_save_dir': 'false'	
			}
		}

		for section, keys in structure.items():
			if section not in self:
				self.add_section(section)
				
			for key, values in keys.items():
				if key not in self[section]:
					self[section][key] = values
					
		if not config_path.is_file():
			self.write()
					
	def write(self, fp=None, space_around_delimiters=True):
		config_path.parent.mkdir(exist_ok=True)
		
		config_path.touch(exist_ok=True)
		if not fp:
			fp = open(config_path, 'w')
		super().write(fp, space_around_delimiters)
		fp.close()
		
	def get_data_dir(self) -> Path:
		if self['settings']['data_dir'] == '':
			return local_path
		else:
			return Path(self['settings']['data_dir'])