import asyncio
import logging
import subprocess
import threading
import time
from typing import IO, TYPE_CHECKING

from gi.repository import Adw, GLib, Gtk

from rencher.gtk.codename_dialog import RencherCodename
from rencher.gtk.filemonitor import RencherFileMonitor
from rencher.gtk.game_entry import GameEntry
from rencher.gtk.import_dialog import ImportDialog
from rencher.gtk.library import Library
from rencher.gtk.options_dialog import OptionsDialog
from rencher.gtk.settings_dialog import SettingsDialog
from rencher.gtk.tasks import PiePaintable, TasksPopover
from rencher.gtk.utils import open_file_manager

if TYPE_CHECKING:
    from rencher.gtk.application import MainApplication

@Gtk.Template.from_resource('/com/github/danatationn/rencher/ui/window.ui')
class MainWindow(Adw.ApplicationWindow):
    __gtype_name__: str = 'MainWindow'

    # variables
    rows: dict[GameEntry, Gtk.ListBoxRow]
    games: dict[Gtk.ListBoxRow, GameEntry]
    current_game_entry: GameEntry
    running: GameEntry | None

    game_process: subprocess.Popen[bytes] | None
    process_time: float
    is_terminating: bool
    pause_monitoring: str

    filter_text: str = ''
    combo_index: int = 0
    ascending_order: bool
    log_buf: Gtk.TextBuffer

    # classes
    app: 'MainApplication'
    settings_dialog: SettingsDialog
    import_dialog: ImportDialog
    options_dialog: OptionsDialog
    codename_dialog: RencherCodename
    filemonitor: RencherFileMonitor
    library: Library
    tasks_popover: TasksPopover
    pie: PiePaintable
    pie_image: Gtk.Image

    # templates
    toast_overlay: Adw.ToastOverlay = Gtk.Template.Child()
    window_progress_bar: Gtk.ProgressBar = Gtk.Template.Child()
    split_view: Adw.OverlaySplitView = Gtk.Template.Child()
    library_list_box: Gtk.ListBox = Gtk.Template.Child()
    selected_status_page: Adw.ViewStackPage = Gtk.Template.Child()
    library_view_stack: Adw.ViewStack = Gtk.Template.Child()
    play_button: Gtk.Button = Gtk.Template.Child()
    options_button: Gtk.Button = Gtk.Template.Child()
    pie_progress_button: Gtk.MenuButton = Gtk.Template.Child()
    library_search_entry: Gtk.SearchEntry = Gtk.Template.Child()

    last_played_row: Adw.ActionRow = Gtk.Template.Child()
    playtime_row: Adw.ActionRow = Gtk.Template.Child()
    added_on_row: Adw.ActionRow = Gtk.Template.Child()
    rpath_row: Adw.ActionRow = Gtk.Template.Child()
    version_row: Adw.ActionRow = Gtk.Template.Child()
    codename_row: Adw.ActionRow = Gtk.Template.Child()
    log_row: Adw.ExpanderRow = Gtk.Template.Child()
    log_text_view: Gtk.TextView = Gtk.Template.Child()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.rows = {}
        self.games = {}
        self.game_process = None
        self.running = None
        self.is_terminating = False
        self.ascending_order = False

        self.app = self.get_application()  # pyright: ignore[reportAttributeAccessIssue]
        self.library = Library(self)
        self.library.connect('game-added', self._on_game_added)
        self.library.connect('game-changed', self._on_game_changed)
        self.library.connect('game-removed', self._on_game_removed)
        self.library_list_box.set_sort_func(self.sort_func)
        self.library_list_box.set_filter_func(self.filter_func)
        self.filemonitor = RencherFileMonitor(self.library)

        self.current_game_entry = GameEntry()
        self.current_game_entry.bind_property('name', self.selected_status_page, 'title')
        self.current_game_entry.bind_property('last_played', self.last_played_row, 'subtitle')
        self.current_game_entry.bind_property('playtime', self.playtime_row, 'subtitle')
        self.current_game_entry.bind_property('added_on', self.added_on_row, 'subtitle')
        self.current_game_entry.bind_property('version', self.version_row, 'subtitle')
        self.current_game_entry.bind_property('rpath', self.rpath_row, 'subtitle')
        self.current_game_entry.bind_property('codename', self.codename_row, 'subtitle')

        self.import_dialog = ImportDialog(self)
        self.options_dialog = OptionsDialog(self)
        self.settings_dialog = SettingsDialog(self)
        self.codename_dialog = RencherCodename(self)

        self.pie = PiePaintable()
        self.pie_image = Gtk.Image.new_from_paintable(self.pie)
        self.tasks_popover = TasksPopover(self)
        self.pie_progress_button.set_popover(self.tasks_popover)
        self.log_buf = self.log_text_view.get_buffer()
        self.log_buf.connect('changed', lambda b: self.log_row.set_sensitive(b.get_char_count() > 0))

        GLib.idle_add(self.library.load_games)
        GLib.timeout_add(250, self.check_process)

    def _on_game_added(self, _, entry: GameEntry) -> None:
        row = Adw.ButtonRow(title=entry.name)
        self.rows[entry] = row
        self.games[row] = entry
        GLib.idle_add(self.library_list_box.append, row)
        self.split_view.set_show_sidebar(True)
        if not self.library_list_box.get_selected_row():
            self.library_view_stack.set_visible_child_name('game-select')

    def _on_game_changed(self, _, entry: GameEntry) -> None:
        if self.current_game_entry == entry:
            self.current_game_entry.refresh(entry.game)

        entry.refresh(entry.game)

        if row := self.rows.get(entry, None):
            GLib.idle_add(row.set_title, entry.name)  # pyright: ignore[reportAttributeAccessIssue]

    def _on_game_removed(self, _, entry: GameEntry) -> None:
        row = self.rows.pop(entry, None)
        if row:
            self.games.pop(row, None)
            GLib.idle_add(self.library_list_box.remove, row)

        if len(self.library.store) == 0:
            self.library_view_stack.set_visible_child_name('empty')
            self.split_view.set_show_sidebar(False)

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
        selected_row = self.library_list_box.get_selected_row()
        if not selected_row:
            return
        if not (entry := self.games.get(selected_row, None)) or not entry.game:
            return

        if not entry.game.is_launchable:
            alert = Adw.AlertDialog(heading='Error', body='This game has no valid executables!')
            alert.add_response('ok', 'OK')
            alert.choose(self)
            return

        if _widget.get_style_context().has_class('suggested-action'):
            self.game_process = entry.game.run()
            self.log_buf.set_text('')
            for stream in (self.game_process.stdout, self.game_process.stderr):
                if stream:
                    threading.Thread(target=self._read_stream, args=(stream,), daemon=True).start()
            self.running = entry
            self.process_time = time.time()
            self.check_process()  # so the button changes instantly
            self.filemonitor.pause_monitor(entry.rpath)
        else:
            if self.game_process:
                self.play_button.set_label('Stopping')
                self.is_terminating = True
                self.game_process.terminate()

    def _read_stream(self, stream: IO[bytes]) -> None:
        for line in stream:
            GLib.idle_add(self._on_log_line, line.decode(errors='replace'))

    def _on_log_line(self, line: str) -> None:
        self.log_buf.insert(self.log_buf.get_end_iter(), line)
        self.log_text_view.scroll_to_iter(self.log_buf.get_end_iter(), 0, False, 0, 0)

    @Gtk.Template.Callback()
    def on_dir_clicked(self, _widget: Gtk.Button) -> None:
        selected_row = self.library_list_box.get_selected_row()
        if not selected_row:
            return
        entry = self.games.get(selected_row, None)
        if entry and entry.apath:
            open_file_manager(entry.apath)

    @Gtk.Template.Callback()
    def on_game_selected(self, _widget: Gtk.ListBox, row: Gtk.ListBoxRow) -> None:
        if row:
            self.library_view_stack.set_visible_child_name('selected')
        # else:
            # self.library_view_stack.set_visible_child_name('game-select')

        if entry := self.games.get(row, None):
            self.current_game_entry.refresh(entry.game)
        elif len(self.games) > 0:
            first_row = next(iter(self.games))
            self.library_list_box.select_row(first_row)

        if not self.running:
            self.log_row.set_expanded(False)
            self.log_buf.set_text('')

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
        selected_row = self.library_list_box.get_selected_row()
        if not selected_row:
            return None
        if (entry := self.games.get(selected_row, None)) and entry.game:
            self.options_dialog.change_game(entry.game)
            self.options_dialog.present(self)

    @Gtk.Template.Callback()
    def on_search_toggled(self, _widget: Gtk.ToggleButton):
        if not _widget.get_active():
            self.library_search_entry.set_text('')

    def check_process(self) -> bool:
        if not self.game_process or self.game_process.poll() is not None:
            self.play_button.set_label('Play')
            self.play_button.get_style_context().remove_class('destructive-action')
            self.play_button.get_style_context().add_class('suggested-action')
            self.options_button.set_sensitive(True)
            self.is_terminating = False

            if self.running is not None:
                self.app.rpc.clear()

            if self.game_process is None or self.running is None or self.running.game is None:
                return True

            playtime = self.running.game.config.get_value('playtime')
            if self.process_time and isinstance(playtime, float):
                playtime += time.time() - self.process_time
                self.running.game.cleanup(playtime)
            self.filemonitor.resume_monitor(self.running.game.rpath)

            self.game_process = None
            self.running = None
        else:
            if self.is_terminating:
                self.play_button.set_label('Stopping')
            else:
                self.play_button.set_label('Stop')
                if self.running and self.running.game and self.running.game.config['overwritten']['discord_rpc'] == 'true':
                    self.app.rpc.update(state=self.running.game.name)
            self.play_button.get_style_context().remove_class('suggested-action')
            self.play_button.get_style_context().add_class('destructive-action')
            self.options_button.set_sensitive(False)
        return True

    def filter_func(self, widget: Adw.ButtonRow) -> bool:
        if not self.filter_text:
            return True
        elif self.filter_text.lower() in widget.get_title().lower():
            return True
        else:
            return False

    def sort_func(self, one: Adw.ActionRow, two: Adw.ActionRow) -> int:
        entry_one = self.games.get(one, None)
        entry_two = self.games.get(two, None)
        if not entry_one or not entry_one.game or not entry_two or not entry_two.game:
            return 0

        one_value: str | int | float
        two_value: str | int | float

        if self.combo_index == 0:
            one_value = entry_one.name.lower()
            two_value = entry_two.name.lower()
        elif self.combo_index == 1:
            one_value = entry_one.game.config['info'].get('last_played', 0)
            two_value = entry_two.game.config['info'].get('last_played', 0)
        elif self.combo_index == 2:
            one_value = float(entry_one.game.config['info'].get('playtime', 0))
            two_value = float(entry_two.game.config['info'].get('playtime', 0))
        else:
            one_value = entry_one.game.config['info'].get('added_on', 0)
            two_value = entry_two.game.config['info'].get('added_on', 0)

        if str(one_value) < str(two_value):
            res = 1
        elif str(one_value) > str(two_value):
            res = -1
        else:
            res = 0

        # 'b' > 'a' so we need to invert these
        if self.ascending_order != self.combo_index == 0:
            return res
        elif self.ascending_order:
            return -res
        elif self.combo_index == 0:
            return -res
        else:
            return res
