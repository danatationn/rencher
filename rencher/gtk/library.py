import glob
import logging
import os.path
from typing import TYPE_CHECKING

from gi.repository import GObject

from rencher import GameInvalidError, GameNoExecutableError
from rencher.gtk.game_item import GameItem
from rencher.renpy.config import RencherConfig

if TYPE_CHECKING:
    from rencher.gtk.window import RencherWindow

class RencherLibrary(GObject.Object):
    game_items = {}
    window: 'RencherWindow'
    
    __gsignals__ = {
        'game-added': (GObject.SignalFlags.RUN_FIRST, None, (GameItem,)),
        'game-removed': (GObject.SignalFlags.RUN_FIRST, None, (GameItem,)),
        'game-changed': (GObject.SignalFlags.RUN_FIRST, None, (GameItem,)),
    }
    
    def __init__(self, window):
        super().__init__()
        self.window = window
        
    def load_games(self) -> None:
        data_dir = RencherConfig().get_data_dir()
        for rpath in glob.iglob(os.path.join(data_dir, 'games', '*')):
            self.add_game(rpath)
        
    def add_game(self, rpath: str) -> None:
        try:
            game_item = GameItem(rpath=rpath)
        except GameInvalidError:
            pass
        except GameNoExecutableError:
            self.window.codename_dialog.popup(rpath)
        else:
            self.game_items[game_item.rpath] = game_item
            self.emit('game-added', game_item)
            logging.debug(f'+{game_item.name}')
        
    def remove_game(self, rpath: str) -> None:
        game_item = self.game_items.pop(rpath, None)
        if isinstance(game_item, GameItem):  # if i don't do this my type checker will tell me the code is unreachable
            self.emit('game-removed', game_item)
            logging.debug(f'-{game_item.name}')
            
    def change_game(self, rpath: str) -> None:
        if rpath in self.game_items:
            self.emit('game-changed', self.game_items[rpath])
            logging.debug(f'~{self.game_items[rpath].name}')