"""
	the core of it all
"""

__version__ = '1.1.0'  # REMEMBER TO CHANGE THIS
__author__ = 'danatationn'
__description__ = 'A Ren\'Py game manager, made with DDLC mods in mind'
__url__ = 'https://github.com/danatationn/Rencher'
__issue_url__ = 'https://github.com/danatationn/Rencher/issues'

import platform
from pathlib import Path

local_path: Path = Path()
config_path: Path = Path()
tmp_path: Path = Path(__file__).parents[1]

if platform.system() == 'Linux':
	local_path = Path.home() / '.local' / 'share' / 'rencher'
	config_path = Path.home() / '.config' / 'rencher.ini'
elif platform.system() == 'Windows':
	local_path = Path.home() / 'AppData' / 'Local' / 'Rencher'
	config_path = Path.home() / 'AppData' / 'Local' / 'Rencher' / 'config.ini'
