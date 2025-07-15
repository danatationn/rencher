import logging
from pathlib import Path

from gi.repository import Adw, Gio, GLib
from watchdog.events import DirModifiedEvent, FileModifiedEvent, FileSystemEventHandler

from rencher import config_path
from rencher.gtk._library import update_library_sidebar, update_library_view
from rencher.gtk.window import RencherWindow
from rencher.renpy.config import RencherConfig

config_path = str(config_path)  # stub


class RencherFileMonitor(FileSystemEventHandler):
    window: RencherWindow = None
    mtimes: list[int] = []  # for debouncing :)
    config: RencherConfig = RencherConfig()

    def __init__(self, window: RencherWindow):
        super().__init__()
        self.window = window
        self.mtimes: list[int] = []

    def on_modified(self, event: DirModifiedEvent | FileModifiedEvent) -> None:
        if self.window.process:
            return
        if self.window.import_dialog.thread.is_alive():
            return
        if self.window.pause_fs:
            return

        src_path = Path(event.src_path)
        if src_path == config_path:
            self.config.read()

        data_dir = self.config.get_data_dir()
        games_path = data_dir / 'games'
        mods_path = data_dir / 'mods'

        if not src_path.is_relative_to(games_path) and not src_path.is_relative_to(mods_path):
            return

        try:
            mtime = int(src_path.stat().st_mtime)
        except FileNotFoundError:
            # something got deleted 🤷‍
            if src_path.parent.is_relative_to(games_path) or src_path.parent.is_relative_to(mods_path):
                GLib.idle_add(update_library_sidebar, self.window)
            mtime = 0

        if mtime in self.mtimes:
            return
        else:
            self.mtimes.append(mtime)
            GLib.idle_add(update_library_sidebar, self.window)
            row = self.window.library_list_box.get_selected_row()
            if row:
                GLib.idle_add(update_library_view, self.window, row.game)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.NOTSET,
        format='[%(levelname)s %(asctime)s.%(msecs)d %(module)s] > %(message)s',
        datefmt='%H:%M:%S',
    )
