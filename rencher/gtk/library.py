import asyncio
import logging
import os.path
import pickle
from pathlib import Path
from typing import TYPE_CHECKING

from gi.repository import GObject

from rencher.gtk.game_item import GameItem
from rencher.renpy.config import RencherConfig
from rencher.renpy.game import GameInvalidError, GameNoExecutableError

if TYPE_CHECKING:
    from rencher.gtk.window import RencherWindow


class RencherLibrary(GObject.Object):
    game_items: dict[str, GameItem] = {}
    window: 'RencherWindow'

    __gsignals__ = {
        'game-added': (GObject.SignalFlags.RUN_FIRST, None, (GameItem,)),
        'game-removed': (GObject.SignalFlags.RUN_FIRST, None, (GameItem,)),
        'game-changed': (GObject.SignalFlags.RUN_FIRST, None, (GameItem,)),
    }

    def __init__(self, window: 'RencherWindow'):
        super().__init__()
        self.window = window

    def load_games(self) -> None:
        data_dir = RencherConfig().get_data_dir()
        games_dir = Path(data_dir) / 'games'
        games_dir.mkdir(exist_ok=True, parents=True)
        for rpath in dict(self.game_items):
            self.remove_game(rpath)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        for d in games_dir.iterdir():
            rpath = os.path.join(games_dir, d)
            loop.run_in_executor(None, self.add_game, rpath)

    def make_cache(self) -> None:
        data_dir = RencherConfig().get_data_dir()
        cache_dir = os.path.join(data_dir, 'cache')
        library_cache = os.path.join(cache_dir, 'library.pickle')
        os.makedirs(cache_dir, exist_ok=True)
        with open(library_cache, 'wb') as f:
            pickle.dump(self.game_items, f)

    def load_cache(self) -> None:
        data_dir = RencherConfig().get_data_dir()
        cache_dir = os.path.join(data_dir, 'cache')
        library_cache = os.path.join(cache_dir, 'library.pickle')
        try:
            with open(library_cache, 'rb') as f:
                data = pickle.load(f)
        except FileNotFoundError:
            logging.debug('cache not found')
        except EOFError:
            pass
        # except pickle.UnpicklingError:
        #     logging.debug('unpickling error')
        else:
            for rpath, game_item in data.items():
                logging.debug(f'{rpath=} {game_item=}')
                logging.debug(game_item.__dict__)
                self.game_items[rpath] = game_item
                self.emit('game-added', game_item)
                logging.debug(f'p+{game_item.name}')

    def add_game(self, rpath: str) -> None:
        try:
            game_item = GameItem(rpath=rpath)
        except GameInvalidError:
            pass
        except GameNoExecutableError:
            self.window.codename_dialog.popup(rpath)
        else:
            if rpath not in self.game_items:
                self.game_items[rpath] = game_item
                self.emit('game-added', game_item)
                logging.debug(f'+{game_item.name}')
            else:
                self.change_game(rpath)

    def remove_game(self, rpath: str) -> None:
        game_item = self.game_items.pop(rpath, None)
        self.emit('game-removed', game_item)
        if game_item:
            logging.debug(f'-{game_item.name}')

    def change_game(self, rpath: str) -> None:
        if rpath in self.game_items:
            self.emit('game-changed', self.game_items[rpath])
            logging.debug(f'~{self.game_items[rpath].name}')

    def get_game(self, rpath: str) -> GameItem | None:
        if rpath in self.game_items:
            return self.game_items[rpath]
        return None
