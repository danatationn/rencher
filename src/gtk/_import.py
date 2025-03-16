from pathlib import Path

from src import root_path

import patoolib


def import_game(name: str, path: Path, mod: bool = False):
	if name == '':
		name = path.stem

	if not mod:
		target_path = root_path / 'games' / name
	else:
		target_path = root_path / 'mods' / name

	if patoolib.is_archive(str(path)):
		patoolib.extract_archive(str(path), 0, str(target_path))
