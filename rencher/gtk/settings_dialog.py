import os.path
import platform
import threading
import time
from pathlib import Path
from typing import TYPE_CHECKING

from gi.repository import Adw, GLib, Gtk

from rencher import local_path, tmp_path
from rencher.gtk.tasks import TaskTypeEnum
from rencher.gtk.utils import open_file_manager
from rencher.renpy.config import RencherConfig

if TYPE_CHECKING:
    from rencher.gtk.window import RencherWindow

filename = os.path.join(tmp_path, 'rencher/gtk/ui/settings.ui')
@Gtk.Template(filename=str(filename))
class RencherSettings(Adw.PreferencesDialog):
    __gtype_name__ = 'RencherSettings'

    window: 'RencherWindow'
    config: RencherConfig = None

    settings_data_dir: Adw.EntryRow = Gtk.Template.Child()
    settings_updates: Adw.SwitchRow = Gtk.Template.Child()
    settings_delete_import: Adw.SwitchRow = Gtk.Template.Child()
    settings_skip_splash_scr: Adw.SwitchRow = Gtk.Template.Child()
    settings_skip_main_menu: Adw.SwitchRow = Gtk.Template.Child()
    settings_forced_save_dir: Adw.SwitchRow = Gtk.Template.Child()
    settings_windowficate: Adw.SwitchRow = Gtk.Template.Child()

    def __init__(self, window, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.window = window
        self.switches_list = [
            [self.settings_delete_import, 'delete_on_import'],
            [self.settings_updates, 'suppress_updates'],
            [self.settings_skip_splash_scr, 'skip_splash_scr'],
            [self.settings_skip_main_menu, 'skip_main_menu'],
            [self.settings_forced_save_dir, 'forced_save_dir'],
            [self.settings_windowficate, 'windowficate_filenames'],
        ]

        if platform.system() == 'Windows':
            self.settings_windowficate.set_visible(False)  # force it on

    def on_show(self):
        self.config = RencherConfig()

        if self.config['settings']['data_dir'] == '':
            self.settings_data_dir.set_text(str(local_path))
        else:
            self.settings_data_dir.set_text(self.config['settings']['data_dir'])

        for switch, key in self.switches_list:
            if self.config['settings'][key] == 'true':
                switch.set_active(True)

    def do_closed(self):
        old_data_dir = self.config['settings']['data_dir']

        if self.settings_data_dir.get_text() == str(local_path):
            self.config['settings']['data_dir'] = ''
        else:
            self.config['settings']['data_dir'] = self.settings_data_dir.get_text()

        for switch, key in self.switches_list:
            if switch.get_active():
                self.config['settings'][key] = 'true'
            else:
                self.config['settings'][key] = 'false'

        self.config.write()

        if self.config['settings']['data_dir'] != old_data_dir:
            self.window.library.load_games()

    @Gtk.Template.Callback()
    def on_picker_clicked(self, _widget: Gtk.Button):
        dialog = Gtk.FileDialog()
        dialog.select_folder(self.window, None, self.on_folder_selected)

    @Gtk.Template.Callback()
    def on_dir_clicked(self, _):
        data_dir = self.settings_data_dir.get_text()
        open_file_manager(data_dir)

    def on_folder_selected(self, dialog: Gtk.FileDialog, result):
        try:
            folder = dialog.select_folder_finish(result)
        except GLib.GError:
            pass  # dialog was dismissed by user
        else:
            self.settings_data_dir.set_text(folder.get_path())

    @Gtk.Template.Callback()
    def on_check_updates(self, _):
        thread = threading.Thread(target=lambda: self.window.application.check_version(show_up_to_date_toast=True))
        thread.start()
        self.close()

    @Gtk.Template.Callback()
    def on_reset_data_dir(self, _widget: Adw.ButtonRow):  # type: ignore
        self.settings_data_dir.set_text(str(local_path))

    @Gtk.Template.Callback()
    def on_delete_games(self, _widget: Adw.ButtonRow):  # type: ignore
        dialog = Adw.AlertDialog(
            heading='Are you sure?',
            body='This will delete ALL the games in your data directory.\nThis action cannot be undone.',
        )
        dialog.add_response('cancel', 'No')
        dialog.add_response('ok', 'Yes')
        dialog.set_response_appearance('ok', Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.set_close_response('cancel')
        dialog.set_default_response('cancel')
        dialog.connect('response', self.nuke_games)
        dialog.choose(self)

    def nuke_games(self, _, response: str):
        if response != 'ok':
            return
        data_dir = Path(self.settings_data_dir.get_text())
        games_dir = data_dir / 'games'

        def nuke_thread():
            self.window.application.pause_monitor('*')
            toast = Adw.Toast(title='All games have been successfully deleted', timeout=5)
            total_work = 0
            completed = 0
            rpaths: list[str] = []

            for _, dirs, files in os.walk(games_dir):
                for _ in dirs:
                    total_work += 1
                for _ in files:
                    total_work += 1

            task_date = time.time()
            GLib.idle_add(self.window.tasks_popover.new_task, task_date, 'le everything', TaskTypeEnum.DELETE, None,
                          total_work)

            for _, dirs, _ in os.walk(games_dir):
                for dir in dirs:
                    path = os.path.join(games_dir, dir)
                    rpaths.append(path)
                break

            for root, dirs, files in os.walk(games_dir, topdown=False):
                for filename in files:
                    file = os.path.join(root, filename)
                    try:
                        os.unlink(file)
                    except PermissionError:
                        pass
                    except FileNotFoundError:
                        pass
                    completed += 1
                    GLib.idle_add(self.window.tasks_popover.update_task, task_date, completed)

                for dirname in dirs:
                    dir = os.path.join(root, dirname)
                    try:
                        os.rmdir(dir)
                    except PermissionError:
                        pass
                    except FileNotFoundError:
                        pass
                    completed += 1
                    GLib.idle_add(self.window.tasks_popover.update_task, task_date, completed)

                if root in rpaths:
                    GLib.idle_add(lambda r=root: self.window.library.remove_game(r))

            GLib.idle_add(lambda: (
                self.window.application.resume_monitor('*'),
                self.window.toast_overlay.add_toast(toast),
            ))

        thread = threading.Thread(target=nuke_thread)
        thread.start()
        self.close()
