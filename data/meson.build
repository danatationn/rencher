### METAINFO ###
if host_machine.system() == 'linux'
	install_data(
	'com.github.danatationn.rencher.metainfo.xml',
		install_dir: get_option('datadir') / 'metainfo'
	)
endif

### DESKTOP FILE ###
desktop = configure_file(
	input: app_id + '.desktop.in',
	output: app_id + '.desktop',
	configuration: conf,
	install: true,
	install_dir: join_paths(get_option('datadir'), 'applications'),
	install_mode: 'rwxr-xr-x'
)

### UI FILES ###
blueprint = custom_target('blueprint',
	input: files(
		'ui/import.blp',
		'ui/options.blp',
		'ui/settings.blp',
		'ui/shortcuts.blp',
		'ui/window.blp',
		'ui/game_page.blp',
	),
	output: '.',
	build_always_stale: true,
	build_by_default: true,
	command: [python_install, find_program('blueprint-compiler').full_path(), 'batch-compile', '@OUTPUT@', '@CURRENT_SOURCE_DIR@', '@INPUT@'],
)

### ICONS ###
icon_dirs = [
	'16x16', '32x32', '48x48', '64x64', '128x128', '256x256'
]
icon_name = '@0@.png'.format(conf.get('app_id'))

foreach dir : icon_dirs
	install_data(
		join_paths(
		    'icons',
		    dir,
			'apps',
			icon_name
		),
		install_dir: join_paths(
			get_option('datadir'),
			'icons/hicolor',
			dir,
			'apps'
		),
	)
endforeach

### GRESOURCE ###
gnome.compile_resources(app_id,
	configure_file(
		input: app_id + '.gresource.xml.in',
		output: app_id + '.gresource.xml',
		configuration: conf
	),
	gresource_bundle: true,
	dependencies: blueprint,
	install: true,
	install_dir: pkgdata_dir
)
