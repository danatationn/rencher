__version__ = '1.1.3'  # REMEMBER TO CHANGE THIS
__description__ = 'A Ren\'Py game manager, made with DDLC mods in mind'
__url__ = 'https://github.com/danatationn/Rencher'
__issue_url__ = 'https://github.com/danatationn/Rencher/issues'
__copyright__ = '© 2025 danatationn'

import glob
import os.path
import platform
import shutil
import subprocess
import sys
import traceback
from types import TracebackType

import tendo
from tendo import singleton

from rencher.gtk import compile_data

local_path: str = ''
config_path: str = ''
tmp_path: str = os.path.abspath(os.path.join(__file__, '..', '..'))
home_path: str = os.path.expanduser('~')

if platform.system() == 'Linux':
    local_path = os.path.join(home_path, '.local/share/rencher')
    config_path = os.path.join(home_path, '.config/rencher.ini')
elif platform.system() == 'Windows':
    local_path = os.path.join(home_path, 'AppData/Local/Rencher') 
    config_path = os.path.join(home_path, 'AppData/Local/Rencher/config.ini')


class GameInvalidError(Exception):
    pass
class GameNoExecutableError(Exception):
    pass
class GameItemDateError(Exception):
    pass
class ImportInvalidError(Exception):
    pass
class ImportCorruptArchiveError(Exception):
    pass
class ImportCancelError(Exception):
    pass

def handle_global_exception(exc_type: type[BaseException], exc_value: BaseException, exc_traceback: TracebackType):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    # if issubclass(exc_type, InvalidGameError):
    #     return
    if issubclass(exc_type, tendo.singleton.SingleInstanceException):
        show_err_dialog("There's already an instance of Rencher running!\n"
                        "Close that one first!")
        return

    err_message = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    print(err_message, file=sys.stderr)
    show_err_dialog('Oops! Rencher has crashed!\n'
                    'Please send this error to the developer, along with a description on what you were doing.\n\n'
                    + err_message)

    sys.exit(1)

def show_err_dialog(text: str) -> None:
    if platform.system() != 'Linux':
        return

    zenity_path = shutil.which('zenity')
    kdialog_path = shutil.which('kdialog')
    if zenity_path:
        subprocess.run([zenity_path, '--title=Rencher', '--error', '--no-markup', '--no-wrap', '--text', text])
    elif kdialog_path:
        subprocess.run([kdialog_path, '--title=Rencher', '--error', text])

def launch() -> None:
    sys.excepthook = handle_global_exception
    _ = singleton.SingleInstance()

    compile_data()

    if getattr(sys, 'frozen', False):
        executable_folder = os.path.dirname(sys.executable)

        if platform.system() == 'Linux' and 'APPIMAGE' not in os.environ:
            # appimages are smart and don't complain when the cache has relatives paths !
            loader_files = glob.glob(os.path.join(executable_folder, 'lib', 'libpixbufloader*.so'))
            cache_text = subprocess.run(['gdk-pixbuf-query-loaders', *loader_files], capture_output=True).stdout
            with open(os.path.join(executable_folder, 'lib', 'pixbuf-loaders.cache'), 'wb') as f:
                f.write(cache_text)
        if platform.system() == 'Windows':
            os.environ['GSK_RENDERER'] = 'cairo'

        os.environ['GTK_EXE_PREFIX'] = executable_folder
        os.environ['GTK_DATA_PREFIX'] = executable_folder
        os.environ['GTK_PATH'] = executable_folder
        if os.environ.get('XDG_DATA_DIRS', None) is None:
            os.environ['XDG_DATA_DIRS'] = os.pathsep + os.path.join(executable_folder, 'share')
        else:
            os.environ['XDG_DATA_DIRS'] += os.pathsep + os.path.join(executable_folder, 'share')
        os.environ['FONTCONFIG_FILE'] = os.path.join(executable_folder, 'share/fonts/fonts.conf')
        os.environ['FONTCONFIG_PATH'] = os.path.join(executable_folder, 'share/fonts')
        os.environ['GDK_PIXBUF_MODULE_FILE'] = os.path.join(executable_folder, 'lib/pixbuf-loaders.cache')
        os.environ['GI_TYPELIB_PATH'] = os.path.join(executable_folder, 'lib/girepository-1.0')
        os.environ['GSETTINGS_SCHEMA_DIR'] = os.path.join(executable_folder, 'share/glib-2.0/schemas')

    # ui files get loaded when the import happens
    # we want the ui that we just compiled
    from rencher.gtk.application import RencherApplication  # noqa: E402	
    app = RencherApplication()

    from gi.repository import Gio
    gres_path = os.path.join(tmp_path, 'rencher/gtk/res/resources.gresource')
    res = Gio.resource_load(gres_path)
    res._register()

    try:
        app.run(sys.argv)
    except Exception as err:
        handle_global_exception(type(err), err, err.__traceback__)
