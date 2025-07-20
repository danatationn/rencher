from rencher.renpy.config import GameConfig
from rencher.renpy.game import Game


class Mod(Game):
    # TODO remove
    
    name: str = None
    codename: str = None
    rpath: str = None
    apath: str = None
    version: str = None
    config: GameConfig = None