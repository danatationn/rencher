import subprocess
from gettext import gettext as _
from typing import override

from gi.repository import Adw, GLib, GObject, Gtk

from rencher.gtk.game_item import GameItem
from rencher.gtk.library import Library
from rencher.gtk.utils import gtk_template_callback, gtk_template_child, open_file_manager
from rencher.gtk.widgets.options_dialog import OptionsDialog
from rencher.renpy.game import GameNoExecutableError


@Gtk.Template.from_resource('/com/github/danatationn/rencher/ui/game_page.ui')
class GamePage(Gtk.Box):
    __gtype_name__: str = 'GamePage'

    title_status_page: Adw.StatusPage = gtk_template_child()
    last_played_row: Adw.ActionRow = gtk_template_child()
    playtime_row: Adw.ActionRow = gtk_template_child()
    added_on_row: Adw.ActionRow = gtk_template_child()
    rpath_row: Adw.ActionRow = gtk_template_child()
    version_row: Adw.ActionRow = gtk_template_child()
    codename_row: Adw.ActionRow = gtk_template_child()
    log_row: Adw.ExpanderRow = gtk_template_child()
    log_text_view: Gtk.TextView = gtk_template_child()

    game_item: GameItem
    row: Adw.ActionRow | Gtk.ListBoxRow
    log_buf: Gtk.TextBuffer
    log_end_mark: Gtk.TextMark
    _handler_ids: list[int]
    library: Library

    play_button: Gtk.Button = gtk_template_child()
    error_dialog: Adw.AlertDialog | None
    options_dialog: OptionsDialog
    options_button: Gtk.Button = gtk_template_child()

    def __init__(self, game_item: GameItem, row: Adw.ActionRow | Gtk.ListBoxRow, library: Library):
        super().__init__()
        self.game_item = game_item
        self.row = row
        self.log_buf = self.log_text_view.get_buffer()
        self.library = library
        self.error_dialog = None
        self.options_dialog = OptionsDialog(game_item)

        # to change the labels when the view is created, we need GObject.BindingFlags.SYNC_CREATE
        # or else it only updates when something changes
        self.game_item.bind_property('name', self.title_status_page, 'title', GObject.BindingFlags.SYNC_CREATE)
        self.game_item.bind_property('last_played', self.last_played_row, 'subtitle', GObject.BindingFlags.SYNC_CREATE)
        self.game_item.bind_property('playtime', self.playtime_row, 'subtitle', GObject.BindingFlags.SYNC_CREATE)
        self.game_item.bind_property('added_on', self.added_on_row, 'subtitle', GObject.BindingFlags.SYNC_CREATE)
        self.game_item.bind_property('version', self.version_row, 'subtitle', GObject.BindingFlags.SYNC_CREATE)
        self.game_item.bind_property('top_dir', self.rpath_row, 'subtitle', GObject.BindingFlags.SYNC_CREATE)
        self.game_item.bind_property('codename', self.codename_row, 'subtitle', GObject.BindingFlags.SYNC_CREATE)

        self._handler_ids = [
            self.library.connect('game-launched', self._game_launched),
            self.library.connect('game-closed', self._game_closed),
            self.library.connect('game-log', self._on_log_line),
        ]

        if self.library.is_game_running(self.game_item.top_dir):
            self._set_running_ui(True)

        self.log_buf = self.log_text_view.get_buffer()
        self.log_buf.create_tag('stderr', foreground='orange')
        self.log_end_mark = self.log_buf.create_mark(None, self.log_buf.get_end_iter(), False)
        self.log_buf.connect('changed', lambda b: self.log_row.set_sensitive(b.get_char_count() > 0))

    @gtk_template_callback
    def on_play_clicked(self, _play_button: Gtk.Button) -> None:
        if self.library.is_game_running(self.game_item.top_dir):
            self.play_button.set_label(_('Stopping'))
            self.activate_action('library.stop-game', GLib.Variant('s', self.game_item.top_dir))
        else:
            self.activate_action('library.run-game', GLib.Variant('s', self.game_item.top_dir))

    def _game_launched(self, _library: Library, game_item: GameItem, _process: subprocess.Popen[bytes]) -> None:
        if self.game_item != game_item:
            return
        if game_item.config.effective().discord_rpc:
            self.activate_action('rpc.update', GLib.Variant('a(ss)', [('state', game_item.name)]))
        self._set_running_ui(True)
        self.log_row.set_expanded(False)
        self.log_buf.set_text('')

    def _game_closed(
        self, _library: Library, game_item: GameItem, failed: bool, err: Exception | None,
    ) -> None:
        if self.game_item != game_item:
            return
        self.activate_action('rpc.clear')
        self._set_running_ui(False)
        self.game_item.refresh()

        if err:
            alert = Adw.AlertDialog(heading=_('Error'))
            alert.add_response('ok', _('OK'))
            if isinstance(err, PermissionError):
                alert.set_body(_('This game\'s executable is not executable!'))
            elif isinstance(err, GameNoExecutableError):
                alert.set_body(_('Couldn\'t find the game executable!'))
            else:
                alert.set_body(_('Something went wrong launching the game! ({}{})')
                    .format(err.__class__.__name__, f': {err}' if str(err) else ''))
            alert.choose(self)

        if failed and self.log_row.is_sensitive():
            self.error_dialog = Adw.AlertDialog(
                heading=_('Something went wrong!'),
                body=_('A game has errors. Check the logs for more details.'),
                default_response='show',
                close_response='cancel',
            )
            self.error_dialog.add_response('show', _('Show Logs'))
            self.error_dialog.add_response('cancel', _('Cancel'))
            self.error_dialog.connect('response', self._on_error_dialog_response)
            GLib.idle_add(self.error_dialog.present, self)

    def _set_running_ui(self, is_running: bool) -> None:
        if is_running:
            self.play_button.set_label(_('Stop'))
            self.play_button.get_style_context().add_class('destructive-action')
            self.play_button.get_style_context().remove_class('suggested-action')
        else:
            self.play_button.set_label(_('Play'))
            self.play_button.get_style_context().add_class('suggested-action')
            self.play_button.get_style_context().remove_class('destructive-action')
        self.options_dialog.delete_game_button.set_sensitive(not is_running)


    def _on_log_line(self, _library: Library, game_item: GameItem, line: str, is_stderr: bool) -> None:
        if self.game_item != game_item:
            return

        # removes empty line at the beginning
        line = line.rstrip('\r\n')
        if self.log_buf.get_char_count() == 0:
            if not line:
                return
        else:
            line = '\n' + line

        if is_stderr:
            self.log_buf.insert_with_tags_by_name(self.log_buf.get_end_iter(), line, 'stderr')
        else:
            self.log_buf.insert(self.log_buf.get_end_iter(), line)
        self.log_text_view.scroll_to_mark(self.log_end_mark, 0, False, 0, 0)

    def _on_error_dialog_response(self, _dialog: Adw.AlertDialog, id: str) -> None:
        if id == 'show':
            GLib.idle_add(self.log_row.set_expanded, True)
            # grab_focus returns true, making this repeat forever. forcefully return False (SOURCE_REMOVE)
            GLib.idle_add(lambda: self.log_text_view.grab_focus and GLib.SOURCE_REMOVE)
            GLib.idle_add(self._scroll_to_log)

    def _scroll_to_log(self) -> None:
        self.log_buf.place_cursor(self.log_buf.get_start_iter())
        self.log_text_view.scroll_to_iter(self.log_buf.get_start_iter(), 0, False, 0, 0)

        revealer = self.log_text_view.get_ancestor(Gtk.Revealer)
        if revealer and not revealer.get_child_revealed():
            # wait for the expand animation, otherwise the page isn't tall enough to scroll yet
            def _on_revealed(revealer: Gtk.Revealer, _pspec: GObject.ParamSpec) -> None:
                if revealer.get_child_revealed():
                    revealer.disconnect(handler_id)
                    self._scroll_to_log()
            handler_id = revealer.connect('notify::child-revealed', _on_revealed)
            return

        page_scroll = self.log_row.get_ancestor(Gtk.ScrolledWindow)
        if not page_scroll:
            return
        ok, bounds = self.log_row.compute_bounds(page_scroll)
        if not ok:
            return

        adj = page_scroll.get_vadjustment()
        row_y = adj.get_value() + bounds.get_y()  # bounds are relative to the visible area
        row_h, page_h = bounds.get_height(), adj.get_page_size()
        if row_h >= page_h:
            adj.set_value(row_y)  # taller than the screen: put the row at the top
        else:
            adj.set_value(row_y - (page_h - row_h) / 2)  # otherwise center it

    @gtk_template_callback
    def on_dir_clicked(self, _widget: Gtk.Button) -> None:
        open_file_manager(self.game_item.base_dir)

    @gtk_template_callback
    def on_options_clicked(self, _widget: Gtk.Button):
        self.options_dialog.change_game(self.game_item)
        self.options_dialog.present(self)

    @override
    def do_unroot(self) -> None:
        for id in self._handler_ids:
            self.library.disconnect(id)
        self._handler_ids.clear()
        Gtk.Box.do_unroot(self)
