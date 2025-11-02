import os
import threading
from enum import Enum
from math import pi
from typing import TYPE_CHECKING

import cairo
from gi.repository import Adw, Gdk, GLib, GObject, Graphene, Gtk

from rencher import tmp_path

if TYPE_CHECKING:
    from rencher.gtk.window import RencherWindow


class Task(Enum):
    IMPORT = 0
    DELETE = 1
    ...


filename = os.path.join(tmp_path, 'rencher/gtk/ui/tasks_popover.ui')
@Gtk.Template(filename=filename)
class RencherTasksPopover(Gtk.Popover):
    __gtype_name__ = 'RencherTasksPopover'

    tasks: dict[float, dict] = {}
    __gsignals__ = {
        'task-added': (GObject.SignalFlags.RUN_FIRST, None, (float,)),
        'task-changed': (GObject.SignalFlags.RUN_FIRST, None, (float,)),
        'task-removed': (GObject.SignalFlags.RUN_FIRST, None, (float,)),
    }

    window: 'RencherWindow'
    rows: dict[float, 'RencherTasksRow'] = {}
    stack: Gtk.Stack = Gtk.Template.Child()
    scrolled_window: Gtk.ScrolledWindow = Gtk.Template.Child()
    empty_status_page: Adw.StatusPage = Gtk.Template.Child()
    list_box: Gtk.ListBox = Gtk.Template.Child()

    def __init__(self, window: 'RencherWindow', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.window = window

    def get_task(self, created_on: float) -> dict | None:
        if created_on in self.tasks:
            return self.tasks[created_on]
        else:
            return None

    def get_active_tasks(self) -> int:
        return len(self.tasks)

    def new_task(self, created_on: float, name: str, task_type: 'Task',
                 cancel_flag: threading.Event | None, max_progress: int) -> None:
        task = {
            'name': name,
            'type': task_type,
            'cancel_flag': cancel_flag,
            'progress': 0,
            'max_progress': max_progress,
        }
        self.tasks[created_on] = task
        self.stack.set_visible_child(self.scrolled_window)
        row = RencherTasksRow(task)
        row.button.connect('clicked', self.remove_task, created_on)
        self.rows[created_on] = row
        self.list_box.append(row)
        GLib.idle_add(self.window.update_pie_paintable)
        # self.emit('task-added', created_on)

    def update_task(self, created_on: float, progress: int) -> None:
        task = self.get_task(created_on)
        if task:
            self.tasks[created_on]['progress'] = progress
            row = self.rows[created_on]
            row.update(task)
        GLib.idle_add(self.window.update_pie_paintable)
        # self.emit('task-changed', created_on)

    def remove_task(self, _, created_on: float) -> None:
        task = self.get_task(created_on)
        if task:
            del self.tasks[created_on]
            flag = task['cancel_flag']
            if isinstance(flag, threading.Event):
                flag.set()
            self.list_box.remove(self.rows[created_on])
            del self.rows[created_on]
        if len(self.rows) == 0:
            self.stack.set_visible_child(self.empty_status_page)
        GLib.idle_add(self.window.update_pie_paintable)
        # self.emit('task-removed', created_on)


filename = os.path.join(tmp_path, 'rencher/gtk/ui/tasks_row.ui')
@Gtk.Template(filename=filename)
class RencherTasksRow(Gtk.ListBoxRow):
    __gtype_name__ = 'RencherTasksRow'

    label: Gtk.Label = Gtk.Template.Child()
    progress_bar: Gtk.ProgressBar = Gtk.Template.Child()
    button: Gtk.Button = Gtk.Template.Child()
    details: Gtk.Label = Gtk.Template.Child()

    def __init__(self, task: dict, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.update(task)

    def update(self, task: dict) -> None:
        if task['type'] == Task.IMPORT:
            self.label.set_label(f'Importing {task['name']}')
        if task['type'] == Task.DELETE:
            self.label.set_label(f'Deleting {task['name']}')
            self.button.set_visible(False)
        if task['max_progress'] != 0:
            fraction = task['progress'] / task['max_progress']
        else:
            fraction = task['progress']

        self.progress_bar.set_fraction(fraction)
        self.details.set_label(f'{task['progress']}/{task['max_progress']}')


class PiePaintable(GObject.Object, Gdk.Paintable):
    __gtype_name__ = 'PieProgressPaintable'
    progress: float

    def __init__(self):
        super().__init__()
        self.progress = 0.0

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
