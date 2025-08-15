import ast
import glob
import logging
import os
import platform
import shutil
import subprocess
import time
import re

from rencher import GameInvalidError, GameNoExecutableError
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
            raise GameNoExecutableError
        
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
            tries to retrieve the game's ren'py version (WITHOUT USING EXEC)
            
            there a lot of ways that versions are tracked based on what version it is
            1. ren'py 6:
                * the version is located in `version_tuple` in `renpy/__init__.py`
                * the commit number is located in `vc_version` in `renpy/vc_version.py`
            2. ren'py 7:
                * the version is located in the first `version_tuple` located in`renpy/ __init__.py`
                    # there are 2 version tuples
                      the py2 one (the real one) and the py3 one (the one preparing for ren'py 8)
                * the commit number is located in `vc_version` in `renpy/vc_version.py`
            3. ren'py 7.6:
                * same as ren'py 7, however it's stored as a `VersionTuple`
                    # i have no idea if this occurs with other versions. i just noticed it in ren'py 7.6
            4. ren'py 8:
                * the version and commit number are located in `version` in `renpy/vc_version.py`
            
        Returns:
            the version as a string. returns `None` if it couldn't be determined
        """
        vc_path = os.path.join(self.apath, 'renpy', 'vc_version.py')
        init_path = os.path.join(self.apath, 'renpy', '__init__.py')
        commit = 0
        version = ''
        
        if os.path.isfile(vc_path):
            with open(vc_path) as f:
                vc_content = f.read()
                version_match = re.findall(r'version .*\'(.*)\'', vc_content, re.MULTILINE)
                if version_match:
                    version = version_match[0]
                commit_match = re.findall(r'vc_version.*(\b\d+\b)', vc_content, re.MULTILINE)
                if commit_match:
                    commit = commit_match[0]
        
        if os.path.isfile(init_path):
            with open(init_path) as f:
                init_content = f.read()
                version_tuple_match = re.findall(r'version_tuple.*\((\d.*)\)', init_content, re.MULTILINE)
                if version_tuple_match:
                    version_tuple = re.findall(r'\b\d+\b', version_tuple_match[0])
                    version = '.'.join(str(i) for i in version_tuple)
        
        if commit:
            version += '.' + commit
        return version

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
    