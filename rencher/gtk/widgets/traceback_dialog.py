import traceback
from collections.abc import Callable
from gettext import gettext as _

from gi.repository import Adw, Gtk

from rencher.gtk.tasks import RencherTask


class TaskTracebackDialog(Adw.Dialog):
    """
    dialog for displaying game task errors .

    looks different depending on what errors are different:
        * traceback - formatted exception traceback
        * error - for expected errors
        * warnings - any non-critical warnings
    """

    task: RencherTask
    button_box: Gtk.Box
    toolbar_view: Adw.ToolbarView

    def __init__(self, task: RencherTask) -> None:
        super().__init__(title=_('"{}" has failed').format(task.label))
        self.task = task

        self.set_content_width(720)
        self.set_content_height(540)
        self.set_follows_content_size(False)

        self.toolbar_view = Adw.ToolbarView()
        self.set_child(self.toolbar_view)

        header = Adw.HeaderBar()
        self.toolbar_view.add_top_bar(header)

        self.button_box = Gtk.Box(
            spacing=6,
            margin_top=6,
            margin_bottom=12,
            margin_end=12,
            margin_start=12,
        )
        self.toolbar_view.add_bottom_bar(self.button_box)

        scrolled = Gtk.ScrolledWindow(
            margin_bottom=12,
            margin_start=12,
            margin_end=12,
            margin_top=12,
        )
        scrolled.add_css_class('card')
        self.toolbar_view.set_content(scrolled)

        text_view = Gtk.TextView(
            editable=False,
            cursor_visible=False,
            wrap_mode=Gtk.WrapMode.WORD_CHAR,
        )
        text_view.add_css_class('monospace')
        text_view.get_buffer().set_text(''.join(traceback.format_exception(self.task.error)))
        scrolled.set_child(text_view)

        self._add_button(_('Cancel'), self._on_cancel)
        # self._add_button(_('Retry'), self._on_cancel, 'suggested-action')

    def _add_button(self, label: str, callback: Callable[[Gtk.Button], None], style: str | None = None) -> None:
        button = Gtk.Button(label=label, hexpand=True)
        if style:
            button.add_css_class(style)
        button.connect('clicked', callback)
        self.button_box.append(button)

    ### callbacks

    def _on_cancel(self, _button: Gtk.Button) -> None:
        self.close()

    def _on_retry(self, _button: Gtk.Button) -> None:
        self.close()
