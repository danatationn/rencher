"""
    HEAVILY inspired by the Nicotine+ cxfreeze script:
    https://github.com/nicotine-plus/nicotine-plus/blob/master/build-aux/windows/setup.py
"""

import os
import platform
import shutil
import sys
from pathlib import Path
from pprint import pprint

from cx_Freeze import Executable, setup

TYPELIB_PREFIXES = ['Gtk-4', 'Gio-', 'Gdk-4', 'GLib-', 'Gsk-', 'GObject-', 'GModule-', 'GdkPixbuf-',
                    'Adw-', 'Graphene-', 'HarfBuzz-', 'Pango-', 'PangoCairo-', 'cairo-', 'freetype2-'
                    'GdkWin32-4' if platform.system == 'Windows' else None,
                    'Win32-' if platform.system == 'Windows' else None]
base_prefix = Path(sys.base_prefix)  # /usr
lib_dir = base_prefix / 'bin' if platform.system == 'Windows' else base_prefix / 'lib'
lib_ext = '.dll' if platform.system == 'Windows' else '.so'
gui = 'Win32GUI' if platform.system == 'Windows' else 'gui'

ldd_path = ''
if platform.system() == 'Linux':
    ldd_path = shutil.which('ldd')
elif platform.system() == 'Windows':
    ldd_path = shutil.which('ntldd')
else:
    raise NotImplementedError('Your OS is not currently supported')
if not ldd_path:
    raise FileNotFoundError('ldd was not found in path (not installed?)')

pkgconf_path = shutil.which('pkg-config')
if not pkgconf_path:
    raise FileNotFoundError('pkg-config was not found in path (not installed?)')

def find_files(pattern: str, search_path: Path | str, dest_path: Path | str = Path(), recursive: bool = False) -> list:
    source_files = []
    files: list[tuple[Path, Path]] = []

    if isinstance(search_path, str):
        search_path = Path(search_path)
    if isinstance(dest_path, str):
        dest_path = Path(dest_path)

    if '*' in pattern:
        if recursive:
            source_files = search_path.rglob(pattern)
        else:
            source_files = search_path.glob(pattern)
    elif (source_file := Path(search_path / pattern)).is_file():
        source_files.append(source_file)
    else:
        return []

    for source_file in source_files:
        if dest_path == Path('.') and source_file.is_relative_to(base_prefix):
            target_file = source_file.relative_to(base_prefix)
            files.append((source_file, target_file))
        else:
            target_file = dest_path / source_file.relative_to(search_path)
            files.append((source_file, target_file))

    return files

def freeze(argv: list[str]):
    include_files: list[tuple[Path, Path]] = []
    if len(argv) == 1:
        print('No build dir specified!')
        return
    if not os.path.isdir(argv[1]):
        print(f'"{argv[1]}" is not a directory!')
        return

    # setup() requires the first argument to be 'build'
    build_dir = Path(argv[1], f'lib/python{sys.version_info.major}.{sys.version_info.minor}/site-packages/rencher/__init__.py')
    argv[1] = 'build'

    if platform.system == 'Windows':
        include_files.extend(find_files('gdbus.exe', lib_dir))
        include_files.extend(find_files('gdbus.exe', lib_dir))

    include_files.extend(find_files('*.conf', '/etc/fonts/', '', True))
    include_files.extend(find_files('libgtk-4*', lib_dir))
    include_files.extend(find_files('libadwaita-1*', lib_dir))
    include_files.extend(find_files('gschemas.compiled', base_prefix / 'share/glib-2.0/schemas'))

    for prefix in TYPELIB_PREFIXES:
        include_files.extend(find_files(f'{prefix}*.typelib', base_prefix / 'lib/girepository-1.0'))

    include_files.extend(find_files('pixbuf-loaders.cache', base_prefix / 'lib/gdk-pixbuf-2.0/2.10.0/'))

    setup(
        name='Rencher',
        description='Rencher',
        version=1,
        options={
            'build': {
                'build_base': Path(__file__).parent / 'build',
            },
            'build_exe': {
                'packages': [],
                'excludes': [],
                'optimize': 2,
                'include_files': include_files,
                'include_msvcr': True,
            },
        },
        executables=[
            Executable(
                base=gui,
                script=build_dir,
                target_name='rencher',
                # icon=icon_path,
                # copyright=rencher.__copyright__,
            ),
        ],
    )

if __name__ == '__main__':
    freeze(sys.argv)
