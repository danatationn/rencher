import logging
import os
import sys

from gi.repository import GLib
from watchdog.events import (
    DirCreatedEvent,
    DirDeletedEvent,
    DirModifiedEvent,
    DirMovedEvent,
    FileClosedEvent,
    FileCreatedEvent,
    FileDeletedEvent,
    FileModifiedEvent,
    FileMovedEvent,
    FileOpenedEvent,
    FileSystemEvent,
    FileSystemEventHandler,
)
from watchdog.observers import Observer

from rencher import config_path, local_path
from rencher.gtk.library import GameItem
from rencher.gtk.window import RencherWindow
from rencher.renpy.config import RencherConfig


class RencherFileMonitor(FileSystemEventHandler):
    """
        watch over rencher files and act accordingly
        
        rencher config:
            * when updated reset the observer so it checks the new data directory
        data directory:
            * if something got updated in the running game, add the event to a queue
            * after the game stops, sort the queue out
    """
    
    window: RencherWindow = None
    config: RencherConfig = RencherConfig()
    observer: Observer = None
    data_dir: str

    def __init__(self, window: RencherWindow):
        super().__init__()
        self.window = window
        self.monitor_data_dir()

    def monitor_data_dir(self) -> None:
        if self.observer is not None:
            self.observer.stop()

        if not os.path.isdir(local_path):
            self.config.write()  # automatically makes the dir and config
        self.data_dir = self.config.get_data_dir()
        if not os.path.isdir(self.data_dir):
            os.mkdir(self.data_dir)

        self.observer = Observer()
        self.observer.schedule(self, config_path)
        self.observer.schedule(self, self.data_dir, recursive=True)
        self.observer.start()
        logging.debug(f'Watching "{self.data_dir}/" for changes')
    
    def on_moved(self, event: DirMovedEvent | FileMovedEvent) -> None:
        logging.debug(f'something got moved {event.src_path} -> {event.dest_path}')
        self.emit_changed(event.dest_path)
            
    def on_deleted(self, event: DirDeletedEvent | FileDeletedEvent) -> None:
        if os.path.exists(event.src_path):
            # this means it *actually* got edited
            # idk either ok??
            self.on_closed(event)
        else:
            ...
        
    def on_closed(self, event: FileClosedEvent | DirDeletedEvent | FileDeletedEvent) -> None:
        if event.src_path == config_path:
            self.monitor_data_dir()
        else:
            ...

    def get_game_item(self, path: str) -> GameItem | None:
        for rpath, game_item in self.window.library.game_items.items():
            if path.startswith(rpath + os.sep):
                return game_item
        return None
        
    def on_modified(self, event: DirModifiedEvent | FileModifiedEvent) -> None:
        self.emit_changed(event.src_path)
    
    def emit_changed(self, path: str) -> None:
        game_item = self.get_game_item(path)
        if game_item:
            if game_item.game.is_valid:
                self.window.library.change_game(game_item.rpath)
            else:
                self.window.library.remove_game(game_item.rpath)
        else:
            games_dir = os.path.join(self.data_dir, 'games')
            rel_path = os.path.relpath(path, games_dir)
            top_dir = rel_path.split(os.sep, 1)[0]
            rpath = os.path.join(games_dir, top_dir)
            self.window.library.add_game(rpath)