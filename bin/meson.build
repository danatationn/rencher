configure_file(
	input: meson.project_name() + '.in',
	output: meson.project_name(),
	configuration: conf,
	install: true,
	install_dir: get_option('bindir'),
	install_mode: 'rwxr-xr-x'
)

run_target('run', command: [meson.project_build_root() / 'bin' / meson.project_name()])
run_target('dev', command: [join_paths(meson.project_build_root(), 'bin', meson.project_name()), '--verbose'])
