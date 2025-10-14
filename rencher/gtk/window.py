import logging
import os.path
import subprocess
import sys
import time
from typing import TYPE_CHECKING

from gi.repository import Adw, GLib, Gtk
from thefuzz.fuzz import partial_token_sort_ratio

from rencher import tmp_path
from rencher.gtk import open_file_manager
from rencher.gtk.codename_dialog import RencherCodename
from rencher.gtk.game_item import GameItem
from rencher.gtk.import_dialog import RencherImport
from rencher.gtk.library import RencherLibrary
from rencher.gtk.options_dialog import RencherOptions
from rencher.gtk.settings_dialog import RencherSettings
from rencher.renpy.game import Game

if TYPE_CHECKING:
    from rencher.gtk.application import RencherApplication

filename = os.path.join(tmp_path, 'rencher/gtk/ui/window.ui')
@Gtk.Template(filename=str(filename))
class RencherWindow(Adw.ApplicationWindow):
    __gtype_name__ = 'RencherWindow'

    """ variables """
    game_process: subprocess.Popen | None = None
    process_time: float = None
    process_row: Gtk.ListBoxRow | None = None
    is_terminating: bool = False
    filter_text: str = ''
    combo_index: int = 0
    ascending_order: bool = False
    pause_monitoring: str = None
    current_game: GameItem = None

    """ classes """
    application: 'RencherApplication'
    settings_dialog: RencherSettings
    import_dialog: RencherImport
    options_dialog: RencherOptions
    codename_dialog: RencherCodename
    library: RencherLibrary

    """ templates """
    toast_overlay: Adw.ToastOverlay = Gtk.Template.Child()
    split_view: Adw.OverlaySplitView = Gtk.Template.Child()
    library_list_box: Gtk.ListBox = Gtk.Template.Child()
    selected_status_page: Adw.ViewStackPage = Gtk.Template.Child()
    library_view_stack: Adw.ViewStack = Gtk.Template.Child()
    play_button: Gtk.Button = Gtk.Template.Child()

    last_played_row: Adw.ActionRow = Gtk.Template.Child()
    playtime_row: Adw.ActionRow = Gtk.Template.Child()
    added_on_row: Adw.ActionRow = Gtk.Template.Child()
    rpath_row: Adw.ActionRow = Gtk.Template.Child()
    version_row: Adw.ActionRow = Gtk.Template.Child()
    codename_row: Adw.ActionRow = Gtk.Template.Child()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not getattr(sys, 'frozen', False):
            self.get_style_context().add_class('devel')

        self.application = self.get_application()  # type: ignore
        self.filemonitor = self.application.file_monitor
        self.library = RencherLibrary(self)
        self.import_dialog = RencherImport(self)
        self.options_dialog = RencherOptions(self)
        self.settings_dialog = RencherSettings(self)
        self.codename_dialog = RencherCodename(self)
        self.library_list_box.set_sort_func(self.sort_func)
        self.library_list_box.set_filter_func(self.filter_func)
        
        self.split_view.set_show_sidebar(False)

        self.library.connect('game-added', self.on_game_added)
        self.library.connect('game-removed', self.on_game_removed)
        self.library.connect('game-changed', self.on_game_changed)
        self.library.load_games()

        GLib.timeout_add(250, self.check_process)

    def on_game_added(self, _, game_item: GameItem):
        button = Adw.ButtonRow(title=game_item.name)  # type: ignore
        button.game = game_item.game
        self.library_list_box.append(button)
        if self.library_list_box.get_selected_row():
            self.library_view_stack.set_visible_child_name('selected')
        else:
            self.library_view_stack.set_visible_child_name('game-select')
        self.split_view.set_show_sidebar(True)

    def on_game_removed(self, _, game_item: GameItem):
        for row in list(self.library_list_box):  # type: ignore
            if getattr(row, 'game', None) == game_item.game:
                self.library_list_box.remove(row)

        if len(list(self.library_list_box)) == 0:
            self.library_view_stack.set_visible_child_name('empty')
            self.split_view.set_show_sidebar(False)

    def on_game_changed(self, _, game_item: GameItem):
        if not self.current_game:
            return
        if self.current_game.rpath == game_item.rpath:
            self.current_game.refresh()
        
        for row in self.library_list_box:  # type: ignore
            if getattr(row, 'game', None) == game_item.game:
                logging.debug(f'Changing row name {row.get_title()} -> {game_item.game.get_name()}')
                row.set_title(game_item.game.get_name())
                break

    @Gtk.Template.Callback()
    def on_import_clicked(self, _widget: Adw.ButtonRow) -> None:  # type: ignore
        if not self.import_dialog.thread.is_alive():
            self.import_dialog.force_close()
            self.import_dialog = RencherImport(self)

        self.import_dialog.present(self)

    @Gtk.Template.Callback()
    def on_settings_clicked(self, _widget: Gtk.Button) -> None:
        self.settings_dialog.present(self)
        self.settings_dialog.on_show()

    @Gtk.Template.Callback()
    def on_play_clicked(self, _widget: Gtk.Button) -> None:
        selected_button_row = self.library_list_box.get_selected_row()
        game = getattr(selected_button_row, 'game', None)
        if isinstance(game, Game) and not game.is_launchable:
            # duct tape fix
            return

        if _widget.get_style_context().has_class('suggested-action'):
            self.game_process = game.run()
            self.process_time = time.time()
            self.check_process()  # so the button changes instantly
            self.process_row = selected_button_row
            self.application.pause_monitor(game.rpath)
        else:
            if self.game_process:
                self.play_button.set_label('Stopping')
                self.is_terminating = True
                self.game_process.terminate()

    @Gtk.Template.Callback()
    def on_dir_clicked(self, _widget: Gtk.Button) -> None:
        selected_button_row = self.library_list_box.get_selected_rows()[0]
        project = getattr(selected_button_row, 'game', None)
        if project.apath:
            open_file_manager(str(project.apath))

    @Gtk.Template.Callback()
    def on_game_selected(self, _widget: Gtk.ListBox, row: Gtk.ListBoxRow) -> None:
        if row:
            self.library_view_stack.set_visible_child_name('selected')
        else:
            self.library_view_stack.set_visible_child_name('game-select')
        
        game = getattr(row, 'game', None)
        if isinstance(game, Game):
            if self.current_game is None:
                self.current_game = GameItem(game=game)
                self.current_game.bind_property('name', self.selected_status_page, 'title')
                self.current_game.bind_property('last_played', self.last_played_row, 'subtitle')
                self.current_game.bind_property('playtime', self.playtime_row, 'subtitle')
                self.current_game.bind_property('added_on', self.added_on_row, 'subtitle')
                self.current_game.bind_property('version', self.version_row, 'subtitle')
                self.current_game.bind_property('rpath', self.rpath_row, 'subtitle')
                self.current_game.bind_property('codename', self.codename_row, 'subtitle')
                self.current_game.refresh()
            else:
                self.current_game.game = game
                self.current_game.refresh()

    @Gtk.Template.Callback()
    def on_search_changed(self, _widget: Gtk.SearchEntry):
        self.filter_text = _widget.get_text()
        self.library_list_box.invalidate_filter()

    @Gtk.Template.Callback()
    def on_combo_changed(self, _widget: Gtk.DropDown, _):
        self.combo_index = _widget.get_selected()
        self.library_list_box.invalidate_sort()

    @Gtk.Template.Callback()
    def on_order_changed(self, _widget: Gtk.ToggleButton):
        self.ascending_order = _widget.get_active()
        self.library_list_box.invalidate_sort()

    @Gtk.Template.Callback()
    def on_options_clicked(self, _widget: Gtk.Button):
        selected_button_row = self.library_list_box.get_selected_row()
        game = getattr(selected_button_row, 'game', None)

        self.options_dialog.change_game(game)
        self.options_dialog.present(self)

    def check_process(self) -> bool:
        if not self.game_process or self.game_process.poll() is not None:
            self.play_button.set_label('Play')
            self.play_button.get_style_context().remove_class('destructive-action')
            self.play_button.get_style_context().add_class('suggested-action')
            self.is_terminating = False

            if self.game_process is None:
                return True  # don't even bother looking down

            apath = os.path.abspath(os.path.join(self.game_process.args[0], '..', '..', '..'))  # we hate os.path
            game = Game(apath=apath)
            playtime = game.config.get_value('playtime')
            if self.process_time:
                playtime += time.time() - self.process_time
            game.cleanup(playtime)
            self.application.resume_monitor(game.rpath)

            self.game_process = None
            self.process_row = None

        else:
            if self.is_terminating:
                self.play_button.set_label('Stopping')
            else:
                self.play_button.set_label('Stop')
            self.play_button.get_style_context().remove_class('suggested-action')
            self.play_button.get_style_context().add_class('destructive-action')
        return True

    def filter_func(self, widget: Gtk.ListBoxRow) -> bool:
        if not self.filter_text:
            return True
        
        if hasattr(widget, 'game'):
            fuzz = partial_token_sort_ratio(widget.game.name, self.filter_text)
            if fuzz > 90:
                return True
        return False

    def sort_func(self, one: Adw.ActionRow, two: Adw.ActionRow) -> int:
        if self.combo_index == 0:
            # b > a so we invert these
            game_one = two.game.name.lower()
            game_two = one.game.name.lower()
        elif self.combo_index == 1:
            game_one = one.game.config['info'].get('last_played', 0)
            game_two = two.game.config['info'].get('last_played', 0)
        elif self.combo_index == 2:
            game_one = float(one.game.config['info'].get('playtime', 0))
            game_two = float(two.game.config['info'].get('playtime', 0))
        else:
            game_one = one.game.config['info'].get('added_on', 0)
            game_two = two.game.config['info'].get('added_on', 0)

        if game_one < game_two:
            res = 1
        elif game_one > game_two:
            res = -1
        else:
            res = 0

        if self.ascending_order:
            return -res
        else:
            return res