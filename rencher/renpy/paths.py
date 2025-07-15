import glob
import os.path
from functools import lru_cache


@lru_cache
def get_rpa_path(rpath: str) -> str | None:
    rp_files = glob.glob(os.path.join(rpath, '**/*.rp*'), recursive=True)

    game_files = [
        rp_file for rp_file in rp_files
        if '00' not in os.path.splitext(rp_file)[0]  # generic engine file
        if '.rpym' not in os.path.splitext(rp_file)[1]  # .rpym files can be compiled (.rypmc)
        if os.path.splitext(rp_file)[1] != '.rpyb'  # cache file
    ]

    try:
        return os.path.dirname(game_files[0])
    except IndexError:
        return None
    except TypeError:
        return None

def get_absolute_path(rpath: str) -> str | None:
    try:
        return os.path.dirname(get_rpa_path(rpath))
    except IndexError:
        return None
    except TypeError:
        return None
