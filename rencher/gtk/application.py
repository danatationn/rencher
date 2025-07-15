import logging
import os
import threading
import tomllib

import gi
import requests
from watchdog.observers import Observer

import rencher
from rencher import local_path, tmp_path
from rencher.renpy.config import RencherConfig

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Adw, Gdk, Gtk  # noqa: E402

Adw.init()

from rencher.gtk.filemonitor import RencherFileMonitor  # noqa: E402
from rencher.gtk.window import RencherWindow  # noqa: E402


class RencherApplication(Gtk.Application):
    config: dict = None
    window: RencherWindow = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, application_id='com.github.danatationn.rencher')
        logging.basicConfig(
            level=logging.NOTSET,
            format='[%(levelname)s\t%(asctime)s.%(msecs)-3d %(module)-16s] %(message)s',
            datefmt='%H:%M:%S', 
        )

        watchdog_logger = logging.getLogger('watchdog')
        watchdog_logger.propagate = False
        urllib3_logger = logging.getLogger('urllib3')
        urllib3_logger.setLevel(logging.WARNING)

    def do_startup(self):
        Gtk.Application.do_startup(self)

    def do_activate(self):
        Gtk.Application.do_activate(self)

        self.config = RencherConfig()
        self.window = RencherWindow(application=self)
        self.window.present()

        observer = Observer()
        handler = RencherFileMonitor(self.window)
        if not os.path.isdir(local_path):
            os.mkdir(local_path)
        observer.schedule(handler, local_path, recursive=True)
        observer.start()

        version_thread = threading.Thread(target=self.check_version)
        version_thread.run()

    def check_version(self):
        # if '__compiled__' not in globals():
        # 	return
        if self.config['settings']['suppress_updates'] == 'true':
            return

        try:
            response = requests.get('https://api.github.com/repos/danatationn/rencher/releases/latest')
        except requests.exceptions.ConnectionError:
            return
        else:
            if response.status_code == 404:
                return
            version = response.json()['tag_name'].replace('v', '')

            if version > rencher.__version__:
                if 'assets' in response.json() and len(response.json()['assets']) > 0:
                    download_url = response.json()['html_url']
                else:
                    return

                logging.info(f'A new update is available! (v{version})')
                logging.info(download_url)
                toast = Adw.Toast(
                    title=f'A new update is available! (v{version})',
                    timeout=5,
                    button_label='Download',
                )
                toast.connect('button-clicked', lambda *_: (
                    Gtk.show_uri(self.window, download_url, Gdk.CURRENT_TIME)
                ))

                self.window.toast_overlay.add_toast(toast)
            else:
                logging.info(f'You\'re up to date! (v{rencher.__version__})')
