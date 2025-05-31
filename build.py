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

ui_path = Path(__file__).parent / 'src' / 'gtk' / 'ui'
main_path = Path(__file__).parent / 'main.py'
yaml_path = Path(__file__).parent / 'build.yml'
pyproject_path = Path(__file__).parent / 'pyproject.toml'

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

if '24.04.2-Ubuntu' not in platform.uname().version:
	# 24.04 does not have adw 1.6 which has buttonrows . 
	blp2ui()

if platform.system() == 'Windows':
	process = subprocess.run(
		['cygpath', '-m', '/ucrt64/bin/'],
		capture_output=True,
		text=True,
		check=True)
	bin_path = Path(process.stdout.strip())

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
			['ntldd', '-R', dll_name],
			capture_output=True,
			text=True,
			check=True)
		output = result.stdout.strip()
		dlls = {}
	
		for line in output.split('\n'):
			parts = line.split('=>')
			dll_name = parts[0].strip()
			dll_info = parts[1].strip()
			
			if 'not found' not in dll_info:
				info_parts = dll_info.split('(')
				dll_path = info_parts[0].strip()
			
				dlls[dll_name] = Path(dll_path) 
			
		for dll in dlls:
			if not dlls[dll].is_relative_to(bin_path):  # ignore all dlls that aren't in msys2
				continue
			args.append(f'--include-data-files={dlls[dll]}={dll}')
		
sys.argv = sys.argv + args

nuitka.main()
