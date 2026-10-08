import sys
import threading
from typing import TYPE_CHECKING, override

from gi.repository import Adw, GLib, Gtk

from rencher.gtk.utils import gtk_template_callback, gtk_template_child, open_file_manager
from rencher.renpy.config import RencherConfig
from rencher.renpy.paths import local_path

if TYPE_CHECKING:
    from rencher.gtk.window import MainWindow

@Gtk.Template.from_resource('/com/github/danatationn/rencher/ui/settings.ui')
class SettingsDialog(Adw.PreferencesDialog):
    __gtype_name__: str = 'SettingsDialog'

    window: 'MainWindow'
    config: RencherConfig

    data_dir_entry: Adw.EntryRow = gtk_template_child()
    updates_switch: Adw.SwitchRow = gtk_template_child()
    delete_import_switch: Adw.SwitchRow = gtk_template_child()
    skip_splash_scr_switch: Adw.SwitchRow = gtk_template_child()
    skip_main_menu_switch: Adw.SwitchRow = gtk_template_child()
    forced_save_dir_switch: Adw.SwitchRow = gtk_template_child()
    windowficate_switch: Adw.SwitchRow = gtk_template_child()
    discord_rpc_switch: Adw.SwitchRow = gtk_template_child()
    reduce_motion_switch: Adw.SwitchRow = gtk_template_child()
    switches_list: list[tuple[Adw.SwitchRow, str]]

    def __init__(self, window: 'MainWindow', *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.switches_list = [
            (self.delete_import_switch, 'delete_on_import'),
            (self.updates_switch, 'suppress_updates'),
            (self.skip_splash_scr_switch, 'skip_splash_scr'),
            (self.skip_main_menu_switch, 'skip_main_menu'),
            (self.forced_save_dir_switch, 'forced_save_dir'),
            (self.windowficate_switch, 'windowficate_filenames'),
            (self.discord_rpc_switch, 'discord_rpc'),
            (self.reduce_motion_switch, 'reduce_motion'),
        ]

        self.window = window

        if sys.platform in ('win32', 'msys'):
            self.windowficate_switch.set_visible(False)  # force it on
            self.reduce_motion_switch.set_visible(True)

    def on_show(self):
        self.config = RencherConfig()

        if self.config['settings']['data_dir'] == '':
            self.data_dir_entry.set_text(str(local_path))
        else:
            self.data_dir_entry.set_text(self.config['settings']['data_dir'])

        for switch, key in self.switches_list:
            if self.config['settings'][key] == 'true':
                switch.set_active(True)

    @override
    def do_closed(self):
        old_data_dir = self.config['settings']['data_dir']

        if self.data_dir_entry.get_text() == str(local_path):
            self.config['settings']['data_dir'] = ''
        else:
            self.config['settings']['data_dir'] = self.data_dir_entry.get_text()

        for switch, key in self.switches_list:
            if switch.get_active():
                self.config['settings'][key] = 'true'
            else:
                self.config['settings'][key] = 'false'

        self.config.write()

        if self.config['settings']['data_dir'] != old_data_dir:
            self.window.library.load_games()

        if self.config.get('settings', 'discord_rpc') == 'true':
            self.activate_action('rpc.start')
        else:
            self.activate_action('rpc.stop')

        self.set_reduced_motion(self.reduce_motion_switch)

    @gtk_template_callback
    def on_picker_clicked(self, _widget: Gtk.Button):
        dialog = Gtk.FileDialog()
        dialog.select_folder(self.window, None, self.on_folder_selected)

    @gtk_template_callback
    def on_dir_clicked(self, _):
        data_dir = self.data_dir_entry.get_text()
        open_file_manager(data_dir)

    def on_folder_selected(self, dialog: Gtk.FileDialog, result):
        try:
            folder = dialog.select_folder_finish(result)
        except GLib.Error:
            pass  # dialog was dismissed by user
        else:
            path = folder.get_path()
            self.data_dir_entry.set_text(path if path else '')

    @gtk_template_callback
    def on_check_updates(self, _):
        thread = threading.Thread(target=lambda: self.window.app.check_version(show_up_to_date_toast=True))
        thread.start()
        self.close()

    def set_reduced_motion(self, switch: Adw.SwitchRow | None = None) -> None:
        """
        gtk animations on windows are REALLY laggy.
        disable them by default, and let users reenable them if they want to
        """
        if sys.platform not in ('win32', 'msys'):
            return

        if switch:
            value = switch.get_active()
        else:
            self.config = RencherConfig()
            value = self.config.get('settings', 'reduce_motion') == 'true'

        if value:
            if settings := Gtk.Settings.get_default():
                settings.set_property('gtk-enable-animations', False)
        else:
            import ctypes
            import ctypes.wintypes

            SPI_GETCLIENTAREAANIMATION = 0x1042
            animations_enabled = ctypes.wintypes.BOOL()

            # TODO type is Any
            success = ctypes.windll.user32.SystemParametersInfoW(
                SPI_GETCLIENTAREAANIMATION,
                0,
                ctypes.byref(animations_enabled),
                0,
            )

            if settings := Gtk.Settings.get_default():
                if success and not animations_enabled.value:
                    settings.set_property('gtk-enable-animations', False)
                else:
                    settings.set_property('gtk-enable-animations', True)

    @gtk_template_callback
    def on_reset_data_dir(self, _widget: Adw.ButtonRow):  # type: ignore
        self.data_dir_entry.set_text(str(local_path))

    @gtk_template_callback
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
        # dialog.connect('response', self.nuke_games)
        dialog.choose(self)
