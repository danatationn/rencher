from cx_Freeze import setup, Executable

build_options = {'packages': [], 'excludes': []}
base = 'gui'
executables = [
	Executable('rencher.py', base=base, target_name='rencher')
]

setup(name='Rencher',
      version = '1.1.0',
      description = "A Ren'Py game manager, made with DDLC mods in mind",
      options = {'build_exe': build_options},
      executables = executables)
