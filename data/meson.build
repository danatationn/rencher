desktop = configure_file(
	input: app_id + '.desktop.in',
	output: app_id + '.desktop',
	configuration: conf,
	install: true,
	install_dir: join_paths(get_option('datadir'), 'applications'),
	install_mode: 'rwxr-xr-x'
)

blueprint = custom_target('blueprint',
	input: files(
		'ui/import.blp',
		'ui/options.blp',
		'ui/settings.blp',
		'ui/shortcuts.blp',
		'ui/tasks_popover.blp',
		'ui/tasks_row.blp',
		'ui/window.blp'
	),
	output: '.',
	build_always_stale: true,
	build_by_default: true,
	command: [find_program('blueprint-compiler'), 'batch-compile', '@OUTPUT@', '@CURRENT_SOURCE_DIR@', '@INPUT@'],
)

icon_conf = configure_file(
	input: 'assets/rencher-icon.svg',
	output: conf.get('app_id') + '.svg',
	copy: true
)
install_data(
	icon_conf,
	install_dir: join_paths(get_option('datadir'), 'icons/hicolor/scalable/apps'),
)

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
