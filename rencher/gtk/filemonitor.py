import logging
import os
import time
from collections import defaultdict

from gi.repository import GLib
from watchdog.events import (
    DirDeletedEvent,
    DirModifiedEvent,
    DirMovedEvent,
    FileClosedEvent,
    FileDeletedEvent,
    FileModifiedEvent,
    FileMovedEvent,
    FileSystemEvent,
    FileSystemEventHandler,
)
from watchdog.observers import Observer

from rencher import config_path, local_path
from rencher.gtk.window import RencherWindow
from rencher.renpy.config import RencherConfig


class RencherFileMonitor(FileSystemEventHandler):
    """
        watch over files and act accordingly
    """
    
    window: RencherWindow
    config: RencherConfig = RencherConfig()
    observer: Observer = None  # type: ignore
    data_dir: str
    pending_changes = defaultdict(lambda: {'last': 0.0, 'path': '', 'action': ''})
    pause_rpaths: list[str] = []

    def __init__(self, window: RencherWindow):
        super().__init__()
        self.window = window
        self.monitor_data_dir()
        GLib.timeout_add(250, self.flush_pending)

    def monitor_data_dir(self) -> None:
        if self.observer is not None:
            self.observer.stop()

        self.config.read()
        if not os.path.isdir(local_path):
            self.config.write()  # automatically makes the dir and config
        self.data_dir = self.config.get_data_dir()
        os.makedirs(self.data_dir, exist_ok=True)

        self.observer = Observer()
        self.observer.schedule(self, config_path)
        self.observer.schedule(self, self.data_dir, recursive=True)
        self.observer.start()
        logging.debug(f'Watching "{self.data_dir}/" for changes')
    
    def queue_event(self, event: FileSystemEvent) -> None:
        # these are all the subsequent events from a directory event or whatever.
        # aka NONE OF THEM MATTER !!!!!!!!
        if getattr(event, 'is_synthetic', False):
            return
        
        if event.dest_path:
            path = os.path.normpath(event.dest_path)
        else:
            path = os.path.normpath(event.src_path)

        if path == config_path:
            return
        if path == self.data_dir:
            return
        if os.path.dirname(path) == self.data_dir:
            return

        game_item = None
        for rpath, item in self.window.library.game_items.items():
            if path.startswith(rpath + os.sep):
                game_item = item
                break
            
        if game_item:
            if game_item.game.is_valid:
                key = game_item.rpath
                action = 'changed'
            else:
                key = game_item.rpath
                action = 'removed'
        else:
            games_dir = os.path.join(self.data_dir, 'games')
            rel_path = os.path.relpath(path, games_dir)
            top_dir = rel_path.split(os.sep, 1)[0]
            key = os.path.join(games_dir, top_dir)
            if top_dir == '..':
                # when refreshing the data directory, it would hallucinate a game with the path "[datadir]/games/.."
                return
            if not os.path.isdir(key):
                # at the end of deleting a game the folder gets added somehow
                return
            action = 'added'
        
        self.pending_changes[key]['last'] = time.time()
        self.pending_changes[key]['path'] = path
        self.pending_changes[key]['action'] = action
    
    def flush_pending(self) -> bool:
        now = time.time()
        to_emit = []
        
        for rpath, info in list(self.pending_changes.items()):
            if rpath in self.pause_rpaths or '*' in self.pause_rpaths:
                continue
            if now - info['last'] >= 0.1:
                to_emit.append((rpath, info['action']))
                del self.pending_changes[rpath]
        
        for rpath, action in to_emit:
            if action == 'changed':
                self.window.library.change_game(rpath)
            elif action == 'removed':
                self.window.library.remove_game(rpath)
            else:
                self.window.library.add_game(rpath)
        return True
    
    def on_moved(self, event: DirMovedEvent | FileMovedEvent) -> None:
        self.queue_event(event)
            
    def on_deleted(self, event: DirDeletedEvent | FileDeletedEvent) -> None:
        if os.path.exists(event.src_path):
            # this means it *actually* got edited
            # idk either ok??
            self.on_closed(event)
        else:
            self.queue_event(event)
        
    def on_closed(self, event: FileClosedEvent | DirDeletedEvent | FileDeletedEvent) -> None:
        # edited
        if event.src_path == config_path:
            if RencherConfig().get_data_dir() != self.data_dir:                
                self.monitor_data_dir()
        else:
            self.queue_event(event)

    def on_modified(self, event: DirModifiedEvent | FileModifiedEvent) -> None:
        self.queue_event(event)
        