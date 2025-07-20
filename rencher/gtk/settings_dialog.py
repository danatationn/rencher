import logging
import os.path
import shutil
import threading
from pathlib import Path

from gi.repository import Adw, GLib, Gtk

import rencher
from rencher import local_path, tmp_path
from rencher.gtk._library import update_library_sidebar
from rencher.renpy.config import RencherConfig

filename = os.path.join(tmp_path, 'rencher/gtk/ui/settings.ui')
@Gtk.Template(filename=str(filename))
class RencherSettings(Adw.PreferencesDialog):
    __gtype_name__ = 'RencherSettings'

    settings_data_dir: Adw.EntryRow = Gtk.Template.Child()
    settings_updates: Adw.SwitchRow = Gtk.Template.Child()
    settings_delete_import: Adw.SwitchRow = Gtk.Template.Child()
    settings_skip_splash_scr: Adw.SwitchRow = Gtk.Template.Child()
    settings_skip_main_menu: Adw.SwitchRow = Gtk.Template.Child()
    settings_forced_save_dir: Adw.SwitchRow = Gtk.Template.Child()

    config: RencherConfig = None

    def __init__(self, window, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.window = window
        self.switches_list = [
            [self.settings_delete_import, 'delete_on_import'],
            [self.settings_updates, 'suppress_updates'],
            [self.settings_skip_splash_scr, 'skip_splash_scr'],
            [self.settings_skip_main_menu, 'skip_main_menu'],
            [self.settings_forced_save_dir, 'forced_save_dir'],
        ]

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
        if self.settings_data_dir.get_text() != str(local_path):
            self.config['settings']['data_dir'] = self.settings_data_dir.get_text()
        else:
            self.config['settings']['data_dir'] = ''

        for switch, key in self.switches_list:
            if switch.get_active():
                self.config['settings'][key] = 'true'
            else:
                self.config['settings'][key] = 'false'

        self.config.write()
        update_library_sidebar(self.window)  # for data_dir

    @Gtk.Template.Callback()
    def on_picker_clicked(self, _widget: Gtk.Button):
        dialog = Gtk.FileDialog()
        dialog.select_folder(self.window, None, self.on_folder_selected)

    def on_folder_selected(self, dialog: Gtk.FileDialog, result):
        try:
            folder = dialog.select_folder_finish(result)
        except GLib.GError:
            pass  # dialog was dismissed by user
        else:
            self.settings_data_dir.set_text(folder.get_path())

    @Gtk.Template.Callback()
    def on_check_updates(self, _):
        logging.debug(rencher.__version__)

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
        if response == 'ok':
            # oh boy
            data_dir = Path(self.settings_data_dir.get_text())
            games_dir = data_dir / 'games'

            def nuke_thread():
                toast = Adw.Toast(
                    title='All games have been successfully deleted',
                    timeout=5,
                )

                self.window.pause_monitoring = True
                try:
                    shutil.rmtree(games_dir)
                except FileNotFoundError:
                    toast.set_title('The deletion has failed')
                finally:
                    self.window.pause_monitoring = False
                    self.close()
                    update_library_sidebar(self.window)
                    self.window.toast_overlay.add_toast(toast)

            thread = threading.Thread(target=nuke_thread)
            thread.start()

    @Gtk.Template.Callback()
    def on_about_clicked(self, _widget: Gtk.Button):
        dialog = Adw.AboutDialog(
            application_icon='rencher',
            application_name='Rencher',
            developer_name=rencher.__author__,
            version=rencher.__version__,
            comments=rencher.__description__,
            website=rencher.__url__,
            issue_url=rencher.__issue_url__,
            support_url=rencher.__issue_url__,
            copyright='© 2025 danatationn',
            license_type=Gtk.License.GPL_3_0_ONLY,
            developers=['danatationn'],
            designers=['danatationn', 'vl1'],
        )
        dialog.add_acknowledgement_section('Credits', [
            'vl1 (for the logo)',
            'All my friends :)',
        ])

        dialog.present(self)