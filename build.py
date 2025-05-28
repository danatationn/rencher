import platform
import subprocess
import sys
from pathlib import Path

from src.gtk import blp2ui
from nuitka import __main__ as nuitka

blp2ui()
ui_path = Path(__file__).parent / 'src' / 'gtk' / 'ui'
main_path = Path(__file__).parent / 'main.py'
yaml_path = Path(__file__).parent / 'build.yml'
bin_path = Path('C:/msys64/ucrt64/bin/')  # windows/msys2 

args = [
	f'--main={main_path}',
	'--standalone',
	# '--onefile',
	f'--include-data-dir={ui_path}=src/gtk/ui',
	# f'--user-package-configuration-file={yaml_path}',
	'--assume-yes-for-downloads'
]

if platform.system() == 'Windows':
	while not bin_path.is_dir():
		input_path = input('MSYS2 could not be found.\nPlease enter its path. ')
		bin_path = Path(input_path) / 'ucrt64' / 'bin'

	args.append('--include-module=gi._enum')

	required_ddls = [
		'libadwaita-1-0.dll',
		'libgtk-4-1.dll',
		'libappstream-5.dll',
		'libfreetype-6.dll',
		'libidn2-0.dll',
		'libpsl-5.dll',
		'libthai-0.dll',
	]

	for dll in required_ddls:
		if not Path(bin_path / dll).exists():
			msg = f'{dll} was not found. Please install it and try again.'
			FileNotFoundError(msg)

	ntldd_path = bin_path / 'ntldd.exe'
	if not ntldd_path.exists():
		msg = 'ntldd is not installed. Please install it and try again.'
		FileNotFoundError(msg)
		
	def ntldd_dlls(dll_name: str) -> dict:
		result = subprocess.run([ntldd_path, dll_name], capture_output=True, text=True, check=True)
		output = result.stdout.strip()
		dlls = {}
	
		for line in output.split('\n'):
			parts = line.split('=>')
			dll_name = parts[0].strip()
			dll_info = parts[1].strip()
			
			info_parts = dll_info.split('(')
			dll_path = info_parts[0].strip()
			
			dlls[dll_name] = dll_path 
	
		for dll in dlls:
			if 'lib' not in dlls[dll]:
				continue
			args.append(f'--include-data-files={dlls[dll]}={dll}')
			
		return dlls

	dlls = []
	for dll_name in required_ddls:
		result = ntldd_dlls(dll_name)
		for dll in result:
			dlls.append(result[dll])
		

sys.argv = sys.argv + args

nuitka.main()
