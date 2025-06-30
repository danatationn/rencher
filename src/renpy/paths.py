from functools import lru_cache
from pathlib import Path


@lru_cache
def get_rpa_path(rpath: Path) -> Path | None:
	rp_files = list(rpath.rglob('*.rp*'))

	game_files = [
		rp_file for rp_file in rp_files
		if '00' not in rp_file.stem  # generic engine file
		if 'rpym' not in rp_file.suffix  # .rpym files can be compiled (.rypmc)
		if rp_file.suffix != 'rpyb'  # cache file
	]
	
	try:
		return game_files[0].parent
	except IndexError:
		return None

def get_absolute_path(rpath: Path) -> Path | None:
	try:
		return get_rpa_path(rpath).parent	
	except IndexError:
		return None
