from enum import Enum, auto

from gi.repository import Adw, GObject, Gtk

from rencher.gtk.game_entry import GameEntry
from rencher.gtk.tasks import RencherTask, TaskError


class RowState(Enum):
    NORMAL = auto()
    BUSY = auto()
    WARNINGS = auto()
    SOFT_ERROR = auto()
    FATAL_ERROR = auto()


class GameRow(Gtk.ListBoxRow):
    _entry: GameEntry | None
    _task: RencherTask | None
    # _error: Exception | None
    _button_box: Gtk.Box
    button_row: Adw.ButtonRow
    action_button: Gtk.Button
    pb: Gtk.ProgressBar
    _task_signal_id: int
    _fraction_binding: GObject.Binding | None

    def __init__(self, entry: GameEntry | None = None, fallback_name: str = ''):
        super().__init__()

        if not entry and fallback_name == '':
            raise ValueError('entry or fallback_name are required')

        self._entry = entry
        self._task = None
        self._fraction_binding = None
        self._task_signal_id = 0

        self._button_box = Gtk.Box()

        self.button_row = Adw.ButtonRow(halign=Gtk.Align.START, hexpand=True, can_target=False)
        self._button_box.append(self.button_row)

        self.action_button = Gtk.Button(
            halign=Gtk.Align.END,
            valign=Gtk.Align.CENTER,
            can_target=False,
            visible=False,
        )
        self.action_button.add_css_class('flat')
        self._button_box.append(self.action_button)

        if entry:
            entry.bind_property('name', self.button_row, 'title', GObject.BindingFlags.SYNC_CREATE)
        elif fallback_name != '':
            self.button_row.set_title(fallback_name)

        self.pb = Gtk.ProgressBar(visible=False)
        self.pb.add_css_class('osd')

        overlay = Gtk.Overlay()
        overlay.set_child(self._button_box)
        overlay.add_overlay(self.pb)
        self.set_child(overlay)

    def set_entry(self, entry: GameEntry) -> None:
        if self._entry:
            self._entry.update(entry.game)
        else:
            self._entry = entry
        self._entry.bind_property('name', self.button_row, 'title', GObject.BindingFlags.SYNC_CREATE)

    def set_task(self, task: RencherTask | None) -> None:
        if self._task and self._task_signal_id:
            self._task.disconnect(self._task_signal_id)
            self._task_signal_id = 0

        if self._fraction_binding:
            self._fraction_binding.unbind()
            self._fraction_binding = None

        self._task = task

        if not task:
            self._reset_ui_state()
            return

        self._fraction_binding = task.bind_property(
            'fraction', self.pb, 'fraction', GObject.BindingFlags.SYNC_CREATE,
        )

        self._task_signal_id = task.connect('notify::finished', self._on_task_finished)

        self._update_ui_state()

    def get_state(self) -> RowState:
        if self.task:
            if not self.task.finished:
                return RowState.BUSY
            elif self.task.error:
                if isinstance(self.task.error, TaskError):
                    return RowState.SOFT_ERROR
                else:
                    return RowState.FATAL_ERROR
            elif self.task.warnings:
                return RowState.WARNINGS

        return RowState.NORMAL

    def _on_task_finished(self, _task: RencherTask, _pspec: GObject.ParamSpec) -> None:
        self._update_ui_state()

    def _new_update_ui_state(self) -> None:
        match self.get_state():
            case RowState.NORMAL:
                self._reset_ui_state()
            case RowState.BUSY:
                self.pb.set_visible(True)
                self.set_selectable(False)
                self.set_activatable(False)
                self.button_row.set_sensitive(False)
            case RowState.SOFT_ERROR:
                self.add_css_class('error')
                self.action_button.set_icon_name('exclamation-mark-symbolic')
                self.action_button.set_visible(True)
            case RowState.FATAL_ERROR:
                self.add_css_class('error')
                self.action_button.set_icon_name('error-outline-symbolic')
                self.action_button.set_visible(True)
            case RowState.WARNINGS:
                self.add_css_class('warning')
                self.action_button.set_icon_name('warning-outline-symbolic')
                self.action_button.set_visible(True)

    def _update_ui_state(self) -> None:
        if not self._task:
            self._reset_ui_state()
            return

        self.remove_css_class('error')
        self.remove_css_class('warning')

        if not self._task.finished:
            self.pb.set_visible(True)
            self.set_selectable(False)
            self.set_activatable(False)
            self.button_row.set_sensitive(False)
            return

        self.pb.set_visible(False)
        self.set_selectable(False)
        self.set_activatable(True)
        self.button_row.set_sensitive(True)
        self.action_button.set_visible(True)

        if self._task.error:
            self.add_css_class('error')
            if isinstance(self._task.error, TaskError):
                self.action_button.set_icon_name('exclamation-mark-symbolic')
            else:
                self.action_button.set_icon_name('error-outline-symbolic')
        elif self._task.warnings:
            self.add_css_class('warning')
            self.action_button.set_icon_name('warning-outline-symbolic')
        else:
            self._reset_ui_state()
            # self.action_button.set_visible(False)
            # self.set_task(None)

    def _reset_ui_state(self) -> None:
        self.remove_css_class('error')
        self.remove_css_class('warning')
        # self._task = None
        self.pb.set_visible(False)
        self.pb.set_fraction(0.0)
        self.action_button.set_visible(False)
        self.set_selectable(True)
        self.set_activatable(True)
        self.button_row.set_sensitive(True)
        # self.set_task(None)

    @property
    def task(self) -> RencherTask | None:
        return self._task

    @property
    def entry(self) -> GameEntry | None:
        return self._entry
