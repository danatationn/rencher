#
# FUCK YOU NUITKA
#
import platform
import subprocess
import sys
import tomllib
from pathlib import Path

from src.gtk import blp2ui
from nuitka import __main__ as nuitka

blp2ui()
ui_path = Path(__file__).parent / 'src' / 'gtk' / 'ui'
main_path = Path(__file__).parent / 'main.py'
yaml_path = Path(__file__).parent / 'build.yml'
pyproject_path = Path(__file__).parent / 'pyproject.toml'
bin_path = Path('C:/msys64/ucrt64/bin/')  # windows/msys2 

with open(pyproject_path, 'rb') as f:
	project = tomllib.load(f)

args = [
	f'--main={main_path}',
	'--standalone',
	'--onefile',
	'--output-filename=Rencher',
	'--company-name=danatationn',
	f'--file-version={project['project']['version']}',
	f'--product-version={project['project']['version']}',
	f'--file-description={project['project']['description']}',
	f'--include-data-dir={ui_path}=src/gtk/ui',
	'--assume-yes-for-downloads',
]

if platform.system() == 'Windows':
	while not bin_path.is_dir():
		input_path = input('MSYS2 could not be found.\nPlease enter its path. ')
		bin_path = Path(input_path) / 'ucrt64' / 'bin'

	args.append('--include-module=gi._enum')

	required_ddls = [
		'libadwaita-1-0.dll',
		'vulkan-1.dll',
		'libwebpdemux-2.dll',
		'libwebpmux-3.dll',
		'libsqlite3-0.dll',
		'libncursesw6.dll',
		'libgthread-2.0-0.dll',
		'gdbus.exe'
	]

	for dll in required_ddls:
		if Path(bin_path / dll).exists():
			args.append(f'--include-data-files={bin_path}/{dll}={dll}')
		else:
			msg = f'(UCRT64) {dll} was not found. Please install it and try again.'
			FileNotFoundError(msg)

	ntldd_path = bin_path / 'ntldd.exe'
	if not ntldd_path.exists():
		msg = 'ntldd is not installed. Please install it and try again.'
		FileNotFoundError(msg)
		
	for dll_name in required_ddls:
		result = subprocess.run(
			['bash', '-c', f'ntldd -R {dll_name}'],
			cwd=str(bin_path),
			capture_output=True,
			text=True,
			check=True
		)
		output = result.stdout.strip()
		dlls = {}
	
		for line in output.split('\n'):
			parts = line.split('=>')
			dll_name = parts[0].strip()
			dll_info = parts[1].strip()
			
			if 'not found' not in dll_info:
				info_parts = dll_info.split('(')
				dll_path = info_parts[0].strip()
			
				dlls[dll_name] = dll_path 
			
		for dll in dlls:
			if not Path(dlls[dll]).is_relative_to(bin_path):  # ignore all dlls that aren't in msys2
				continue
			args.append(f'--include-data-files={dlls[dll]}={dll}')
		
sys.argv = sys.argv + args

nuitka.main()
