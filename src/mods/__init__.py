import subprocess
import platform
from pathlib import Path
from src.mods import paths


class Mod:
	name: str = None
	codename: str = None
	rpath: Path = None
	apath: Path = None
	type: int = None

	def __init__(self, rpath: Path = None, apath: Path = None, name: str = None):
		self.rpath = rpath  # relative path
		self.apath = apath  # absolute path
		self.name = name

		if not rpath and apath:
			self.rpath = apath
		if not apath and rpath:
			self.apath = paths.find_relative_path(self.rpath)
			if self.apath is None:
				raise FileNotFoundError('The mod is a lie.')

		if not apath and not rpath and name:
			self.apath = Path.cwd() / 'mods' / name
			self.rpath = self.apath

		if not name:
			self.name = rpath.name

		self.codename = self.find_codename()
		if self.codename == 'DDLC.py':
			self.type = 0  # ren'py 6
		else:
			self.type = 1  # ren'py 7/8

	def find_codename(self) -> str | None:
		"""
			returns a name based off of the .py scripts located in apath
			useful to quickly tell if a mod is ren'py 6 or 7/8
		"""
		py_names = [
			py_path.name for py_path in sorted(self.apath.glob('*.py'))
			if py_path.name not in {'DDLC.py', 'LinuxLauncher.py'}
		]

		if len(py_names) > 0:
			return py_names[0]
		else:
			return 'DDLC.py'

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
			f'{os}-i686'  # ddlc is 32-bit only on windows; ren'py 6 mods are 32-bit only
		)

		if os == 'windows':
			exec_name = 'python.exe'
		elif os == 'linux':
			codename = self.find_codename()
			exec_name = Path(codename).stem
		else:
			raise NotImplemented('Your OS is not yet implemented.')

		for lib_dir in lib_directories:
			exec_path = self.apath / 'lib' / lib_dir / exec_name
			if exec_path.exists():
				return exec_path
		return None

	def run(self) -> None:
		"""
			this will be handled by the ui but for now it's nice to daydream
		"""

		args = [self.find_exec_path()]
		if not self.type:
			args.extend(['-EO', self.apath / 'DDLC.py'])

		subprocess.run(args)