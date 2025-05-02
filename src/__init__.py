import platform
import sys
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
