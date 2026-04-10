import logging
import os
import time
from collections import defaultdict
from typing import override

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

from rencher.gtk.library import Library
from rencher.renpy.config import RencherConfig
from rencher.renpy.paths import config_path, local_path


class RencherFileMonitor(FileSystemEventHandler):
    """
        watch over files and act accordingly
    """

    observer: Observer = None  # pyright: ignore[reportInvalidTypeForm]
    data_dir: str
    pending_changes: defaultdict[object, dict[str, float | str]]
    pause_rpaths: list[str]
    library: Library

    def __init__(self, library: Library):
        super().__init__()
        self.monitor_data_dir()
        self.library = library
        self.pause_rpaths = []
        self.pending_changes = defaultdict(lambda: {'last': 0.0, 'path': '', 'action': ''})
        GLib.timeout_add(250, self.flush_pending)

    def monitor_data_dir(self) -> None:
        if self.observer is not None:
            self.observer.stop()

        config = RencherConfig()
        config.read()
        if not os.path.isdir(local_path):
            config.write()  # automatically makes the dir and config
        self.data_dir = config.get_data_dir()
        os.makedirs(self.data_dir, exist_ok=True)

        self.observer = Observer()
        self.observer.schedule(self, config_path)
        self.observer.schedule(self, self.data_dir, recursive=True)
        self.observer.start()
        logging.debug(f'Watching "{self.data_dir}" for changes')

    def queue_event(self, event: FileSystemEvent) -> None:
        # these are all the subsequent events from a directory event or whatever.
        # aka NONE OF THEM MATTER !!!!!!!!
        if getattr(event, 'is_synthetic', False):
            return

        if event.dest_path:
            path = str(os.path.normpath(event.dest_path))
        else:
            path = str(os.path.normpath(event.src_path))

        if path == config_path:
            return
        if path == self.data_dir:
            return
        if os.path.dirname(path) == self.data_dir:
            return

        # game_item = None
        # for _, item in enumerate(self.library.store):
            # if item and path.startswith(item.rpath + os.sep):
                # game_item = item
                # break

        if (result := self.library.find(path)):
            _, game_item = result
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
            key = os.path.normpath(os.path.join(games_dir, top_dir))
            if top_dir in ['..', '.']:
                # when refreshing the data directory, it would hallucinate a game with the path "[datadir]/games/.."
                return
            if not os.path.isdir(key):
                # at the end of deleting a game the folder gets added somehow
                return
            action = 'added'

        self.pending_changes[key]['last'] = time.time()
        self.pending_changes[key]['path'] = str(path)
        self.pending_changes[key]['action'] = action
        # logging.debug(f'queue_event: action={action!r} key={key!r}')

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
                self.library.change_game(rpath)
            elif action == 'removed':
                self.library.remove_game(rpath)
            else:
                self.library.add_game(rpath)
            # logging.debug(f'flush_pending: action={action!r} rpath={rpath!r}')
        return True

    @override
    def on_moved(self, event: DirMovedEvent | FileMovedEvent) -> None:
        self.queue_event(event)

    @override
    def on_deleted(self, event: DirDeletedEvent | FileDeletedEvent) -> None:
        if os.path.exists(event.src_path):
            # this actually means that it was edited
            self.on_closed(event)
        else:
            self.queue_event(event)

    @override
    def on_closed(self, event: FileClosedEvent | DirDeletedEvent | FileDeletedEvent) -> None:
        # edited
        if os.path.isfile(event.src_path) and config_path.samefile(event.src_path):
            if RencherConfig().get_data_dir() != self.data_dir:
                self.monitor_data_dir()
        else:
            self.queue_event(event)

    @override
    def on_modified(self, event: DirModifiedEvent | FileModifiedEvent) -> None:
        self.queue_event(event)

    def pause_monitor(self, rpath: str) -> None:
        if rpath not in self.pause_rpaths:
            self.pause_rpaths.append(rpath)

    def resume_monitor(self, path: str) -> None:
        for rpath in self.pause_rpaths:
            if os.path.commonpath([path, rpath]):
                self.pause_rpaths.remove(rpath)
        self.flush_pending()
