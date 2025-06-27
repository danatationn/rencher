import logging
import os
import shutil
import subprocess
import platform
import time
from pathlib import Path
from configparser import NoOptionError
from pprint import pprint

from src.renpy import paths
from src.renpy.config import GameConfig


class Game:
	name: str = None
	codename: str = None
	rpath: Path = None
	apath: Path = None
	version: str = None
	config: GameConfig = None

	def __init__(self, rpath: Path = None, apath: Path = None):
		self.rpath = rpath  # relative path
		self.apath = apath  # absolute path (root / the working directory)

		if not rpath and apath:
			self.rpath = apath
		if not apath and rpath:
			self.apath = paths.find_absolute_path(self.rpath)
			if self.apath is None:
				raise FileNotFoundError('This is not a real game!')

		config_path = self.apath / 'game' / 'rencher.ini'
		if not config_path.exists():
			config = GameConfig(config_path)
			config.write()

		self.config = GameConfig(config_path)

		if self.config['info']['nickname'] != '':
			self.name = self.config['info']['nickname']
		else:
			self.name = self.rpath.name

		self.version = self.get_renpy_version()
		self.codename = self.get_executable().stem

	def __eq__(self, other) -> bool:
		if isinstance(other, Game):
			return (
					self.name == other.name
					and self.codename == other.codename
					and self.rpath == other.rpath
					and self.apath == other.apath
					and self.version == other.version
			)
		else:
			return False

	def __hash__(self):
		return hash(
			(
				self.name,
				self.codename,
				self.rpath,
				self.apath,
				self.version,
			)
		)

	def get_executable(self) -> Path | None:
		"""
			returns a name based off of the .py scripts located in apath
		"""
		py_files = [py_path for py_path in sorted(self.apath.glob('*.py'))]

		if py_files:
			return py_files[0]
		else:
			return None

	def get_python_path(self) -> Path | None:
		arch = platform.machine()
		os = platform.system().lower()
		if arch == 'AMD64':
			arch = 'x86_64'  # for windose

		lib_directories = (
			f'py3-{os}-{arch}',
			f'py2-{os}-{arch}',
			f'{os}-{arch}',
			f'{os}-i686'  # last resort
		)

		exec_name = 'python'
		if os == 'windows':
			exec_name += '.exe'

		for lib_dir in lib_directories:
			exec_path = self.apath / 'lib' / lib_dir / exec_name
			if exec_path.exists():
				return exec_path
		return None

	def get_renpy_version(self) -> str | None:
		"""
			tries to retrieve the game's ren'py version from multiple known locations:

			- renpy/__init__.py (only in ren'py <8)
			- renpy/vc_version.py (only in ren'py =>8)
		"""
		# log_path = self.apath / 'log.txt'
		vc_path = self.apath / 'renpy' / 'vc_version.py'
		init_path = self.apath / 'renpy' / '__init__.py'

		vc_dict = {}
		if vc_path.exists():
			with open(vc_path, 'r') as f:
				exec(f.read(), {}, vc_dict)
				if vc_dict.get('version'):
					return vc_dict['version']
		if init_path.exists():
			with open(init_path, 'r') as f:
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
		self.setup()
		self.config.read()  # just to be SURE

		args = [self.get_python_path()]
		env = os.environ
		py_path = self.apath / self.get_executable()

		if self.config['overwritten']['skip_splash_scr'] == 'true':
			env['RENPY_SKIP_SPLASHSCREEN'] = '1'
		if self.config['overwritten']['skip_main_menu'] == 'true':
			env['RENPY_SKIP_MAIN_MENU'] = '1'

		librenpython_path = args[0].parent / 'librenpython.so'
		if librenpython_path.exists():
			args.extend([py_path])
		else:
			args.extend(['-EO', py_path])

		if self.config['overwritten']['forced_save_dir'] == 'true':
			save_dir = self.apath / 'game' / 'saves'
			
			save_slot = self.config['options'].getint('save_slot')
			if save_slot > 1:
				save_dir = save_dir.with_name(f'saves{save_slot}')
				logging.debug(save_dir)
				
			args.extend(['--savedir', save_dir])

		config_dict = {}
		for item in self.config['overwritten']:
			config_dict[item] = self.config['overwritten'][item]
		logging.debug(f'config: {config_dict}')
		logging.debug(f'args: {args}')
		return subprocess.Popen(args, env=env)

	def setup(self) -> None:
		# LINUX: make files executable
		exec_path = self.get_python_path()
		exec_path.chmod(exec_path.stat().st_mode | 0o111)

	def cleanup(self, playtime: float) -> None:
		self.config['info']['playtime'] = str(playtime)
		self.config['info']['last_played'] = str(int(time.time()))
		self.config.write()


class Mod(Game):
	name: str = None
	codename: str = None
	rpath: Path = None
	apath: Path = None
	# is_independent: bool = None
	version: str = None
	config: GameConfig = None

	def __init__(self, rpath: Path = None, apath: Path = None):
		super().__init__(rpath=rpath, apath=apath)

	def get_executable(self) -> str | None:
		"""
			returns a name based off of the .py scripts located in apath

			function modified as renpy tend to be independent of their base games
		"""
		py_files = [py_path for py_path in sorted(self.apath.glob('*.py'))]
		codename = self.config['info']['codename']
		exec = self.apath / f'{codename}.py'

		if codename != '':
			return exec
		elif len(py_files) == 0:
			raise FileNotFoundError
		elif len(py_files) == 1:
			return py_files[0]
		else:
			raise NoOptionError('codename', 'info')

	def setup(self):
		""" in newer ren'py versions, a dll called "librenpython" got added
		this library includes all the python libraries ren'py needs (i think)
		this makes modding a bit more complicated, as errors arise based on mod ren'py versions and the game's (ddlc)

		PRE LIBRENPYTHON:
		* libraries were located in lib/ inside the exec path
		* you needed to pass "-EO <python_path>" to args
		
		POST LIBRENPYTHON:
		* lib/ folder is gone
		* you no longer need to pass anything to args
		"""
		super().setup()

		try:
			exec_path = self.get_python_path()
			libs_path = exec_path.parent / 'lib'
			librenpython_path = exec_path.parent / 'librenpython.so'
			if libs_path.is_dir() and librenpython_path.exists():
				shutil.rmtree(libs_path)
		except ValueError:
			pass
