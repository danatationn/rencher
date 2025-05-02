import os
import stat
import shutil
import subprocess
import platform
import time
from pathlib import Path

from src import local_path
from src.renpy import paths, _config


class Game:
	name: str = None
	codename: str = None
	rpath: Path = None
	apath: Path = None
	version: str = None
	config: dict = None


	def __init__(self, rpath: Path = None, apath: Path = None, name: str = None):
		self.rpath = rpath  # relative path
		self.apath = apath  # absolute path (cwd)
		self.name = name

		if not rpath and apath:
			self.rpath = apath
		if not apath and rpath:
			self.apath = paths.find_absolute_path(self.rpath)
			if self.apath is None:
				raise FileNotFoundError('The game is a lie.')

		if not apath and not rpath and name:
			self.rpath = local_path / 'games' / name
			self.apath = paths.find_absolute_path(self.rpath)

		if not name:
			self.name = self.rpath.name

		self.version = self.return_renpy_version()
		self.codename = self.return_codename()
		self.config = _config.read_game_config(self)


	def __eq__(self, other) -> bool:
		if isinstance(other, Game):
			return(
				self.name == other.name
				and self.codename == other.codename
				and self.rpath == other.rpath
				and self.apath == other.apath
				and self.version == other.version
				# and self.config == other.config
			)
		else:
			return False


	def __hash__(self):
		# config_tuple = tuple((section, tuple(items.items())) for section, items in self.config.items())
		return hash(
			(
				self.name,
				self.codename,
				self.rpath,
				self.apath,
				self.version,
				# config_tuple
			)
		)


	def return_codename(self) -> str | None:
		"""
			returns a name based off of the .py scripts located in apath
		"""
		py_names = [py_path.stem for py_path in sorted(self.apath.glob('*.py'))]

		if py_names:
			return py_names[0]
		else:
			return None

	def find_exec_path(self) -> Path | None:
		arch = platform.machine()
		os = platform.system().lower()

		lib_directories = (
			f'py3-{os}-{arch}',
			f'py2-{os}-{arch}',
			f'{os}-{arch}',
			f'{os}-i686'  # last resort
		)

		if os == 'windows':
			exec_name = 'python.exe'
		elif os == 'linux':
			codename = self.return_codename()
			exec_name = Path(codename).stem
		else:
			err = f'{os} is not supported. Sorry !'
			raise NotImplemented(err)

		for lib_dir in lib_directories:
			exec_path = self.apath / 'lib' / lib_dir / exec_name
			if exec_path.exists():
				return exec_path
		return None


	def return_renpy_version(self) -> str | None:
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
			return None  # yo shit broken boy


	def run(self) -> subprocess.Popen:
		args = [self.find_exec_path()]
		env = os.environ
		py_path = self.apath / f'{self.return_codename()}.py'
		
		if self.config['options']['skip_splash_scr'] == 'true':
			env['RENPY_SKIP_SPLASHSCREEN'] = '1'
		if self.config['options']['skip_main_menu'] == 'true':
			env['RENPY_SKIP_MAIN_MENU'] = '1'
		
		if self.version[0] == '6':
			args.extend(['-EO', py_path])

		return subprocess.Popen(args, env=env)		


	def setup(self) -> None:
		# make files executable (linux)
		exec_path = self.find_exec_path()
		exec_path.chmod(exec_path.stat().st_mode | stat.S_IEXEC)


	def cleanup(self, playtime: float) -> None:
		self.config['info']['playtime'] = str(playtime)
		self.config['info']['last_played'] = str(int(time.time()))
		_config.write_game_config(self)


class Mod(Game):
	name: str = None
	codename: str = None
	rpath: Path = None
	apath: Path = None
	is_independent: bool = None
	version: str = None
	config: dict = None


	def __init__(self, rpath: Path = None, apath: Path = None, name: str = None):
		if not apath and not rpath and name:
			rpath = local_path / 'renpy' / name
			apath = paths.find_absolute_path(rpath)

		super().__init__(rpath=rpath, apath=apath, name=name)

		self.version = self.return_renpy_version()
		self.codename = self.return_codename()

		if self.codename != super().return_codename():
			self.is_independent = True
		else:
			self.is_independent = False


	def return_codename(self) -> str | None:
		# TODO de-ddlc this
		"""
			returns a name based off of the .py scripts located in apath

			function modified as renpy tend to be independent of their base games
		"""
		py_names = [
			py_path.stem for py_path in sorted(self.apath.glob('*.py'))
			if py_path.stem not in 'DDLC'
		]

		if len(py_names) > 0:
			return py_names[0]
		else:
			return 'DDLC'


	def cleanup(self) -> None:
		super().cleanup()

		# fix future.standard_library (ren'py 7+, linux)
		ver_first_digit = self.return_renpy_version()[0]
		try:
			if int(ver_first_digit) > 6:
				exec_path = self.find_exec_path()
				libs_path = exec_path.parent / 'libs'
				if libs_path.is_dir():
					shutil.rmtree(libs_path)
		except ValueError:
			pass