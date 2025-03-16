import stat
import shutil
import subprocess
import platform
from pathlib import Path

from src import root_path
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
			self.rpath = root_path / 'games' / name
			self.apath = paths.find_absolute_path(self.rpath)

		if not name:
			self.name = rpath.name

		self.version = self.return_renpy_version()
		self.codename = self.return_codename()
		self.config = _config.read_game_config(self)


	def return_codename(self) -> str | None:
		"""
			returns a name based off of the .py scripts located in apath
		"""
		py_names = [py_path.stem for py_path in sorted(self.apath.glob('*.py'))]

		if py_names:
			return py_names[0]


	def find_exec_path(self) -> Path | None:
		"""
			windows and linux only rn
		"""
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
			raise NotImplemented('Your OS is not yet implemented.')

		for lib_dir in lib_directories:
			exec_path = self.apath / 'lib' / lib_dir / exec_name
			if exec_path.exists():
				return exec_path
		return None


	def return_renpy_version(self) -> str | None:
		"""
			tries to retrieve the game's ren'py version from multiple known locations:

			- the log file* (it's the third line, but it's not always present)
			- renpy/__init__.py (only present in versions below 8 i believe)
			- renpy/vc_version.py (only present in versions above 8)

			*ok so i don't even need it lol! if i find a game that doesn't use any of these i will bring it back
		"""
		# log_path = self.apath / 'log.txt'
		vc_path = self.apath / 'renpy' / 'vc_version.py'
		init_path = self.apath / 'renpy' / '__init__.py'
		# if log_path.exists():
			# with open(log_path, 'r') as f:
			# 	text = f.read().splitlines()
			# 	for line in text:
			# 		if 'Ren\'Py' in line:
			# 			try:
			# 				parts = line.split()
			# 				return parts[1]
			# 			except ValueError:
			# 				pass
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
			return 'N/A'  # yo shit broken boy


	def run(self) -> subprocess.Popen:
		args = [self.find_exec_path()]
		py_path = self.apath / f'{self.return_codename()}.py'
		if self.version[0] == '6':
			args.extend(['-EO', py_path])

		return subprocess.Popen(args)		


	def cleanup(self) -> None:
		# make files executable (linux)
		exec_path = self.find_exec_path()
		exec_path.chmod(exec_path.stat().st_mode | stat.S_IEXEC)
		

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
			rpath = root_path / 'renpy' / name
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
		if self.return_renpy_version()[0] == '7':
			exec_path = self.find_exec_path()
			libs_path = exec_path.parent / 'libs'
			if libs_path.is_dir():
				shutil.rmtree(libs_path)