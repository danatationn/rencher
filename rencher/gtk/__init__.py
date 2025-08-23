import glob
import os.path
import platform
import shutil
import subprocess
import sys

import gi

gi.require_version('Gtk', '4.0')
from gi.repository import Gio  # noqa: E402


def return_comp(name: str) -> str:
    if platform.system() == 'Linux':
        comp_path = shutil.which(name)
    else:  # Windows
        result = subprocess.run(
            ['cygpath', '-m', f'/ucrt64/bin/{name}'],
            capture_output=True,
            text=True,
            check=True,
        )
        comp_path = result.stdout.strip()
    if not comp_path:
        raise FileNotFoundError(f'{name} is not installed. Exiting...')

    return comp_path

def compile_data() -> None:
    """
        converts all .blp files in usable .ui files using blueprint-compiler (provided you have it installed)
    """

    if getattr(sys, 'frozen', False):
        return  # you can't build blp files if they don't exist 🤷

    blpc_path = return_comp('blueprint-compiler')
    resc_path = return_comp('glib-compile-resources')

    ui_dir = os.path.join(os.path.dirname(__file__), 'ui')
    
    blp_files = glob.glob(os.path.join(ui_dir, '*.blp'))
    args = ['python', blpc_path, 'batch-compile', ui_dir, ui_dir]

    for file in blp_files:
        args.extend([file])

    print(f'{__file__} {os.path.dirname(__file__)} {ui_dir}')
    print('Compiling .blp files...')
    subprocess.run(args)

    res_dir = os.path.join(os.path.dirname(__file__), 'res')
    xml_file = os.path.join(res_dir, 'resources.gresource.xml')

    print('Compiling resources...')
    subprocess.run([resc_path, xml_file], cwd=res_dir)

def open_file_manager(path: str):
    if platform.system() == 'Linux':
        Gio.AppInfo.launch_default_for_uri('file:///' + path)
    elif platform.system() == 'Windows':
        subprocess.run(['explorer', path.replace('/', '\\')])

def windowficate_file(path: str) -> str:
    """
    returns a file that abides by the windows file naming conventions
    
    Args:
        path (str): is used
    Returns:
        str: the new path
    """
    forbidden_characters = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
    forbidden_names = ['CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 
                       'COM9', 'COM¹', 'COM²', 'COM³', 'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8',
                       'LPT9', 'LPT¹', 'LPT²', 'LPT³']

    new_path = ''
    for character in path:
        if character in forbidden_characters:
            new_path += '_'
        else:
            new_path += character
    if path in forbidden_names:
        raise ValueError()

    return new_path
