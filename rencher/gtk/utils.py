import logging
import typing
from pathlib import Path

import gi

gi.require_version('Gtk', '4.0')
from gi.repository import Gio, GLib, Gtk  # noqa: E402


def gtk_template_callback[F: typing.Callable[..., typing.Any]](func: F) -> F:
    return typing.cast(F, Gtk.Template.Callback()(func))

def gtk_template_child[T](name: str | None = None) -> T:  # pyright: ignore[reportInvalidTypeVarUse]
    return typing.cast(T, Gtk.Template.Child(name=name))

def open_file_manager(path: str):
    def _on_launched(launcher: Gtk.FileLauncher, result: Gio.AsyncResult) -> None:
        try:
            launcher.launch_finish(result)
        except GLib.Error as e:
            logging.error(f'Couldn\'t open {path}. ({e})')

    Gtk.FileLauncher.new(Gio.File.new_for_path(path)).launch(None, None, _on_launched)

def sanitize_path(path: Path) -> Path:
    # TODO make this universal
    """
    returns a file that abides by the Windows file naming conventions

    Args:
        path (str): is used
    Returns:
        str: the new path
    """
    forbidden_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
    forbidden_names = ['CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8',
                       'COM9', 'COM¹', 'COM²', 'COM³', 'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8',
                       'LPT9', 'LPT¹', 'LPT²', 'LPT³']

    new_name: str = ''
    for char in path.name:
        if char in forbidden_chars:
            new_name += '_'
        else:
            new_name += char
    if new_name in forbidden_names:
        new_name = 'game'

    return path.parent / new_name
