import glob
import os.path

from gi.repository import Adw, Gtk

from rencher.renpy.game import Game


class RencherCodename(Adw.AlertDialog):
    game: Game = None

    def __init__(self, parent: Adw.ApplicationWindow):
        super().__init__()

        self.list_box = Gtk.ListBox()
        self.list_box.add_css_class('boxed-list')
        self.set_extra_child(self.list_box)

        self.add_response('ok', 'OK')
        self.set_default_response('ok')

        self.connect('response', self.on_response)

    def change_game(self, rpath: str) -> None:
        self.game = Game(rpath=rpath)
        self.list_box.remove_all()

        self.set_heading('Select Mod Executable')
        self.set_body( f'The mod "{self.game.name}" provides multiple executables.\n'
                       'Please choose the correct one below.\n'
                       '(You can change this later in settings.)')

        py_files = glob.glob(os.path.join(self.game.apath, '*.py'))
        for path in py_files:
            name = os.path.basename(path)
            row = Adw.ActionRow(title=name)
            self.list_box.append(row)

    def on_response(self, *_):
        selected_row = self.list_box.get_selected_row()  # do some linter shutting up here
        codename = selected_row.get_title()
        self.game.config['info']['codename'] = codename
        self.game.config.write()