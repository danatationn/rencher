import logging
import os
from gettext import gettext as _
from pathlib import Path
from typing import override

from gi.repository import Adw, GLib, Gtk

from rencher.gtk.game_item import GameItem
from rencher.gtk.utils import gtk_template_callback, gtk_template_child, open_file_manager
from rencher.renpy.config import RencherConfig, get_rencher_settings
from rencher.renpy.paths import get_py_files


@Gtk.Template.from_resource('/com/github/danatationn/rencher/ui/options.ui')
class OptionsDialog(Adw.PreferencesDialog):
    __gtype_name__: str = 'OptionsDialog'

    nickname_entry: Adw.EntryRow = gtk_template_child()
    location_row: Adw.ActionRow = gtk_template_child()
    codename_combo: Adw.ComboRow = gtk_template_child()
    delete_game_button: Adw.ButtonRow = gtk_template_child()
    skip_splash_scr_switch: Adw.SwitchRow = gtk_template_child()
    skip_main_menu_switch: Adw.SwitchRow = gtk_template_child()
    forced_save_dir_switch: Adw.SwitchRow = gtk_template_child()
    discord_rpc_switch: Adw.SwitchRow = gtk_template_child()
    overwrite_skip_splash_scr_switch: Gtk.Switch = gtk_template_child()
    overwrite_skip_main_menu_switch: Gtk.Switch = gtk_template_child()
    overwrite_forced_save_dir_switch: Gtk.Switch = gtk_template_child()
    overwrite_discord_rpc_switch: Gtk.Switch = gtk_template_child()
    switches_list: list[tuple[Gtk.Switch, Adw.SwitchRow, str]]
    # options_save_slot: Adw.SpinRow = gtk_template_child()

    game_item: GameItem
    rencher_config: RencherConfig

    def __init__(self, game_item: GameItem):
        super().__init__()

        self.game_item = game_item

        self.switches_list = [
            (self.overwrite_skip_splash_scr_switch, self.skip_splash_scr_switch, 'skip_splash_scr'),
            (self.overwrite_skip_main_menu_switch, self.skip_main_menu_switch, 'skip_main_menu'),
            (self.overwrite_forced_save_dir_switch, self.forced_save_dir_switch, 'forced_save_dir'),
            (self.overwrite_discord_rpc_switch, self.discord_rpc_switch, 'discord_rpc'),
        ]

        # self.options_save_slot.set_adjustment(Gtk.Adjustment(
        #     lower=1,
        #     upper=10,
        #     value=1,
        #     step_increment=1,
        #     page_increment=10,
        # ))

        self.change_game(game_item)

    def change_game(self, game_item: GameItem):
        self.game_item.update(game_item.game)
        string_list = Gtk.StringList()
        self.codename_combo.set_model(string_list)

        self.rencher_config = get_rencher_settings()

        if game_item.has_nickname:
            self.nickname_entry.set_text(game_item.name)
        self.location_row.set_subtitle(str(game_item.top_dir))
        # self.options_save_slot.set_text(game.config['options']['save_slot'])

        py_files = get_py_files(game_item.base_dir)

        codename_index = None
        for i, path in enumerate(py_files):
            codename = os.path.splitext(os.path.basename(path))[0]
            string_list.append(codename)
            if codename == game_item.config.info.codename:
                codename_index = i

        self.codename_combo.set_model(string_list)
        if codename_index is not None:
            self.codename_combo.set_selected(codename_index)

        for overwrite_switch, switch, key in self.switches_list:
            if getattr(game_item.config.options, key) is not None:  # overwritten
                overwrite_switch.set_active(True)
                if getattr(game_item.config.options, key) is True:
                    switch.set_active(True)
                else:
                    switch.set_active(False)
            elif getattr(self.rencher_config, key) is True:  # default
                switch.set_active(True)
                overwrite_switch.set_active(False)
            else:
                overwrite_switch.set_active(False)
                switch.set_active(False)

    @override
    def do_closed(self):
        if not Path(self.game_item.top_dir).is_dir():
            return  # it got deleted

        sel_codename = self.codename_combo.get_selected_item()
        if not isinstance(sel_codename, Gtk.StringObject):
            logging.error(f'"{self.game_item.game.top_dir.stem}" has no scripts! Ignoring for now')
            return

        if self.game_item.name != self.nickname_entry.get_text():
            self.game_item.config.info.nickname = self.nickname_entry.get_text()
        if self.game_item.codename != sel_codename.get_string():
            self.game_item.config.info.codename = sel_codename.get_string()
        # self.game.config.options.save_slot = self.options_save_slot.get_text()

        for overwrite_switch, switch, key in self.switches_list:
            if overwrite_switch.get_active():
                if switch.get_active():
                    setattr(self.game_item.config.options, key, True)
                else:
                    setattr(self.game_item.config.options, key, False)
            else:
                setattr(self.game_item.config.options, key, None)

        self.game_item.config.save()
        self.game_item.refresh()

    @gtk_template_callback
    def on_switch_changed(self, _widget: Gtk.Switch | Adw.SwitchRow, _):
        for overwrite_switch, switch, key in self.switches_list:
            if _widget == overwrite_switch:
                if getattr(self.rencher_config, key) is True:
                    switch.set_active(True)
                else:
                    switch.set_active(False)

    @gtk_template_callback
    def on_dir_clicked(self, _widget: Gtk.Button):
        open_file_manager(str(self.game_item.top_dir))

    @gtk_template_callback
    def on_clear_info(self, _widget: Adw.ButtonRow):  # type: ignore
        dialog = Adw.AlertDialog(
            heading=_('Are you sure?'),
            body=_('This will permanently reset all user data for "{}".\nThis action cannot be undone.')
                .format(self.game_item.name),
        )
        dialog.add_response('cancel', _('No'))
        dialog.add_response('ok', _('Yes'))
        dialog.set_response_appearance('ok', Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.set_default_response('cancel')
        dialog.set_close_response('cancel')
        dialog.choose(self)
        dialog.connect('response', self.on_clear_info_response)

    def on_clear_info_response(self, _dialog: Adw.AlertDialog, response: str):
        if response == 'ok':
            # slaughter time
            # self.entry.config.info.nickname = ''
            self.game_item.config.info.last_played = 0.0
            self.game_item.config.info.playtime = 0.0

            # self.entry.config.options.skip_splash_scr = None
            # self.entry.config.options.skip_main_menu = None
            # self.entry.config.options.forced_save_dir = None

            self.game_item.config.save()

            toast = Adw.Toast(
                title=_('"{}" stats have been reset').format(self.game_item.name),
                timeout=5,
            )
            self.add_toast(toast)

    @gtk_template_callback
    def on_delete_game(self, _widget: Adw.ButtonRow):
        if self.rencher_config.use_trash:
            self.on_delete_game_response(None, 'ok')
            return

        dialog = Adw.AlertDialog(
            heading=_('Are you sure?'),
            body=_('This will permanently delete "{}".\nThis action cannot be undone.').format(self.game_item.name),
        )
        dialog.add_response('cancel', _('No'))
        dialog.add_response('ok', _('Yes'))
        dialog.set_response_appearance('ok', Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.set_default_response('cancel')
        dialog.set_close_response('cancel')
        dialog.choose(self)
        dialog.connect('response', self.on_delete_game_response)

    def on_delete_game_response(self, _dialog: Adw.AlertDialog | None, response: str):
        if response == 'ok':
            self.activate_action('library.delete-game', GLib.Variant('s', self.game_item.top_dir))
            self.close()
