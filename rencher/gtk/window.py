import logging
import os.path
import subprocess
import sys
import time
from typing import TYPE_CHECKING

from gi.repository import Adw, GLib, Gtk
from thefuzz.fuzz import partial_token_sort_ratio

from rencher import tmp_path
from rencher.gtk.codename_dialog import RencherCodename
from rencher.gtk.game_item import GameItem
from rencher.gtk.import_dialog import RencherImport
from rencher.gtk.library import RencherLibrary
from rencher.gtk.options_dialog import RencherOptions
from rencher.gtk.settings_dialog import RencherSettings
from rencher.gtk.tasks import PiePaintable, TasksPopover
from rencher.gtk.utils import open_file_manager
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
    current_gameitem: GameItem = None
    rows: dict[GameItem, Adw.ActionRow] = {}

    """ classes """
    application: 'RencherApplication'
    settings_dialog: RencherSettings
    import_dialog: RencherImport
    options_dialog: RencherOptions
    codename_dialog: RencherCodename
    library: RencherLibrary
    tasks_popover: TasksPopover

    """ templates """
    toast_overlay: Adw.ToastOverlay = Gtk.Template.Child()
    window_progress_bar: Gtk.ProgressBar = Gtk.Template.Child()
    split_view: Adw.OverlaySplitView = Gtk.Template.Child()
    library_list_box: Gtk.ListBox = Gtk.Template.Child()
    selected_status_page: Adw.ViewStackPage = Gtk.Template.Child()
    library_view_stack: Adw.ViewStack = Gtk.Template.Child()
    play_button: Gtk.Button = Gtk.Template.Child()
    options_button: Gtk.Button = Gtk.Template.Child()
    pie_progress_button: Gtk.MenuButton = Gtk.Template.Child()

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
        self.library.connect('game-added', self.on_game_added)
        self.library.connect('game-changed', self.on_game_changed)
        self.library.connect('game-removed', self.on_game_removed)
        self.library.load_games()

        self.import_dialog = RencherImport(self)
        self.options_dialog = RencherOptions(self)
        self.settings_dialog = RencherSettings(self)
        self.codename_dialog = RencherCodename(self)
        self.library_list_box.set_sort_func(self.sort_func)
        self.library_list_box.set_filter_func(self.filter_func)

        self.current_gameitem = GameItem()
        self.current_gameitem.bind_property('name', self.selected_status_page, 'title')
        self.current_gameitem.bind_property('last_played', self.last_played_row, 'subtitle')
        self.current_gameitem.bind_property('playtime', self.playtime_row, 'subtitle')
        self.current_gameitem.bind_property('added_on', self.added_on_row, 'subtitle')
        self.current_gameitem.bind_property('version', self.version_row, 'subtitle')
        self.current_gameitem.bind_property('rpath', self.rpath_row, 'subtitle')
        self.current_gameitem.bind_property('codename', self.codename_row, 'subtitle')

        self.pie = PiePaintable()
        self.pie_image = Gtk.Image.new_from_paintable(self.pie)
        self.tasks_popover = TasksPopover(self)
        self.pie_progress_button.set_popover(self.tasks_popover)

        GLib.timeout_add(250, self.check_process)

    def on_game_added(self, _, game_item: GameItem):
        row = Adw.ButtonRow(title=game_item.name)  # type: ignore
        row.game = game_item.game
        self.library_list_box.append(row)
        self.rows[game_item] = row
        if self.library_list_box.get_selected_row():
            self.library_view_stack.set_visible_child_name('selected')
        else:
            self.library_view_stack.set_visible_child_name('game-select')
        self.split_view.set_show_sidebar(True)

    def on_game_removed(self, _, game_item: GameItem):
        if game_item in self.rows:
            row = self.rows[game_item]
            if getattr(row, 'game', None) == game_item.game:
                self.library_list_box.remove(row)
                del self.rows[game_item]

        if len(self.rows) == 0:
            self.library_view_stack.set_visible_child_name('empty')
            self.split_view.set_show_sidebar(False)

    def on_game_changed(self, _, game_item: GameItem):
        if not self.current_gameitem:
            return
        if self.current_gameitem.rpath == game_item.rpath:
            self.current_gameitem.refresh(game_item.game)

        if game_item in self.rows:
            row = self.rows[game_item]
            game = getattr(row, 'game', None)
            if game == game_item.game and game.name != game_item.name:
                logging.debug(f'Changing row name {row.get_title()} -> {game_item.game.get_name()}')
                row.set_title(game_item.game.get_name())

    def update_pie_paintable(self):
        fraction = self.tasks_popover.get_total_fraction()

        if fraction < 1.0 and fraction != 0.0:
            self.pie_progress_button.set_child(self.pie_image)
            self.pie.set_fraction(fraction)
        else:
            self.pie_progress_button.set_icon_name('test-pass')

    @Gtk.Template.Callback()
    def on_import_clicked(self, *_) -> None:  # type: ignore
        self.import_dialog.do_show()
        self.import_dialog.present(self)

    @Gtk.Template.Callback()
    def on_play_clicked(self, _widget: Gtk.Button) -> None:
        selected_button_row = self.library_list_box.get_selected_row()
        game = getattr(selected_button_row, 'game', None)
        if isinstance(game, Game) and not game.is_launchable:
            alert = Adw.AlertDialog(heading='Error', body='This game has no valid executables!')
            alert.add_response('ok', 'OK')
            alert.choose(self)
            return

        if _widget.get_style_context().has_class('suggested-action'):
            self.game_process = game.run
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
            open_file_manager(project.apath)

    @Gtk.Template.Callback()
    def on_game_selected(self, _widget: Gtk.ListBox, row: Gtk.ListBoxRow) -> None:
        if row:
            self.library_view_stack.set_visible_child_name('selected')
        else:
            self.library_view_stack.set_visible_child_name('game-select')
        
        game = getattr(row, 'game', None)
        if isinstance(game, Game):
            self.current_gameitem.refresh(game)

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
            self.options_button.set_sensitive(True)
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
            self.options_button.set_sensitive(False)
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
        game_one = getattr(one, 'game', None)
        game_two = getattr(two, 'game', None)

        if self.combo_index == 0:
            game_one = game_one.name.lower()
            game_two = game_two.name.lower()
        elif self.combo_index == 1:
            game_one = game_one.config['info'].get('last_played', 0)
            game_two = game_two.config['info'].get('last_played', 0)
        elif self.combo_index == 2:
            game_one = float(game_one.config['info'].get('playtime', 0))
            game_two = float(game_two.config['info'].get('playtime', 0))
        else:
            game_one = game_one.config['info'].get('added_on', 0)
            game_two = game_two.config['info'].get('added_on', 0)

        if game_one < game_two:
            res = 1
        elif game_one > game_two:
            res = -1
        else:
            res = 0

        # b > a so we need to invert these
        if self.ascending_order != self.combo_index == 0:
            return res
        elif self.ascending_order:
            return -res
        elif self.combo_index == 0:
            return -res
        else:
            return res