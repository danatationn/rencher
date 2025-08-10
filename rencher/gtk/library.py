import glob
import logging
import os.path

from gi.repository import GObject

from rencher import GameInvalidError
from rencher.renpy.config import RencherConfig
from rencher.renpy.game import Game
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
        
        
class RencherLibrary(GObject.Object):
    game_items = {}
    
    __gsignals__ = {
        'game-added': (GObject.SignalFlags.RUN_FIRST, None, (GameItem,)),
        'game-removed': (GObject.SignalFlags.RUN_FIRST, None, (GameItem,)),
        'game-changed': (GObject.SignalFlags.RUN_FIRST, None, (GameItem,)),
    }
    
    def __init__(self):
        super().__init__()
        
    def load_games(self):
        data_dir = RencherConfig().get_data_dir()
        for rpath in glob.iglob(os.path.join(data_dir, 'games', '*')):
            self.add_game(rpath)
        
    def add_game(self, rpath: str):
        try:
            game_item = GameItem(rpath=rpath)
        except GameInvalidError:
            pass
        else:
            self.game_items[game_item.rpath] = game_item
            self.emit('game-added', game_item)
            logging.debug(f'+{game_item.name}')
        
    def remove_game(self, rpath: str):
        game_item = self.game_items.pop(rpath, None)
        if game_item:
            self.emit('game-removed', game_item)
            logging.debug(f'-{game_item.name}')
            
    def change_game(self, rpath: str):
        if rpath in self.game_items:
            self.emit('game-changed', self.game_items[rpath])
            logging.debug(f'~{self.game_items[rpath].name}')