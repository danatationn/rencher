import glob
import logging
import os.path
from gettext import gettext as _

from gi.repository import Adw, Gtk

from rencher.gtk.game_entry import GameEntry
from rencher.gtk.library import Library


class CodenameDialog(Adw.AlertDialog):
    library: Library
    entry: GameEntry
    codename_list_box: Gtk.ListBox

    def __init__(self, library: Library, entry: GameEntry):
        super().__init__()
        self.library = library
        self.entry = entry

        self.codename_list_box = Gtk.ListBox()
        self.codename_list_box.add_css_class('boxed-list')
        self.set_extra_child(self.codename_list_box)

        self.add_response('ok', 'OK')
        self.set_default_response('ok')
        self.connect('response', self.on_response)

        self.set_heading(_('Select Mod Executable'))
        self.set_body(f'The mod "{self.entry.name}" provides multiple executables.\n'+
                       'Please choose the correct one below.\n'+
                       '(You can change this later in settings.)')

        py_files = glob.glob(os.path.join(self.entry.apath, '*.py'))
        for path in py_files:
            name = os.path.splitext(os.path.basename(path))[0]
            row = Adw.ActionRow(title=name)
            self.codename_list_box.append(row)

    def on_response(self, _dialog: 'CodenameDialog', _id: str) -> None:
        selected_row = self.codename_list_box.get_selected_row()
        if isinstance(selected_row, Adw.ActionRow):
            codename = selected_row.get_title()
            self.entry.config.set('info', 'codename', codename)
            self.entry.config.write()
            self.library.add_game(self.entry.rpath)
