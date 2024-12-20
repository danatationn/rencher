from pathlib import Path


def find_absolute_path(path: Path) -> Path | None:
	rp_files = sorted(path.rglob('*.rp*'))
	game_files = [
		rp_file for rp_file in rp_files
		if '00' not in rp_file.stem  # generic engine file
		if 'rpym' not in rp_file.suffix  # .rpym files can be compiled (.rypmc)
		if rp_file.suffix != 'rpyb'  # cache file
	]

	try:
		return game_files[0].parents[1]
	except IndexError:
		return None
