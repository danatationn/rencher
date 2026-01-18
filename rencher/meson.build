configure_file(
	input: meson.project_name() + '.in',
	output: meson.project_name(),
	configuration: conf,
	install: true,
	install_dir: get_option('bindir')
)

configure_file(
	input: '__init__.py' + '.in',
	output: '__init__.py',
	configuration: conf,
	install: true,
	install_dir: join_paths(python3.get_install_dir(), 'rencher')
)

run_target('run', command: join_paths(meson.project_build_root(), 'rencher', meson.project_name()))
