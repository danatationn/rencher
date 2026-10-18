import os
import sys
from enum import Enum
from gettext import gettext as _
from pathlib import Path
from typing import TYPE_CHECKING

from gi.repository import Adw, GLib, Gtk

from rencher.gtk.game_item import GameItem
from rencher.gtk.library import Library
from rencher.gtk.rpc import Rpc
from rencher.gtk.tasks import DeleteGameTask, RencherTask, TaskError
from rencher.gtk.utils import gtk_template_callback, gtk_template_child
from rencher.gtk.widgets.codename_dialog import CodenameDialog
from rencher.gtk.widgets.game_page import GamePage
from rencher.gtk.widgets.game_row import GameRow
from rencher.gtk.widgets.import_dialog import ImportDialog
from rencher.gtk.widgets.settings_dialog import SettingsDialog
from rencher.gtk.widgets.task_alert_dialog import TaskAlertDialog
from rencher.gtk.widgets.traceback_dialog import TaskTracebackDialog
from rencher.renpy.config import get_rencher_settings

if TYPE_CHECKING:
    from rencher.gtk.application import MainApplication

class SortComboEnum(Enum):
    NAME = 0
    LAST_PLAYED = 1
    PLAYTIME = 2
    ADDED_ON = 3

@Gtk.Template.from_resource('/com/github/danatationn/rencher/ui/window.ui')
class MainWindow(Adw.Window):
    __gtype_name__: str = 'MainWindow'

    # variables
    rows: dict[GameItem, GameRow]
    games: dict[GameRow, GameItem]
    game_views: dict[GameItem, GamePage]
    task_rows: dict[RencherTask, GameRow]
    toasts: dict[GameRow, Adw.Toast]

    filter_text: str = ''
    combo_index: SortComboEnum = SortComboEnum.NAME
    ascending_order: bool

    # classes
    app: 'MainApplication'
    settings_dialog: SettingsDialog
    import_dialog: ImportDialog
    library: Library
    error_dialog: Adw.AlertDialog | None
    rpc: Rpc

    # templates
    toast_overlay: Adw.ToastOverlay = gtk_template_child()
    split_view: Adw.NavigationSplitView = gtk_template_child()
    library_list_box: Gtk.ListBox = gtk_template_child()
    library_view_stack: Adw.ViewStack = gtk_template_child()
    library_search_entry: Gtk.SearchEntry = gtk_template_child()
    library_search_button: Gtk.ToggleButton = gtk_template_child()
    collapse_breakpoint: Adw.Breakpoint = gtk_template_child()

    def __init__(self, application: 'MainApplication'):
        super().__init__(application=application)

        self.rows = {}
        self.games = {}
        self.game_views = {}
        self.task_rows = {}
        self.toasts = {}

        self.app = application
        self.library = Library()
        self.insert_action_group('library', self.library.action_group)
        self.library.connect('game-added', self._on_game_added)
        self.library.connect('game-unknown-exec', self._on_game_unknown_exec)
        self.library.connect('game-changed', self._on_game_changed)
        self.library.connect('game-removed', self._on_game_removed)
        self.library.connect('task-started', self._on_task_started)
        self.library.connect('task-finished', self._on_task_finished)
        self.library.connect('message', self._on_message)

        self.rpc = Rpc(1485229562123124818)
        self.insert_action_group('rpc', self.rpc.action_group)

        if get_rencher_settings().discord_rpc:
            self.activate_action('rpc.start')

        self.ascending_order = False
        self.library_list_box.set_sort_func(self.sort_func)
        self.library_list_box.set_filter_func(self.filter_func)

        self.import_dialog = ImportDialog(self)
        self.settings_dialog = SettingsDialog(self)

        self.error_dialog = None

        GLib.idle_add(self.library.load_games)
        GLib.idle_add(self.settings_dialog.set_reduced_motion)

        # add devel style if running from meson
        if os.environ.get('MESON_BUILD_ROOT', None):
            self.add_css_class('devel')

        # gtk on windows CANNOT do hidpi yet (it does integer scaling but blah).
        # it only scales up the font which is pathetic
        # because of this, `sp` would break, as the font would be wayyy bigger,
        # but the window would remain the same size.
        # WORKAROUND: force `px` for now.
        if sys.platform in ('win32', 'msys'):
            self.collapse_breakpoint.set_condition(
                Adw.BreakpointCondition.parse('max-width: 540px'),
            )

    def _on_game_added(self, _library: Library, game_item: GameItem) -> None:
        row = GameRow(game_item)
        self.rows[game_item] = row
        self.games[row] = game_item

        GLib.idle_add(self.library_list_box.append, row)
        self.library_search_button.set_sensitive(True)

        if not self.library_list_box.get_selected_row():
            self.library_view_stack.set_visible_child_name('game-select')
        self.library_list_box.invalidate_sort()

    def _on_game_changed(self, _library: Library, game_item: GameItem) -> None:
        game_item.refresh()  # gamepage + the row binds item properties. this updates every label
        # self.library_list_box.invalidate_sort()

    def _on_game_removed(self, _library: Library, game_item: GameItem) -> None:
        row = self.rows.get(game_item)
        if not row:
            return
        if row.task and (row.task.error or row.task.warnings):
            # if a game was deleted and there were errors, the user should at least know
            return

        self._remove_row(row, game_item)

    def _remove_row(self, row: GameRow, game_item: GameItem | None) -> None:
        if game_item:
            self.rows.pop(game_item, None)
            if view := self.game_views.pop(game_item, None):
                # line below is required because of https://gitlab.gnome.org/GNOME/libadwaita/-/work_items/1163
                # also i love how the issue was instaclosed just because it was made with ai . At Least fix it please
                view.set_visible(False)
                self.library_view_stack.remove(view)
        self.games.pop(row, None)

        def _do_remove() -> bool:
            """removes the row and then selects something else"""
            self._select_adjacent_row(row)
            self.library_list_box.remove(row)

            return GLib.SOURCE_REMOVE

        GLib.idle_add(_do_remove)

        if len(self.library.store) == 0:
            self.library_view_stack.set_visible_child_name('empty')
            self.library_search_button.set_sensitive(False)

    def _on_task_started(self, _library: Library, task: RencherTask, game_item: GameItem | None) -> None:
        if not game_item:
            # add the button to promise that a game is coming
            row = GameRow(None, task.label)
            self.library_list_box.append(row)
            self.task_rows[task] = row
        else:
            # a game has been added
            if not (row := self.rows.get(game_item)):
                row = GameRow(game_item)
                self.rows[game_item] = row
                self.library_list_box.append(row)
            self.task_rows[task] = row

            if isinstance(task, DeleteGameTask):
                self._select_adjacent_row(row)

        row.set_task(task)
        self.library_list_box.invalidate_sort()

    def _on_task_finished(self, _library: Library, task: RencherTask, game_item: GameItem | None) -> None:
        row = self.task_rows.get(task)
        if not row:
            return

        if game_item and not row.game_item and not task.error:
            # it finished the task! yay
            row.set_game_item(game_item)
            row.set_task(None)
            self.rows[game_item] = row
            self.games[row] = game_item

        # check exit status. if something went wrong then set up traceback dialog
        if task.error or task.warnings:
            toast = Adw.Toast(button_label=_('Details'), timeout=0)

            if task.error:
                toast.set_title(_('"{}" has failed!').format(task.label))
            else:  # warnings
                toast.set_title(_('"{}" has finished with warnings!').format(task.label))

            toast.connect('button-clicked', lambda *_: self._show_task_dialog(row))

            self.toasts[row] = toast
            toast.connect('dismissed', lambda *_: self.toasts.pop(row, None))
            self.toast_overlay.add_toast(toast)
        else:
            self.task_rows.pop(task, None)
            if row.game_item:
                row.set_task(None)
            else:
                GLib.idle_add(self.library_list_box.remove, row)
        # self.library_list_box.invalidate_sort()

    def _on_message(self, _task: RencherTask, text: str) -> None:
        toast = Adw.Toast.new(text)
        toast.set_timeout(3)
        self.toast_overlay.add_toast(toast)

    def _select_adjacent_row(self, row: GameRow) -> None:
        """selects either the next or previous row if either exist"""
        was_selected = row == self.library_list_box.get_selected_row()
        next_row = row.get_next_sibling() or row.get_prev_sibling()

        if not next_row:
            return
        if not isinstance(next_row, GameRow):
            return

        def _select():
            if next_row.get_parent() is self.library_list_box:
                self.library_list_box.select_row(next_row)
            return GLib.SOURCE_REMOVE

        if was_selected and next_row:
            GLib.idle_add(_select)

    def _show_task_dialog(self, row: GameRow) -> None:
        if (toast := self.toasts.get(row)):
            toast.dismiss()

        task = row.task
        if not task:
            return
        if task.error and not isinstance(task.error, TaskError):
            dialog = TaskTracebackDialog(task)
        else:
            dialog = TaskAlertDialog(task)

        dialog.connect('closed', lambda *_: self._on_task_dialog_closed(row, task))
        dialog.present(self)

    def _on_task_dialog_closed(self, row: GameRow, task: RencherTask):
        if row.task is not task:
            # row has a new task i.e. a retry. don't remove it
            return

        del self.task_rows[task]

        if row.game_item and self.library.find(row.game_item.top_dir):
            # game is still in library. don't remove
            row.set_task(None)
        else:
            self._remove_row(row, row.game_item)

    def _on_game_unknown_exec(self, library: Library, game_item: GameItem):
        # TODO right now this shows all dialogs all at once.
        # it's not a big deal if you only have a couple games that are broken,
        # but it is when there's a lot.
        # i'll add a queue thing later
        CodenameDialog(library, game_item).present(self)

    @gtk_template_callback
    def on_import_clicked(self, _button: Gtk.Button | None = None) -> None:
        self.import_dialog.do_show()
        self.import_dialog.present(self)

    @gtk_template_callback
    def on_row_activated(self, _widget: Gtk.ListBox, row: GameRow | None) -> None:
        if row and row.task and (row.task.error or row.task.warnings):
            if row in self.toasts:
                toast = self.toasts.get(row)
                assert(isinstance(toast, Adw.Toast))
                toast.dismiss()
                # del self.toasts[row]
            self._show_task_dialog(row)

    @gtk_template_callback
    def on_game_selected(self, _widget: Gtk.ListBox, row: GameRow | None) -> None:
        if row:
            if game_item := self.games.get(row):
                if not Path(game_item.top_dir).is_dir():
                    self.library.remove_game(game_item.top_dir)
                    self.toast_overlay.add_toast(
                        Adw.Toast(title=_('This game is missing!')),
                    )
                    return

                view = self.game_views.get(game_item, None)

                if not view:
                    view = GamePage(game_item, row, self.library)
                    self.game_views[game_item] = view
                    self.library_view_stack.add_named(view, game_item.top_dir)

                self.library_view_stack.set_visible_child_name(game_item.top_dir)
        else:
            self.library_view_stack.set_visible_child_name('game-select')

    @gtk_template_callback
    def on_hide_sidebar(self, _widget: Gtk.Button) -> None:
        self.split_view.set_show_content(True)

    @gtk_template_callback
    def on_search_changed(self, _widget: Gtk.SearchEntry):
        self.filter_text = _widget.get_text()
        self.library_list_box.invalidate_filter()

    @gtk_template_callback
    def on_combo_changed(self, _widget: Gtk.DropDown, _):
        self.combo_index = SortComboEnum(_widget.get_selected())
        self.library_list_box.invalidate_sort()

    @gtk_template_callback
    def on_order_changed(self, _widget: Gtk.ToggleButton):
        self.ascending_order = _widget.get_active()
        self.library_list_box.invalidate_sort()

    @gtk_template_callback
    def on_search_toggled(self, _widget: Gtk.ToggleButton):
        if not _widget.get_active():
            self.library_search_entry.set_text('')

    def filter_func(self, widget: GameRow) -> bool:
        if not self.filter_text:
            return True
        elif self.filter_text.lower() in widget.button_row.get_title().lower():
            return True
        # elif widget.game_item and self.filter_text.lower() in widget.game_item.top_dir.lower():
            # return True
        else:
            return False

    def sort_func(self, one: GameRow, two: GameRow) -> int:
        item_one = self.games.get(one, None)
        item_two = self.games.get(two, None)

        one_value: str | int | float
        two_value: str | int | float

        # game is currently importing . so whatevsif not item_one or not item_two:
        if one.task or two.task:
            if self.combo_index == SortComboEnum.NAME:
                one_value = one.button_row.get_title().lower()
                two_value = two.button_row.get_title().lower()
            else:
                return 0
        elif not item_one or not item_one.game or not item_two or not item_two.game:
            return 0
        else:
            if self.combo_index == SortComboEnum.NAME:
                one_value = item_one.name.lower()
                two_value = item_two.name.lower()
            elif self.combo_index == SortComboEnum.LAST_PLAYED:
                one_value = item_one.game.config.info.last_played
                two_value = item_two.game.config.info.last_played
            elif self.combo_index == SortComboEnum.PLAYTIME:
                one_value = item_one.game.config.info.playtime
                two_value = item_two.game.config.info.playtime
            elif self.combo_index == SortComboEnum.ADDED_ON:
                one_value = item_one.game.config.info.added_on
                two_value = item_two.game.config.info.added_on
            else:
                return 0

        if one_value < two_value:  # pyright: ignore[reportOperatorIssue]
            res = 1
        elif one_value > two_value:  # pyright: ignore[reportOperatorIssue]
            res = -1
        else:
            res = 0

        # 'b' > 'a' so we need to invert these
        if self.ascending_order and self.combo_index == SortComboEnum.NAME:
            return res
        elif self.ascending_order:
            return -res
        elif self.combo_index == SortComboEnum.NAME:
            return -res
        else:
            return res
