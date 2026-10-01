from gettext import gettext as _
import logging

from gi.repository import Adw, GLib, Gtk

from rencher.gtk.tasks import RencherTask, TaskError


class TaskAlertDialog(Adw.AlertDialog):
    task: RencherTask

    def __init__(self, task: RencherTask):
        super().__init__()
        self.task = task
        if self.task.error:
            assert(isinstance(self.task.error, TaskError))

        # can hold the warning label and the warning list
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)

        if self.task.error and self.task.warnings:
            warn_label = Gtk.Label(label=_('Warnings'), halign=Gtk.Align.START)
            warn_label.add_css_class('heading')
            content.append(warn_label)

        if self.task.warnings:
            # u00a0 is a non-breaking space.
            # if it weren't here the bullet point and the warning on diff lines
            text: str = '\n\n'.join(f'•\u00a0{w}' for w in self.task.warnings)
            label = Gtk.Label(
                label=text, wrap=True, halign=Gtk.Align.START,
                margin_start=12, margin_bottom=12, margin_end=12, margin_top=12,
            )
            scrolled = Gtk.ScrolledWindow(
                propagate_natural_height=True,
                # propagate_natural_width=True,
                hexpand=True,
                halign=Gtk.Align.FILL,
            )
            scrolled.add_css_class('card')
            scrolled.set_child(label)
            content.append(scrolled)
            self.set_extra_child(content)

        if self.task.error:
            self.set_heading(_('Task Failed'))
            self.set_body(self.task.error.message)
            self.add_response('cancel', _('Cancel'))
            self.set_close_response('cancel')
            self.add_response('retry', _('Retry'))
            self.set_default_response('retry')
            self.set_response_appearance('retry', Adw.ResponseAppearance.SUGGESTED)
        else:  # warnings
            self.set_heading(_('Task Completed with Warnings'))
            self.add_response('ok', _('OK'))
            self.set_default_response('ok')
            self.set_close_response('ok')

        self.connect('response', self._on_response)

    def _on_response(self, _dialog: 'TaskAlertDialog', id: str) -> None:
        if id == 'retry':
            self.activate_action('library.retry-task', GLib.Variant('s', str(self.task.uuid)))
        elif id == 'cancel':
            self.activate_action('library.cancel-task', GLib.Variant('s', str(self.task.uuid)))
