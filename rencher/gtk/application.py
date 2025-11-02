import logging
import os
import threading

import gi
import requests

import rencher
from rencher import tmp_path
from rencher.renpy.config import RencherConfig

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Adw, Gdk, Gio, GLib, Gtk  # noqa: E402

Adw.init()

from rencher.gtk.filemonitor import RencherFileMonitor  # noqa: E402
from rencher.gtk.window import RencherWindow  # noqa: E402


class RencherApplication(Gtk.Application):
    config: dict = None
    window: RencherWindow = None
    file_monitor: RencherFileMonitor = None


    def __init__(self, *args, **kwargs):
        super().__init__(
            *args, **kwargs,
            application_id='com.github.danatationn.rencher',
            flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE | Gio.ApplicationFlags.NON_UNIQUE,
        )

        self.add_main_option('verbose', ord('v'), GLib.OptionFlags.NONE, GLib.OptionArg.NONE, 'Enable verbose output')
        self.add_main_option('version', ord('V'), GLib.OptionFlags.NONE, GLib.OptionArg.NONE, 'Prints version')

        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter('[%(levelname)s\t%(asctime)s.%(msecs)-3d %(module)s] %(message)s',
                                   datefmt='%H:%M:%S')

        file_handler = logging.FileHandler(os.path.join(rencher.local_path, 'log.txt'), mode='w')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        console_handler.name = 'console_handler'
        logger.addHandler(console_handler)

        watchdog_logger = logging.getLogger('watchdog')
        watchdog_logger.propagate = False
        urllib3_logger = logging.getLogger('urllib3')
        urllib3_logger.setLevel(logging.WARNING)

        actions = [
            ['show-import', self.on_show_import, ['<Primary>plus']],
            # ['show-tasks', self.on_show_tasks, ['<Primary>b']],
            ['show-preferences', self.on_show_preferences, ['<Primary>comma']],
            ['show-shortcuts', self.on_show_shortcuts, ['<Primary>question']],
            ['show-about', self.on_show_about, []],
            ['quit', self.on_quit, ['<Primary>q', '<Primary>w']],
        ]

        for name, callback, accels in actions:
            simple_action = Gio.SimpleAction.new(name, None)
            simple_action.connect('activate', callback)
            self.add_action(simple_action)
            if accels:
                self.set_accels_for_action(f'app.{name}', accels)

    def do_command_line(self, command_line):
        options = command_line.get_options_dict()
        
        if options.contains('verbose'):
            logging.getHandlerByName('console_handler').setLevel(logging.DEBUG)
        if options.contains('version'):
            print(rencher.__version__)
            return 0
        # if options.contains('data-dir'):
        #     data_dir = options.lookup_value('data-dir').get_string()
        #     logging.info(f'Setting data directory at {os.path.abspath(data_dir)}')
            
        self.activate()
        return 0
    
    def do_activate(self):
        Gtk.Application.do_activate(self)

        self.config = RencherConfig()
        self.window = RencherWindow(application=self)
        self.window.present()
        self.file_monitor = RencherFileMonitor(self.window)

        if self.config['settings']['suppress_updates'] != 'true':
            version_thread = threading.Thread(target=self.check_version)
            version_thread.start()

    def on_show_import(self, *_):
        self.window.on_import_clicked()

    def on_show_preferences(self, *_):
        self.window.settings_dialog.on_show()
        self.window.settings_dialog.present(self.window)

    # def on_show_tasks(self, *_):
    #     self.window.pie_progress_button.activate()

    def on_show_shortcuts(self, *_):
        ui_file = os.path.join(tmp_path, 'rencher/gtk/ui/shortcuts.ui')
        if os.path.isfile(ui_file):
            builder = Gtk.Builder.new_from_file(ui_file)
            dialog = builder.get_object('RencherShortcuts')
            if isinstance(dialog, Adw.ShortcutsDialog):
                dialog.present(self.window)
        else:
            ui_file = os.path.join(tmp_path, 'rencher/gtk/ui/shortcuts_deprecated.ui')
            builder = Gtk.Builder.new_from_file(ui_file)
            dialog = builder.get_object('RencherShortcuts')
            if isinstance(dialog, Gtk.ShortcutsWindow):
                dialog.set_transient_for(self.window)
                dialog.show()

    def on_quit(self, *_):
        self.quit()

    def on_show_about(self, *_):
        dialog = Adw.AboutDialog(
            application_icon='rencher-icon',
            application_name='Rencher',
            developer_name='danatationn',
            version=rencher.__version__,
            comments=rencher.__description__,
            website=rencher.__url__,
            issue_url=rencher.__issue_url__,
            support_url=rencher.__issue_url__,
            copyright=rencher.__copyright__,
            license_type=Gtk.License.GPL_3_0_ONLY,
            developers=['danatationn'],
            designers=['danatationn', 'vl1'],
        )
        dialog.set_release_notes("""<ul>
            <li> Added tasks </li>
            <li> Added crash dialogs on Linux </li>
            <li> Added basic shortcuts </li>
            <li> Swapped settings button for hamburger menu </li>
            <li> Brought back filename restrictions for Windows </li>
            <li> Fixed import dialog "memory leak" </li>
            <li> More crash prevention </li>
        </ul>""")

        dialog.present(self.window)

    def pause_monitor(self, rpath: str) -> None:
        if rpath not in self.file_monitor.pause_rpaths:
            self.file_monitor.pause_rpaths.append(rpath)
            
    def resume_monitor(self, path: str) -> None:
        for rpath in self.file_monitor.pause_rpaths:
            if os.path.commonpath([path, rpath]):
                self.file_monitor.pause_rpaths.remove(rpath)
        self.file_monitor.flush_pending()

    def check_version(self, show_up_to_date_toast: bool = False) -> None:
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
                toast = Adw.Toast(title=f'A new update is available! (v{version})', timeout=5, button_label='Download')
                toast.connect('button-clicked', lambda *_: (
                    Gtk.show_uri(self.window, download_url, Gdk.CURRENT_TIME)
                ))

                GLib.idle_add(self.window.toast_overlay.add_toast, toast)
            else:
                message = f'You\'re up to date! (v{rencher.__version__})'
                if show_up_to_date_toast:
                    toast = Adw.Toast(title=message, timeout=5)
                    GLib.idle_add(self.window.toast_overlay.add_toast, toast)
                logging.info(message)
