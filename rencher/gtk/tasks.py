import logging
import os
import threading
from enum import Enum
from math import pi
from types import NoneType
from typing import TYPE_CHECKING

import cairo
from gi.repository import Adw, Gdk, GLib, GObject, Graphene, Gtk

from rencher import tmp_path

if TYPE_CHECKING:
    from rencher.gtk.window import RencherWindow


class TaskTypeEnum(Enum):
    IMPORT = 0
    DELETE = 1
    ...


class TaskClass(GObject.Object):
    __gtype_name__ = 'TaskClass'

    created_on = GObject.Property(type=float)
    name = GObject.Property(type=str)
    _task_type: TaskTypeEnum
    _cancel_flag: threading.Event | None
    progress = GObject.Property(type=int)
    max_progress = GObject.Property(type=int)

    def __init__(self, created_on: float, name: str, task_type: TaskTypeEnum, cancel_flag: threading.Event | None,
                 max_progress: int):
        super().__init__()

        self.name = name
        self.created_on = created_on
        self.task_type = task_type
        self.cancel_flag = cancel_flag
        self.max_progress = max_progress
        self.progress = 0.0

    @GObject.Property(type=float)
    def fraction(self):
        if self.max_progress != 0:
            return min(self.progress/self.max_progress, 1.0)
        return 0.0

    @property
    def task_type(self):
        return self._task_type
    @property
    def cancel_flag(self):
        return self._cancel_flag
    @property
    def cancel_flag_set(self):
        if isinstance(self.cancel_flag, threading.Event):
            return self.cancel_flag.is_set()
        else:
            return False
    @task_type.setter
    def task_type(self, value: TaskTypeEnum):
        if isinstance(value, TaskTypeEnum):
            self._task_type = value
        else:
            raise ValueError
    @cancel_flag.setter
    def cancel_flag(self, value: threading.Event):
        if isinstance(value, threading.Event):
            self._cancel_flag = value
        elif isinstance(value, NoneType):
            self._cancel_flag = None
        else:
            raise ValueError


filename = os.path.join(tmp_path, 'rencher/gtk/ui/tasks_row.ui')
@Gtk.Template(filename=filename)
class TasksRow(Gtk.ListBoxRow):
    __gtype_name__ = 'TasksRow'
    task: TaskClass

    label: Gtk.Label = Gtk.Template.Child()
    progress_bar: Gtk.ProgressBar = Gtk.Template.Child()
    button: Gtk.Button = Gtk.Template.Child()
    details: Gtk.Label = Gtk.Template.Child()

    def __init__(self, task: TaskClass, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.update(task)

    def update(self, task: TaskClass) -> None:
        self.task = task

        if task.fraction < 1.0 and not task.cancel_flag_set:
            if task.task_type == TaskTypeEnum.IMPORT:
                self.button.set_icon_name('stop-large-symbolic')
                self.label.set_label(f'Importing "{task.name}"')
            elif task.task_type == TaskTypeEnum.DELETE:
                self.button.set_sensitive(False)
                self.button.set_icon_name('cross-large-symbolic')
                self.label.set_label(f'Deleting "{task.name}"')
        else:
            if task.task_type == TaskTypeEnum.IMPORT:
                self.label.set_label(f'Imported "{task.name}"')
            elif task.task_type == TaskTypeEnum.DELETE:
                self.label.set_label(f'Deleted "{task.name}"')
                self.button.set_sensitive(True)
            self.button.set_icon_name('cross-large-symbolic')

        self.progress_bar.set_fraction(task.fraction)

        self.details.set_label(f'{task.progress}/{task.max_progress}')


filename = os.path.join(tmp_path, 'rencher/gtk/ui/tasks_popover.ui')
@Gtk.Template(filename=filename)
class TasksPopover(Gtk.Popover):
    __gtype_name__ = 'TasksPopover'
    __gsignals__ = {
        'task-added': (GObject.SignalFlags.RUN_FIRST, None, (float,)),
        'task-changed': (GObject.SignalFlags.RUN_FIRST, None, (float,)),
        'task-removed': (GObject.SignalFlags.RUN_FIRST, None, (float,)),
    }

    window: 'RencherWindow'
    tasks: dict[float, TaskClass] = {}
    rows: dict[float, TasksRow] = {}
    stack: Gtk.Stack = Gtk.Template.Child()
    scrolled_window: Gtk.ScrolledWindow = Gtk.Template.Child()
    empty_status_page: Adw.StatusPage = Gtk.Template.Child()
    list_box: Gtk.ListBox = Gtk.Template.Child()

    def __init__(self, window: 'RencherWindow', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.window = window

    def get_total_fraction(self) -> float:
        progress = 0
        max_progress = 0
        for _, task in self.tasks.items():
            if task.fraction == 1.0:
                continue
            progress += task.progress
            max_progress += task.max_progress

        if max_progress != 0:
            return progress / max_progress
        else:
            return 0.0

    def new_task(self, created_on: float, name: str, task_type: TaskTypeEnum,
                 cancel_flag: threading.Event | None, max_progress: int) -> None:
        task = TaskClass(created_on, name, task_type, cancel_flag, max_progress)
        self.tasks[created_on] = task

        self.stack.set_visible_child(self.scrolled_window)
        row = TasksRow(task)
        row.button.connect('clicked', self.cancel_task, created_on)
        self.rows[created_on] = row
        self.list_box.append(row)
        GLib.idle_add(self.window.update_pie_paintable)

    def update_task(self, key: float, progress: int) -> None:
        task = self.tasks[key]
        if task:
            self.tasks[key].progress = progress
            row = self.rows[key]
            if row:
                row.update(task)
        GLib.idle_add(self.window.update_pie_paintable)

    def cancel_task(self, _, key: float) -> None:
        task = self.tasks[key]
        if not task:
            return
        if task.fraction < 1.0 and not task.cancel_flag.is_set():
            task.cancel_flag.set()
            row = self.rows[key]
            if row:
                row.update(task)
        else:
            self.remove_task(None, key)

    def remove_task(self, _, key: float) -> None:
        task = self.tasks[key]
        if task:
            del self.tasks[key]
            self.list_box.remove(self.rows[key])
            del self.rows[key]
        if len(self.rows) == 0:
            self.stack.set_visible_child(self.empty_status_page)
        GLib.idle_add(self.window.update_pie_paintable)


class PiePaintable(GObject.Object, Gdk.Paintable):
    __gtype_name__ = 'PieProgressPaintable'
    progress = 0.0

    def __init__(self):
        super().__init__()

    def set_fraction(self, fraction):
        self.progress = max(0.0, min(1.0, fraction))
        self.invalidate_contents()

    def do_snapshot(self, snapshot: Gdk.Snapshot, width: float, height: float):
        bounds = Graphene.Rect().init(0, 0, width, height)
        cr: cairo.Context = snapshot.append_cairo(bounds)
        cr.set_operator(cairo.OPERATOR_CLEAR)
        cr.paint()
        cr.set_operator(cairo.OPERATOR_OVER)
        color = Gtk.Label().get_color()  # doesn't update to colorscheme changes anymore

        radius = min(width, height) / 2 - 2
        cx, cy = width / 2, height / 2
        stroke = min(width, height) / 10

        cr.set_source_rgba(color.red, color.green, color.blue, .25)
        cr.set_line_width(stroke)
        cr.set_line_cap(cairo.LINE_CAP_ROUND)
        cr.arc(cx, cy, radius, 0, 2 * pi)
        cr.stroke()

        cr.set_source_rgba(color.red, color.green, color.blue, color.alpha)
        cr.set_line_width(stroke)
        start_angle = -pi / 2
        end_angle = start_angle + 2 * pi * self.progress
        cr.arc(cx, cy, radius, start_angle, end_angle)
        cr.stroke()
