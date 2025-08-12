import glob
import logging
import os
import platform
import shutil
import subprocess
import time
from configparser import NoOptionError

from rencher import GameInvalidError
from rencher.renpy.config import GameConfig
from rencher.renpy.paths import get_absolute_path, get_py_files, validate_game_files


class Game:
    rpath: str = None
    apath: str = None
    config: GameConfig = None

    def __init__(self, rpath: str = None, apath: str = None):
        self.rpath = rpath  # relative path
        self.apath = apath  # absolute path (root / the working directory)

        if not rpath and apath:
            self.rpath = apath
        if not apath and rpath:
            self.apath = get_absolute_path(self.rpath)
            if self.apath is None:
                name = os.path.basename(rpath)
                raise GameInvalidError(f'{name} is not a valid game! ({rpath})')

        config_path = os.path.join(self.apath, 'game/rencher.ini')
        self.config = GameConfig(config_path)

    def __eq__(self, other) -> bool:
        if isinstance(other, Game):
            return self.rpath == other.rpath
        else:
            return False

    def __hash__(self):
        return hash(self.rpath)

    def validate(self) -> bool:
        """
            returns false if game cannot be run/isn't a real game
        """
        files = glob.glob(f'{self.apath}/**', recursive=True)
        return validate_game_files(files)
        

    def get_executable(self) -> str:
        """
            returns a name based off of the .py scripts located in apath
        """
        py_files = get_py_files(self.apath)
        codename = self.config.get_value('codename')
        exec_path = os.path.join(self.apath, f'{codename}.py')
    
        if codename != '':
            return exec_path
        elif len(py_files) == 0:
            raise GameInvalidError(f'No executable found in {self.apath}')
        elif len(py_files) == 1:
            return py_files[0]
        else:
            raise NoOptionError('codename', 'info')
        
    def get_codename(self) -> str:
        exec_name = os.path.basename(self.get_executable())
        return os.path.splitext(exec_name)[0]
    
    def get_name(self) -> str:
        nickname = self.config['info']['nickname']
        if nickname != '':
            return nickname
        else:
            return os.path.basename(self.rpath)
    
    def get_python_path(self) -> str | None:
        arch = platform.machine()
        sys = platform.system().lower()
        if arch == 'AMD64':
            arch = 'x86_64'  # for windose

        lib_directories = (
            f'py3-{sys}-{arch}',
            f'py2-{sys}-{arch}',
            f'{sys}-{arch}',
            f'{sys}-i686',  # last resort
        )

        exec_name = 'pythonw'
        if sys == 'windows':
            exec_name += '.exe'

        for lib_dir in lib_directories:
            exec_path = os.path.join(self.apath, 'lib', lib_dir, exec_name)
            if os.path.isfile(exec_path):
                return exec_path
        return None

    def get_renpy_version(self) -> str | None:
        """
            tries to retrieve the game's ren'py version from multiple known locations:

            - renpy/__init__.py (only in ren'py <8)
            - renpy/vc_version.py (only in ren'py =>8)
        """
        vc_path = os.path.join(self.apath, 'renpy/vc_version.py')
        init_path = os.path.join(self.apath, 'renpy/__init__.py')

        vc_dict = {}
        if os.path.isfile(vc_path):
            with open(vc_path) as f:
                exec(f.read(), {}, vc_dict)
                if vc_dict.get('version'):
                    return vc_dict['version']
                
        if os.path.isfile(init_path):
            with open(init_path) as f:
                """
                    we can't exec() here because the file actually has code in it and has imports
                    instead we'll just do it the basic way (log file 😊) and look for version_tuple
                """
                text = f.read().splitlines()
                for line in text:
                    if 'version_tuple' in line.strip():
                        try:
                            if vc_dict.get('vc_version'):
                                version_tuple = eval(line.split(' = ')[1], {}, vc_dict)
                                return '.'.join(str(i) for i in version_tuple)  # code ironically stolen from __init__
                        except ValueError:
                            pass
        else:
            return None  # Oops!

    def run(self) -> subprocess.Popen:
        """
            launches the game with the specified options
        """
        self.setup()
        self.config.read()  # just to be SURE

        args = [self.get_python_path()]
        env = os.environ
        py_path = os.path.join(self.apath, self.get_executable()) 

        if self.config['overwritten']['skip_splash_scr'] == 'true':
            env['RENPY_SKIP_SPLASHSCREEN'] = '1'
        elif env.get('RENPY_SKIP_SPLASHSCREEN'):
            env.pop('RENPY_SKIP_SPLASHSCREEN')
        if self.config['overwritten']['skip_main_menu'] == 'true':
            env['RENPY_SKIP_MAIN_MENU'] = ('Did you know you can put anything here and it stills work '
                                           'like ren\'py doesn\'t even check for the value it\'s crazy')
        elif env.get('RENPY_SKIP_MAIN_MENU'):
            env.pop('RENPY_SKIP_MAIN_MENU')

        librenpython_path = os.path.join(os.path.dirname(args[0]), 'librenpython.so')
        if os.path.isfile(librenpython_path):
            args.extend([py_path])
        else:
            args.extend(['-EO', py_path])

        if self.config['overwritten']['forced_save_dir'] == 'true':
            save_dir = os.path.join(self.apath, 'game/saves')

            save_slot = self.config['options'].getint('save_slot')
            if save_slot > 1:
                save_dir = os.path.join(os.path.dirname(save_dir), f'saves{save_slot}')
                logging.debug(save_dir)

            args.extend(['--savedir', save_dir])

        config_dict = {}
        for item in self.config['overwritten']:
            config_dict[item] = self.config['overwritten'][item]
        logging.debug(f'config: {config_dict}')
        logging.debug(f'args: {args}')
        return subprocess.Popen(args, env=env)

    def setup(self) -> None:
        """ 
            1. makes files executable for linux
        
            2. in newer ren'py versions, a dll called "librenpython" got added
            this library includes all the python libraries ren'py needs (i think)
            this makes modding a bit more complicated, as certain conflicts might arise
    
            PRE LIBRENPYTHON:
            * libraries were located in lib/ inside the exec path
            * you need to pass "-EO <python_path>" to args
            
            POST LIBRENPYTHON:
            * lib/ folder is gone and instead replaced by librenpython
            * you need to pass "<python_path>" to args instead
        """
        
        exec_path = self.get_python_path()
        exec_mode = os.stat(exec_path).st_mode
        os.chmod(exec_path, exec_mode | 0o111)

        try:
            exec_path = self.get_python_path()
            libs_path = os.path.join(os.path.dirname(exec_path), 'lib')
            librenpython_path = os.path.join(os.path.dirname(exec_path), 'librenpython.so')
            if os.path.isdir(libs_path) and os.path.isfile(librenpython_path):
                shutil.rmtree(libs_path)
        except ValueError:
            pass

    def cleanup(self, playtime: float) -> None:
        self.config['info']['playtime'] = str(playtime)
        self.config['info']['last_played'] = str(int(time.time()))
        self.config.write()

    @property
    def name(self):
        return self.get_name()
    @property
    def codename(self):
        return self.get_codename()
    @property
    def version(self):
        return self.get_renpy_version()
    @property
    def is_mod(self):
        py_files = get_py_files(self.apath)
        if len(py_files) > 1:
            return True
        elif len(py_files) <= 1:
            return False
        else:
            raise FileNotFoundError
    @property
    def is_valid(self):
        return self.validate()
    