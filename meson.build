project('rencher', version: '1.2.1')

name = 'Rencher'
app_id = 'com.github.danatationn.rencher'
description = 'A Ren\'Py mod manager, made with DDLC mods in mind'

pkgdata_dir = join_paths(
	get_option('prefix'),
	get_option('datadir'),
	meson.project_name()
)

python = import('python')
python_install = python.find_installation()
gnome = import('gnome')

# conf
conf = configuration_data()
conf.set('name', name)
conf.set('project_name', meson.project_name())
conf.set('version', meson.project_version())
conf.set('copyright', '© 2026 danatationn')
conf.set('app_id', app_id)
conf.set('pkgdata_dir', pkgdata_dir)
conf.set('description', description)
conf.set('bin_dir', join_paths(get_option('prefix'), get_option('bindir')))
conf.set('python_dir', join_paths(get_option('prefix'), python_install.get_install_dir()))

# install
subdir('rencher')
subdir('data')
subdir('bin')
install_subdir(meson.project_name(), install_dir: python_install.get_install_dir())
gnome.post_install(
	gtk_update_icon_cache: true,
	update_desktop_database: true,
)

# appimage
appimagetool = find_program('appimagetool', required: false)
if appimagetool.found()
	run_target('appimage',
		command: ['sh', '-c',
			'''
			cp -r @0@/.venv/lib/python*/site-packages/. $1/lib/python3.14/site-packages/ &&
			cp @1@ $1/AppRun &&
			chmod +x $1/AppRun &&
			cp @2@ $1/rencher-icon.svg &&
			cp @3@ $1/rencher.desktop &&
			ARCH=$(uname -m) @4@ $1 $1/../Rencher.AppImage
			'''.format(
				meson.current_source_dir(),
				meson.current_source_dir() / 'data/AppRun',
				meson.current_source_dir() / 'data/assets/rencher-icon.svg',
				meson.current_build_dir() / 'data' / app_id + '.desktop',
				appimagetool.full_path(),
			),
			'sh', get_option('prefix'),
		]
	)
endif
