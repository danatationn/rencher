import glob
import logging
import os
import time

from gi.repository import Gio, GLib

from rencher import config_path
from rencher.renpy.config import RencherConfig

config_path = str(config_path)  # stub


class RencherFileMonitor:
    """
    shoutout to gio.file for SUCKING DICK    
    
    UGHHHHHH
    
    CONFIG:
        whenever the config changes, check the data dir
        is it different?
            * unlink all current monitors
            * recursively add new ones
    
    DATA DIR:
        recursively monitor all directories in the data dir
        
    """

    monitor_config: Gio.FileMonitor = None
    monitor_data_dir: Gio.FileMonitor = None
    monitors: list[Gio.FileMonitor] = []

    def __init__(self):
        super().__init__()
        self.setup_monitors()

    def add_monitor(self, path: str):
        file = Gio.File.new_for_path(path)
        
        if os.path.isfile(path):
            monitor_file = file.monitor_file(Gio.FileMonitorFlags.NONE, None)
            monitor_file.connect('changed', self.on_file_changed)
        else:
            monitor_file = file.monitor_directory(Gio.FileMonitorFlags.NONE, None)
            monitor_file.connect('changed', self.on_dir_changed)
        self.monitors.append(monitor_file)

    def setup_monitors(self):
        start_time = time.perf_counter()

        config_file = Gio.File.new_for_path(config_path)
        self.monitor_config = config_file.monitor_file(Gio.FileMonitorFlags.NONE)
        self.monitor_config.connect('changed', self.on_config_changed)
        logging.info('config updated')

        data_dir_path = RencherConfig().get_data_dir()
        data_dir = str(data_dir_path)
        self.monitor_subdirs(data_dir)

        logging.debug(f'time: {time.perf_counter() - start_time}s')
        logging.debug(f'monitors: {len(self.monitors)}')

    def monitor_subdirs(self, dir: str):
        for root, dirs, files in os.walk(dir):
            if os.path.samefile(root, dir):
                pass
                # continue
            for path in dirs:
                self.add_monitor(path)
            for path in files:
                self.add_monitor(path)

    def on_config_changed(self, *_):
        self.setup_monitors()
        
    def on_file_changed(self, monitor: Gio.FileMonitor, file: Gio.File, 
                        other_file: Gio.File, event_type: Gio.FileMonitorEvent):
        path = file.get_path()
        
        logging.debug(f'file changed: {path}')
    
    def on_dir_changed(self, monitor: Gio.FileMonitor, file: Gio.File,
                       other_file: Gio.File, event_type: Gio.FileMonitorEvent):
        path = file.get_path()

        logging.debug(f'dir changed: {path}')

if __name__ == '__main__':
    logging.basicConfig(
        level=logging.NOTSET,
        format='[%(levelname)s %(asctime)s.%(msecs)d %(module)s] > %(message)s',
        datefmt='%H:%M:%S',
    )
    fm = RencherFileMonitor()
    loop = GLib.MainLoop()
    try:
        loop.run()
    except KeyboardInterrupt:
        loop.quit()