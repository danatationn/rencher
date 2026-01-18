configure_file(
	input: app_id + '.desktop.in',
	output: app_id + '.desktop',
	configuration: conf,
	install: true,
	install_dir: join_paths(get_option('datadir'), 'applications')
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
