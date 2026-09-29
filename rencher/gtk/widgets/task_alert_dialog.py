from gettext import gettext as _

from gi.repository import Adw, Gtk

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
            text: str = '\n\n'.join(f'• {w}' for w in self.task.warnings)
            label = Gtk.Label(
                label=text,
                wrap=True,
            )
            scrolled = Gtk.ScrolledWindow(
                propagate_natural_height=True,
                propagate_natural_width=True,
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
            self.set_default_response('cancel')
            # self.add_response('retry', _('Retry'))
            # self.set_default_response('retry')
            # self.set_response_appearance('retry', Adw.ResponseAppearance.SUGGESTED)
        else:  # warnings
            self.set_heading(_('Task Completed with Warnings'))
            self.add_response('ok', _('OK'))
            self.set_default_response('ok')
            self.set_close_response('ok')

        self.connect('response', self._on_response)

    def _on_response(self, _dialog: 'TaskAlertDialog', _id: str) -> None:
        ...
