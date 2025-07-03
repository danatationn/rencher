# most of this was stolen from apostrophe
# https://gitlab.gnome.org/World/apostrophe/-/blob/main/meson.build?ref_type=heads
# check the app out it's reall good

project (
	'Rencher',
	version: 'dev'
)

if host_machine.system() == 'windows'
	error('You need MSYS2 to build Rencher on Windows! (https://www.msys2.org/)')
endif
if host_machine.system() == 'darwin'
	error('Rencher doesn\'t support Darwin right now!')
endif

fs = import('fs')
gnome = import('gnome')
python = import('python')

py_installation = python.find_installation('python3')

dependency('glib-2.0')
dependency('gobject-2.0')
dependency('gobject-introspection-1.0')
dependency('gtk4', version: '>= 4.0.0')
dependency('libadwaita-1', version: '>= 1.6')

find_program('glib-compile-schemas', required: true)
find_program('blueprint-compiler', required: true)
wget = find_program('wget', required: true)
unzip = find_program('unzip', required: true)

pyoxidizer_urls = {
	'linux-x86_64': 'https://nightly.link/ntamas/PyOxidizer/workflows/pyoxidizer/main/exe-pyoxidizer-x86_64-unknown-linux-musl.zip',
	'linux-aarch64': 'https://nightly.link/ntamas/PyOxidizer/workflows/pyoxidizer/main/exe-pyoxidizer-aarch64-unknown-linux-musl.zip',
	'cygwin-x86_64': 'https://nightly.link/ntamas/PyOxidizer/workflows/pyoxidizer/main/exe-pyoxidizer-x86_64-pc-windows-msvc.zip',
	'cygwin-i686': 'https://nightly.link/ntamas/PyOxidizer/workflows/pyoxidizer/main/exe-pyoxidizer-i686-pc-windows-msvc.zip'
}
system = host_machine.system() + '-' + host_machine.cpu_family()
assert(pyoxidizer_urls.has_key(system), 'Rencher is not supported for your system (' + system + ')')
url = pyoxidizer_urls[system]

if host_machine.system() == 'cygwin'
	output = 'pyoxidizer.exe'
else
	output = 'pyoxidizer'
endif

download = custom_target(
	'download-zip',
	output: 'pyoxidizer.zip',
	command: [wget, '-O', '@OUTPUT@', url],
	build_by_default: true
)
extract = custom_target(
	'extract-zip',
	input: download,
	output: output,
	command: [unzip, '-o', '@INPUT@'],
	build_by_default: true
)
pyoxidizer = find_program(meson.current_build_dir() / 'pyoxidizer', required: true)

root = fs.parent(meson.current_build_dir())

build = custom_target(
	'build-rencher',
	command: [pyoxidizer, 'build', '--path', root],
	output: 'enis',
	build_by_default: true
)