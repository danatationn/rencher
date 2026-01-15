project('rencher', version: '1.2.0')

python = import('python')
gnome = import('gnome')

blueprint_compiler = find_program('blueprint-compiler', required: true)

py_install = python.find_installation('python3')
if not py_install.found()
	error('no python')
endif
if not py_install.language_version().version_compare('>=3.12')
	error('out of date python3 (<3.12)')
endif

py_dir = py_install.get_install_dir()
system = host_machine.system()
if system == 'linux'
	prefix = get_option('prefix')  # /usr
	bin_dir = get_option('bindir')  # /bin
	data_dir = get_option('datadir')  # /share
	pkg_data_dir = join_paths(prefix, data_dir, meson.project_name())  # /usr/share/rencher
elif system == 'windows'
	error('wip')
else
	error('not yet supported')
endif

install_subdir(meson.project_name(), install_dir: py_dir)
message(py_dir)

gnome.post_install(gtk_update_icon_cache: true)
