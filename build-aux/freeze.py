"""
    HEAVILY inspired by the nicotine+ cxfreeze script:
    https://github.com/nicotine-plus/nicotine-plus/blob/master/build-aux/windows/setup.py
"""

import glob
import os.path
import sys
import tempfile

from cx_Freeze import Executable, setup

# try:
#     from cx_Freeze.hooks import gi  # pylint: disable=import-error
# except ImportError:
#     from cx_Freeze.hooks import _gi_ as gi  # pylint: disable=import-error,import-private-name
# 
# del gi.load_gi

cwd = os.path.dirname(os.path.abspath(__file__))
tmp_path = os.path.abspath(os.path.dirname(cwd))
sys.path.append(tmp_path)
import rencher  # noqa: E402

include_files = []
def add_files(name: str, search_dir: str, target_dir: str) -> None:
    if '*' in name:
        paths = glob.glob(os.path.join(search_dir, name), recursive=True)
    else:
        paths = [os.path.join(search_dir, name)]
    
    for path in paths:
        if os.path.isfile(path):
            rel_path = os.path.relpath(path, start=search_dir)
            dest_path = os.path.join(target_dir, rel_path)
            include_files.append((path, dest_path)) 
        else:
            raise FileNotFoundError(f'{path} could\'nt be found')

def main():
    if sys.platform == 'win32':
        ext = '.dll'
        lib_dir = os.path.join(sys.base_prefix, 'bin')
        add_files('gdbus.exe', lib_dir, 'lib')
    else:
        ext = '.so'
        lib_dir = os.path.join(sys.base_prefix, 'lib')
        
    add_files('libgtk-4*'+ext, lib_dir, 'lib')
    add_files('libadwaita-1*'+ext, lib_dir, 'lib')
    add_files('gschemas.compiled', os.path.join(sys.base_prefix, 'share/glib-2.0/schemas'), 'lib/schemas')
    add_files('**/*.conf', os.path.join(sys.base_prefix, 'etc/fonts'), 'share/fonts')
    typelibs = [
        "Adw-",
        "Gtk-4",
        "Gio-",
        "Gdk-4",
        "GLib-",
        "Graphene-",
        "Gsk-",
        "HarfBuzz-",
        "Pango-",
        "PangoCairo-",
        "GObject-",
        "GdkPixbuf-",
        "cairo-",
        "GModule-",
        "freetype2-",
    ]
    if sys.platform == 'win32':
        typelibs.append('GdkWin32-4')
        typelibs.append('Win32-')
    
    for typelib in typelibs:
        add_files(typelib+'*.typelib', os.path.join(sys.base_prefix, 'lib/girepository-1.0'), 'lib/girepository-1.0')
        
    loaders_path = 'lib/gdk-pixbuf-2.0/2.10.0/loaders.cache'
    temp_loaders_path = os.path.join(tempfile.mkdtemp(), 'pixbuf-loaders.cache')
    
    # if it wasn't for nicotine+ i wouldn't have ever fucking figured this out 🥹🥹
    with open(temp_loaders_path, 'w') as temp_loaders_f, \
        open(os.path.join(sys.base_prefix, loaders_path)) as loaders_f:
        data = loaders_f.read()
        
        if sys.platform == 'win32':
            data = data.replace('lib\\\\gdk-pixbuf-2.0\\\\2.10.0\\\\loaders', 'lib')
        temp_loaders_f.write(data)
        
    add_files('pixbuf-loaders.cache', os.path.dirname(temp_loaders_path), 'lib')
    add_files(f'*{ext}', os.path.join(sys.base_prefix, 'lib/gdk-pixbuf-2.0/2.10.0/loaders'), 'lib')
            
if __name__ == '__main__':
    main()

setup(
    name='Rencher',
    version=rencher.__version__,
    description=rencher.__description__,
    options={
        'build_exe': {
            'packages': [],
            'excludes': [],
            'optimize': 2,
            'include_files': include_files,
        },
    },
    executables=[
        Executable(
            script='rencher.py',
            base='gui',
            target_name='rencher',
            icon=os.path.join(rencher.tmp_path, 'rencher/gtk/res/rencher.svg'),
        ),
    ],
)