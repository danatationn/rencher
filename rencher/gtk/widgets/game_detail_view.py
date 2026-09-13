import subprocess
import threading
from gettext import gettext as _
from typing import IO

from gi.repository import Adw, GLib, GObject, Gtk

from rencher.gtk.game_entry import GameEntry
from rencher.gtk.library import Library
from rencher.gtk.rpc import Rpc
from rencher.gtk.utils import gtk_template_callback, gtk_template_child, open_file_manager
from rencher.gtk.widgets.options_dialog import OptionsDialog


@Gtk.Template.from_resource('/com/github/danatationn/rencher/ui/game_detail_view.ui')
class GameDetailView(Gtk.Box):
    __gtype_name__: str = 'GameDetailView'

    title_status_page: Adw.StatusPage = gtk_template_child()
    last_played_row: Adw.ActionRow = gtk_template_child()
    playtime_row: Adw.ActionRow = gtk_template_child()
    added_on_row: Adw.ActionRow = gtk_template_child()
    rpath_row: Adw.ActionRow = gtk_template_child()
    version_row: Adw.ActionRow = gtk_template_child()
    codename_row: Adw.ActionRow = gtk_template_child()
    log_row: Adw.ExpanderRow = gtk_template_child()
    log_text_view: Gtk.TextView = gtk_template_child()

    entry: GameEntry
    rpc: Rpc
    row: Adw.ActionRow | Gtk.ListBoxRow
    log_buf: Gtk.TextBuffer

    play_button: Gtk.Button = gtk_template_child()
    error_dialog: Adw.AlertDialog | None
    options_dialog: OptionsDialog
    options_button: Gtk.Button = gtk_template_child()

    def __init__(self, entry: GameEntry, rpc: Rpc, row: Adw.ActionRow | Gtk.ListBoxRow, library: Library, **kwargs):
        super().__init__(**kwargs)
        self.entry = entry
        self.rpc = rpc
        self.row = row
        self.log_buf = self.log_text_view.get_buffer()

        self.error_dialog = None
        self.options_dialog = OptionsDialog(entry)

        # to change the labels when the view is created, we need GObject.BindingFlags.SYNC_CREATE
        # or else it only updates when something changes
        self.entry.bind_property('name', self.title_status_page, 'title', GObject.BindingFlags.SYNC_CREATE)
        self.entry.bind_property('last_played', self.last_played_row, 'subtitle', GObject.BindingFlags.SYNC_CREATE)
        self.entry.bind_property('playtime', self.playtime_row, 'subtitle', GObject.BindingFlags.SYNC_CREATE)
        self.entry.bind_property('added_on', self.added_on_row, 'subtitle', GObject.BindingFlags.SYNC_CREATE)
        self.entry.bind_property('version', self.version_row, 'subtitle', GObject.BindingFlags.SYNC_CREATE)
        self.entry.bind_property('rpath', self.rpath_row, 'subtitle', GObject.BindingFlags.SYNC_CREATE)
        self.entry.bind_property('codename', self.codename_row, 'subtitle', GObject.BindingFlags.SYNC_CREATE)

        library.connect('game-launched', self._game_launched)
        library.connect('game-closed', self._game_closed)

        self.log_buf = self.log_text_view.get_buffer()
        self.log_buf.create_tag('stderr', foreground='orange')
        self.log_buf.connect('changed', lambda b: self.log_row.set_sensitive(b.get_char_count() > 0))

    @gtk_template_callback
    def on_play_clicked(self, _play_button: Gtk.Button) -> None:
        if self.entry.process and self.entry.process.poll() is None:
            self.play_button.set_label(_('Stopping'))
            self.activate_action('library.stop-game', GLib.Variant('s', self.entry.rpath))
        else:
            self.activate_action('library.run-game', GLib.Variant('s', self.entry.rpath))

    def _game_launched(self, _library: Library, entry: GameEntry, process: subprocess.Popen[bytes]) -> None:
        if self.entry != entry:
            return
        self.play_button.set_label(_('Stop'))
        self.play_button.get_style_context().add_class('destructive-action')
        self.play_button.get_style_context().remove_class('suggested-action')

        self.options_dialog.delete_game_button.set_sensitive(False)

        self.log_row.set_expanded(False)
        self.log_buf.set_text('')
        threading.Thread(target=self._read_stream, args=(process.stdout, False), daemon=True).start()
        threading.Thread(target=self._read_stream, args=(process.stderr, True), daemon=True).start()

    def _game_closed(
        self, _library: Library, entry: GameEntry, process: subprocess.Popen[bytes] | None, err: Exception | None,
    ) -> None:
        if self.entry != entry:
            return
        self.play_button.set_label(_('Play'))
        self.play_button.get_style_context().add_class('suggested-action')
        self.play_button.get_style_context().remove_class('destructive-action')

        self.options_dialog.delete_game_button.set_sensitive(True)
        self.entry.refresh()

        if isinstance(err, PermissionError):
            alert = Adw.AlertDialog(heading=_('Error'), body=_('This game\'s executable is not executable!'))
            alert.add_response('ok', _('OK'))
            alert.choose(self)

        if process and process.returncode != 0 and self.log_row.is_sensitive():
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

    def _read_stream(self, stream: IO[bytes], is_stderr: bool) -> None:
        for line in stream:
            GLib.idle_add(self._on_log_line, line.decode(errors='replace'), is_stderr)

    def _on_log_line(self, line: str, is_stderr: bool) -> None:
        if is_stderr:
            self.log_buf.insert_with_tags_by_name(self.log_buf.get_end_iter(), line, 'stderr')
        else:
            self.log_buf.insert(self.log_buf.get_end_iter(), line)
        self.log_text_view.scroll_to_iter(self.log_buf.get_end_iter(), 0, False, 0, 0)

    def _on_error_dialog_response(self, _dialog: Adw.AlertDialog, id: str) -> None:
        if id == 'show':
            GLib.idle_add(self.log_row.set_expanded, True)
            GLib.idle_add(self.log_text_view.grab_focus)

    # TODO scroll to the *bottom* of the log view . not the top
    def _scroll_to_log(self) -> None:
        scrolled_window = self.log_text_view.get_parent()
        if isinstance(scrolled_window, Gtk.ScrolledWindow):
            adj = scrolled_window.get_vadjustment()
            adj.set_value(adj.get_upper() - adj.get_page_size())

    @gtk_template_callback
    def on_dir_clicked(self, _widget: Gtk.Button) -> None:
        open_file_manager(self.entry.apath)

    @gtk_template_callback
    def on_options_clicked(self, _widget: Gtk.Button):
        self.options_dialog.change_game(self.entry)
        self.options_dialog.present(self)
