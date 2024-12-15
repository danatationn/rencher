import sys
from pathlib import Path

from src.mods import Game, Mod


if __name__ == '__main__':
	game = Game(name='Hydrangea-1.5.1-pc')
	print(game.version)
	print(game.codename)

	print('\n')

	mod = Mod(name='A Date With Monika')
	print(mod.apath)
	print(mod.version)
	print(mod.codename)
	print(mod.is_independent)

	mod.run()