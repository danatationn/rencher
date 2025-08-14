import glob
import os
from functools import lru_cache


# @lru_cache
def get_py_files(apath: str) -> list[str]:
    return glob.glob(os.path.join(apath, '*.py'))

@lru_cache
def get_rpa_files(rpath: str) -> list[str]:
    rp_files = glob.glob(os.path.join(rpath, '**/*.rp*'), recursive=True)

    game_files = [
        rp_file for rp_file in rp_files
        if '00' not in os.path.splitext(rp_file)[0]  # generic engine file
        if '.rpym' not in os.path.splitext(rp_file)[1]  # .rpym files can be compiled (.rypmc)
        if os.path.splitext(rp_file)[1] != '.rpyb'  # cache file
    ]

    return game_files
 
def get_rpa_path(rpath: str) -> str | None:
    game_files = get_rpa_files(rpath)
    
    if not game_files:
        return None
    
    # some mods apparently store ren'py files in lib/
    # those are further nested inside the game so just try and get the top folder
    rpa_path = min(game_files, key=lambda path: len(path.split(os.sep)))
    return os.path.dirname(rpa_path)
 
def get_absolute_path(rpath: str) -> str | None:
    try:
        return os.path.dirname(get_rpa_path(rpath))
    except IndexError:
        return None
    except TypeError:
        return None

def validate_game_files(files: list[str]) -> bool:
    """
    a quick validation function, to be used before importing games
    
    Args:
        files: the list of files
    Returns:
        true if it's a valid game, false if it's not
    """
    if not files:
        return False

    rp_files = [file for file in files if '.rp' in os.path.splitext(file)[1]]
    game_files = [
        rp_file for rp_file in rp_files
        if '00' not in os.path.splitext(rp_file)[0]  # generic engine file
        if '.rpym' not in os.path.splitext(rp_file)[1]  # .rpym files can be compiled (.rypmc)
        if os.path.splitext(rp_file)[1] != '.rpyb'  # cache file
    ]
    if not game_files:
        return False

    rpa_path = min(game_files, key=lambda path: len(path.split(os.sep)))
    apath = os.path.abspath(os.path.join(rpa_path, '..', '..'))
    rel_files = [os.path.relpath(file, apath) for file in files]

    required_folders = [file for file in rel_files
                        if len(file.split(os.sep)) == 1
                        if file in ['game', 'lib', 'renpy']]
    if len(required_folders) != 3:
        return False

    game_scripts = [file for file in rel_files
                    if len(file.split(os.sep)) == 1
                    if os.path.splitext(file)[1] == '.py']
    if not game_scripts:
        return False

    game_files = [file for file in rel_files
                  if os.path.commonpath(['game', file])
                  if os.path.splitext(file)[1] == '.rpa']
    if not game_files:
        return False

    engine_files = [file for file in rel_files
                    if os.path.commonpath(['renpy', file])
                    if os.path.splitext(file)[1] in ['.py', '.pyo', '.pyx', '.rpym', '.rpymc']]
    if not engine_files:
        return False
    
    return True
