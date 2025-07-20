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
from rencher.gtk._library import update_library_sidebar
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
            *
    """
    
    window: RencherWindow = None
    mtimes: dict[str, float] = {}  # for debouncing :)
    config: RencherConfig = RencherConfig()
    observer: Observer = None
    queue: list[FileSystemEvent] = []

    def __init__(self, window: RencherWindow):
        super().__init__()
        self.window = window
        self.monitor_data_dir()
        # GLib.timeout_add(500, self.handle_queue)

    def monitor_data_dir(self) -> None:
        if self.observer is not None:
            self.observer.stop()
            # self.observer.join()

        if not os.path.isdir(local_path):
            self.config.write()  # automatically makes the dir and config
        data_dir = self.config.get_data_dir()
        if not os.path.isdir(data_dir):
            os.mkdir(data_dir)

        self.observer = Observer()
        self.observer.schedule(self, config_path)
        self.observer.schedule(self, data_dir, recursive=True)
        self.observer.start()
        logging.debug(data_dir)
        
    # def handle_queue(self) -> bool:
    #     if not self.window.games:
    #         return True
    #     
    #     events: dict = {}
    #     for event in self.queue:
    #         for game in self.window.games:
    #             if os.path.commonpath([event.src_path, game.rpath]) == game.rpath:
    #                 events[game] = event
    #     
    #     for game, event in events.items():
    #         if isinstance(event, FileModifiedEvent):
    #             
    #     
    #     logging.debug(events)
    #     self.queue.clear()
    #     return True

    def on_moved(self, event: DirMovedEvent | FileMovedEvent) -> None:
        logging.debug(f'something got moved {event.src_path} -> {event.dest_path}')        
            
    def on_deleted(self, event: DirDeletedEvent | FileDeletedEvent) -> None:
        if os.path.exists(event.src_path):
            # this means it *actually* got edited
            # idk either ok??
            self.on_closed(event)
        elif self.queue_check():
            self.queue.append(event)
        else:
            ...
        
    def on_closed(self, event: FileClosedEvent | DirDeletedEvent | FileDeletedEvent) -> None:
        if event.src_path == config_path:
            self.monitor_data_dir()
        elif self.queue_check():
            self.queue.append(event)
        else:
            ...
        
    def on_modified(self, event: DirModifiedEvent | FileModifiedEvent) -> None:
        if self.queue_check() and not isinstance(event, DirModifiedEvent):
            self.queue.append(event)
        else:
            ...
    
    def handle_event(self, event: FileSystemEvent) -> None:
        src_path = event.src_path
        if src_path == config_path:
            self.config.read()
    
        data_dir = self.config.get_data_dir()
        games_path = os.path.join(data_dir, 'games')
        if os.path.commonpath([src_path, games_path]) != games_path:
            return
    
        try:
            mtime = int(os.stat(src_path).st_mtime)
        except FileNotFoundError:
            # something got deleted 🤷‍
            if os.path.commonpath([src_path, games_path]) == games_path:
                GLib.idle_add(update_library_sidebar, self.window)
            mtime = 0
    
        if mtime in self.mtimes:
            return
        else:
            self.mtimes[src_path] = mtime
            GLib.idle_add(self.window.current_game.refresh)
            
    def queue_check(self) -> list[str]:
        return [
            self.window.pause_monitoring,
            self.window.game_process,
            self.window.import_dialog.thread.is_alive(),
        ]