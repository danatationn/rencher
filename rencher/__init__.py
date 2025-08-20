__version__ = '1.1.0'  # REMEMBER TO CHANGE THIS
__description__ = 'A Ren\'Py game manager, made with DDLC mods in mind'
__url__ = 'https://github.com/danatationn/Rencher'
__issue_url__ = 'https://github.com/danatationn/Rencher/issues'
__copyright__ = '© 2025 danatationn'

import os.path
import platform
import sys
import traceback

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
    pass  # """error"""

def handle_global_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return 
    # if issubclass(exc_type, InvalidGameError):
    #     return
    
    err_message = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    print(err_message, file=sys.stderr)
    
    sys.exit(1)

def launch() -> None:
    sys.excepthook = handle_global_exception
    
    compile_data()

    """
        sourced from nicotine+ ^^
        https://github.com/nicotine-plus/nicotine-plus/blob/master/pynicotine/gtkgui/__init__.py
    """
    if getattr(sys, 'frozen', False):
        executable_folder = os.path.dirname(sys.executable)
        
        os.environ['GTK_EXE_PREFIX'] = executable_folder
        os.environ['GTK_DATA_PREFIX'] = executable_folder
        os.environ['GTK_PATH'] = executable_folder
        os.environ['XDG_DATA_DIRS'] = os.path.join(executable_folder, 'share')
        os.environ['FONTCONFIG_FILE'] = os.path.join(executable_folder, 'share/fonts/fonts.conf')
        os.environ['FONTCONFIG_PATH'] = os.path.join(executable_folder, 'share/fonts')
        os.environ['GDK_PIXBUF_MODULE_FILE'] = os.path.join(executable_folder, 'lib/pixbuf-loaders.cache')
        os.environ['GI_TYPELIB_PATH'] = os.path.join(executable_folder, 'lib/girepository-1.0')
        os.environ['GSETTINGS_SCHEMA_DIR'] = os.path.join(executable_folder, 'share/glib-2.0/schemas')
        print(os.path.join(executable_folder, 'lib/girepository-1.0'))

    # if sys.platform == 'win32':
    #     os.environ['PANGOCAIRO_BACKEND'] = 'fontconfig'
    #     os.environ['GTK_CSD'] = '0'
    #     os.environ['GDK_DISABLE'] = 'gl,vulkan'
    #     os.environ['GSK_RENDERER'] = 'cairo'

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
