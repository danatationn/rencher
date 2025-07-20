import logging

from gi.repository import GObject

from rencher.renpy import Game
from rencher.renpy.paths import get_absolute_path


class GameItem(GObject.Object):
    """
        used mostly for binding labels and shi
    
        uhh
    """
    __gtype_name__ = 'GameItem'
    _game: Game
    name = GObject.Property(type=str)
    rpath = GObject.Property(type=str)
    apath = GObject.Property(type=str)
    last_played = GObject.Property(type=str)
    playtime = GObject.Property(type=str)
    added_on = GObject.Property(type=str)
    version = GObject.Property(type=str)
    codename = GObject.Property(type=str)

    def __init__(self, rpath: str = None, game: Game = None):
        super().__init__()

        apath = get_absolute_path(rpath)
        if game and rpath and game.apath != apath:
            raise Exception('wtf')
        
        if game and not rpath:
            rpath = game.rpath
        if rpath and not game:
            game = Game(rpath=rpath)

        self.game = game
        
    def refresh(self):
        self.game.config.read()
        self.name = self.game.get_name()
        self.rpath = self.game.rpath
        self.apath = self.game.apath
        self.last_played = self.game.config.get_value('last_played')
        self.added_on = self.game.config.get_value('added_on')
        self.playtime = self.game.config.get_value('playtime')
        self.version = self.game.get_renpy_version()
        self.codename = self.game.get_codename()
        
    @property
    def game(self) -> Game:
        return self._game
    @game.setter
    def game(self, value: Game):
        self._game = value
        self.refresh()
        
    
if __name__ == '__main__':
    game_item = GameItem(rpath='/home/dan/.local/share/rencher/games/BreakAndEnter-1.0.2-Renpy7Mod')
    value = game_item.rpath
    print(value)