import glob
import logging
import os
import shutil
import threading
from configparser import ConfigParser

from gi.repository import Adw, GLib, Gtk

from rencher import config_path, local_path, tmp_path
from rencher.gtk import open_file_manager
from rencher.gtk._library import update_library_sidebar
from rencher.renpy.game import Game

filename = os.path.join(tmp_path, 'rencher/gtk/ui/options.ui')
@Gtk.Template(filename=str(filename))
class RencherOptions(Adw.PreferencesDialog):
    __gtype_name__ = 'RencherOptions'

    options_nickname: Adw.EntryRow = Gtk.Template.Child()
    options_location: Adw.ActionRow = Gtk.Template.Child()
    options_codename: Adw.ComboRow = Gtk.Template.Child()
    options_skip_splash_scr: Adw.SwitchRow = Gtk.Template.Child()
    options_skip_main_menu: Adw.SwitchRow = Gtk.Template.Child()
    options_forced_save_dir: Adw.SwitchRow = Gtk.Template.Child()
    overwrite_skip_splash_scr: Gtk.Switch = Gtk.Template.Child()
    overwrite_skip_main_menu: Gtk.Switch = Gtk.Template.Child()
    overwrite_forced_save_dir: Gtk.Switch = Gtk.Template.Child()
    options_save_slot: Adw.SpinRow = Gtk.Template.Child()

    game: Game = None
    rencher_config: ConfigParser = None

    def __init__(self, window: 'RencherWindow'):
        super().__init__()

        self.window = window
        self.switches_list = [
            [self.overwrite_skip_splash_scr, self.options_skip_splash_scr, 'skip_splash_scr'],
            [self.overwrite_skip_main_menu, self.options_skip_main_menu, 'skip_main_menu'],
            [self.overwrite_forced_save_dir, self.options_forced_save_dir, 'forced_save_dir'],
        ]

        self.options_save_slot.set_adjustment(Gtk.Adjustment(
            lower=1,
            upper=10,
            value=1,
            step_increment=1,
            page_increment=10,
        ))

    def change_game(self, game: Game):
        self.game = game
        string_list = Gtk.StringList()
        self.options_codename.set_model(string_list)

        with open(config_path) as f:
            self.rencher_config = ConfigParser()
            self.rencher_config.read_file(f)

        self.options_nickname.set_text(game.name)
        self.options_location.set_subtitle(str(game.rpath))
        self.options_save_slot.set_text(game.config['options']['save_slot'])

        py_files = glob.glob(os.path.join(game.apath, '*.py'))

        for i, path in enumerate(py_files):
            name = os.path.basename(path)
            codename = os.path.splitext(name)[0]
            if codename == game.config['info']['codename']:
                logging.debug(f'{i}: {codename}')
                self.options_codename.set_selected(i)
                logging.debug(self.options_codename.get_selected())
            string_list.append(codename)

        self.options_codename.set_model(string_list)

        for overwrite_switch, switch, key in self.switches_list:
            if game.config['options'][key] != '':
                overwrite_switch.set_active(True)
                if game.config['options'][key] == 'true':
                    switch.set_active(True)
                else:
                    switch.set_active(False)
            elif self.rencher_config['settings'][key] == 'true':
                switch.set_active(True)

    def do_closed(self):
        if not os.path.isdir(self.game.rpath):
            return  # it got deleted

        if self.game.name != self.options_nickname.get_text():
            self.game.config['info']['nickname'] = self.options_nickname.get_text()
        if self.game.codename != self.options_codename.get_selected_item().get_string():
            self.game.config['info']['codename'] = self.options_codename.get_selected_item().get_string()
        self.game.config['options']['save_slot'] = self.options_save_slot.get_text()

        for overwrite_switch, switch, key in self.switches_list:
            if overwrite_switch.get_active():
                if switch.get_active():
                    self.game.config['options'][key] = 'true'
                    self.game.config['overwritten'][key] = 'true'
                else:
                    self.game.config['options'][key] = 'false'
                    self.game.config['overwritten'][key] = 'false'
            else:
                self.game.config['options'][key] = ''
                self.game.config['overwritten'][key] = self.rencher_config['settings'][key]

        self.game.config.write()
        self.select_after_refresh()

    def select_after_refresh(self):
        def select():
            for row in self.window.library_list_box:
                if row.game.rpath == self.game.rpath:
                    self.window.current_game.refresh()
                    self.window.library_list_box.select_row(row)
                    break

        update_library_sidebar(self.window)
        GLib.idle_add(select)


    @Gtk.Template.Callback()
    def on_switch_changed(self, _widget: Gtk.Switch | Adw.SwitchRow, _):
        for overwrite_switch, switch, key in self.switches_list:
            if _widget == overwrite_switch:
                current_value = self.rencher_config['settings'][key]
                if current_value == 'true':
                    switch.set_active(True)
                else:
                    switch.set_active(False)

    @Gtk.Template.Callback()
    def on_dir_clicked(self, _widget: Gtk.Button):
        open_file_manager(str(self.game.rpath))

    @Gtk.Template.Callback()
    def on_clear_info(self, _widget: Adw.ButtonRow):  # type: ignore
        dialog = Adw.AlertDialog(
            heading='Are you sure?',
            body=f'This will permanently reset all user data for "{self.game.name}".\nThis action cannot be undone.',
        )
        dialog.add_response('cancel', 'No')
        dialog.add_response('ok', 'Yes')
        dialog.set_response_appearance('ok', Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.set_default_response('cancel')
        dialog.set_close_response('cancel')
        dialog.choose(self)
        dialog.connect('response', self.on_clear_info_response)

    def on_clear_info_response(self, _, response: str):
        if response == 'ok':
            # slaughter time
            self.game.config['info']['nickname'] = ''
            self.game.config['info']['last_played'] = ''
            self.game.config['info']['playtime'] = '0.0'

            self.game.config['options']['skip_splash_scr'] = ''
            self.game.config['options']['skip_main_menu'] = ''
            self.game.config['options']['forced_save_dir'] = ''
            # self.game.config['info']['added_on'] = str(int(time.time()))
            # self.game.config.write_config()
            toast = Adw.Toast(
                title=f'"{self.game.name}" stats have been reset',
                timeout=5,
            )
            self.window.toast_overlay.add_toast(toast)

    @Gtk.Template.Callback()
    def on_delete_game(self, _widget: Adw.ButtonRow):  # type: ignore
        dialog = Adw.AlertDialog(
            heading='Are you sure?',
            body=f'This will permanently delete "{self.game.name}".\nThis action cannot be undone.',
        )
        dialog.add_response('cancel', 'No')
        dialog.add_response('ok', 'Yes')
        dialog.set_response_appearance('ok', Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.set_default_response('cancel')
        dialog.set_close_response('cancel')
        dialog.choose(self)
        dialog.connect('response', self.on_delete_game_response)

    def on_delete_game_response(self, _, response: str):
        if response == 'ok':
            # some safety measures
            def delete_thread():
                self.window.pause_monitoring = True
                toast = Adw.Toast(
                    title=f'"{self.game.name}" succesfully deleted',
                    timeout=5,
                )

                try:
                    shutil.rmtree(self.game.rpath)
                except FileNotFoundError:
                    toast.set_title('The deletion has failed')
                finally:
                    self.window.pause_monitoring = False
                    self.close()
                    update_library_sidebar(self.window)
                    self.window.toast_overlay.add_toast(toast)

            thread = threading.Thread(target=delete_thread)
            thread.start()