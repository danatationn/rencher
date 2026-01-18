project('rencher', version: '1.2.1')

name = 'Rencher'
app_id = 'com.github.danatationn.Rencher'
description = 'A Ren\'Py mod manager, made with DDLC mods in mind'

pkgdata_dir = join_paths(
	get_option('prefix'),
	get_option('datadir'),
	meson.project_name()
)

python = import('python')
gnome = import('gnome')
python3 = python.find_installation('python3')

conf = configuration_data()
conf.set('name', name)
conf.set('project_name', meson.project_name())
conf.set('app_id', app_id)
conf.set('pkgdata_dir', pkgdata_dir)
conf.set('description', description)
conf.set('bin_dir', join_paths(get_option('prefix'), get_option('bindir')))
conf.set('python_dir', join_paths(get_option('prefix'), python3.get_install_dir()))

subdir('data')
subdir('rencher')
install_subdir(meson.project_name(), install_dir: python3.get_install_dir())

gnome.post_install(
	# gtk_update_icon_cache: true,
	update_desktop_database: true,
)
