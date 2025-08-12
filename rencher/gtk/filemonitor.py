import logging
import os
import sys
import time
from collections import defaultdict

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
from rencher.gtk.game_item import GameItem
from rencher.gtk.window import RencherWindow
from rencher.renpy.config import RencherConfig


class RencherFileMonitor(FileSystemEventHandler):
    """
        watch over files and act accordingly
    """
    
    window: RencherWindow = None
    config: RencherConfig = RencherConfig()
    observer: Observer = None
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
        if not os.path.isdir(self.data_dir):
            os.mkdir(self.data_dir)

        self.observer = Observer()
        self.observer.schedule(self, config_path)
        self.observer.schedule(self, self.data_dir, recursive=True)
        self.observer.start()
        logging.debug(f'Watching "{self.data_dir}/" for changes')
    
    def queue_event(self, event: FileSystemEvent) -> None:
        if getattr(event, 'is_synthetic', False):
            return
        
        if event.dest_path:
            path = event.dest_path
        else:
            path = event.src_path

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
            logging.debug(f'"{games_dir}"; "{rel_path}"; "{top_dir}"; "{key}"')
            action = 'added'
        
        self.pending_changes[key]['last'] = time.time()
        self.pending_changes[key]['path'] = path
        self.pending_changes[key]['action'] = action
    
    def flush_pending(self) -> bool:
        now = time.time()
        to_emit = []
        for rpath, info in list(self.pending_changes.items()):
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
            self.monitor_data_dir()
        else:
            self.queue_event(event)

    def on_modified(self, event: DirModifiedEvent | FileModifiedEvent) -> None:
        self.queue_event(event)
        