__version__ = '1.1.0'  # REMEMBER TO CHANGE THIS
__author__ = 'danatationn'
__description__ = 'A Ren\'Py game manager, made with DDLC mods in mind'
__url__ = 'https://github.com/danatationn/Rencher'
__issue_url__ = 'https://github.com/danatationn/Rencher/issues'

import os.path
import platform

local_path: str = ''
config_path: str = ''
tmp_path: str = os.path.abspath(os.path.join(__file__, '..', '..'))
home_path: str = os.path.expanduser('~')

if platform.system() == 'Linux':
    local_path = os.path.join(home_path, '.local/share/rencher')
    config_path = os.path.join(home_path, '.config/rencher.ini')
elif platform.system() == 'Windows':
    local_path = os.path.join(home_path, 'AppData/Local/Rencher') 
    config_path = os.path.join(home_path, 'AppData/Local/Rencher/config.ini')
