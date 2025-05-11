import unittest
from pathlib import Path

from configparser import ConfigParser
from src.renpy._config import GameConfig


class TestConfig(unittest.TestCase):
	def test_something(self):
		# config = GameConfig(Path(__file__).parent / 'rencher.ini')
		# for section in config.sections():
		# 	for key in config[section]:
		# 		print(f'config[{section}][{key}]: ' + config[section][key])

		# config.write_config()

		GameConfig.write_config()

if __name__ == '__main__':
	unittest.main()
