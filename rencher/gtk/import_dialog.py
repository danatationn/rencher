import glob
import logging
import os
import os.path
import shutil
import threading
import time
import zipfile
from pathlib import Path
from typing import TYPE_CHECKING

import rarfile
from gi.repository import Adw, Gio, GLib, Gtk

from rencher import ImportCancelError, ImportCorruptArchiveError, ImportInvalidError, tmp_path
from rencher.gtk.game_item import GameItem
from rencher.gtk.tasks import Task
from rencher.gtk.utils import windowficate_path
from rencher.renpy.config import RencherConfig
from rencher.renpy.game import Game
from rencher.renpy.paths import get_absolute_path, get_py_files, get_rpa_files, get_rpa_path, validate_game_files

if TYPE_CHECKING:
    from rencher.gtk.window import RencherWindow


filename = os.path.join(tmp_path, 'rencher/gtk/ui/import.ui')
@Gtk.Template(filename=filename)
class RencherImport(Adw.PreferencesDialog):
    __gtype_name__ = 'RencherImport'

    import_title: Adw.EntryRow = Gtk.Template.Child()
    import_location: Adw.EntryRow = Gtk.Template.Child()
    import_location_picker: Gtk.Button = Gtk.Template.Child()
    import_type: Adw.ComboRow = Gtk.Template.Child()
    import_game_combo: Adw.ComboRow = Gtk.Template.Child()
    import_button: Adw.ActionRow = Gtk.Template.Child()
    import_progress_bar: Gtk.ProgressBar = Gtk.Template.Child()
    import_mod_toggle: Adw.SwitchRow = Gtk.Template.Child()

    thread = threading.Thread()
    cancel_flag = threading.Event()
    selected_type: str = 'Archive (.zip, .rar)'
    archive_location: str = ''
    folder_location: str = ''

    def __init__(self, window: 'RencherWindow', *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.window = window
        list_store = Gio.ListStore.new(GameItem)

        for _, game_item in window.library.game_items.items():
            if not game_item.game.is_mod:
                list_store.append(game_item)

        self.import_game_combo.set_model(list_store)
        self.import_game_combo.set_expression(
            Gtk.PropertyExpression.new(GameItem, None, 'name'),
        )

        string_list = Gtk.StringList()
        string_list.append('Archive (.zip, .rar)')
        string_list.append('Folder')
        self.import_type.set_model(string_list)

        # GLib.timeout_add(250, self.check_process)

    @Gtk.Template.Callback()
    def on_type_changed(self, *_):
        selected_item = self.import_type.get_selected_item()
        assert isinstance(selected_item, Gtk.StringObject)
        self.selected_type = selected_item.get_string()
        if self.selected_type == 'Folder':
            self.import_location.set_title('Folder Location')
            self.import_location_picker.set_icon_name('folder-open-symbolic')
            self.import_location.set_text(self.folder_location)
        else:
            self.import_location.set_title('Archive Location')
            self.import_location_picker.set_icon_name('file-cabinet-symbolic')
            self.import_location.set_text(self.archive_location)

    @Gtk.Template.Callback()
    def on_location_changed(self, entry_row: Adw.EntryRow):
        location_text = entry_row.get_text()
        if self.selected_type == 'Folder':
            self.folder_location = location_text
        else:
            self.archive_location = location_text

        try:
            if Path(location_text).suffix == '.zip':
                zipfile.ZipFile(location_text, 'r')
            if Path(location_text).suffix == '.rar':
                rarfile.RarFile(location_text, 'r')
        except (rarfile.BadRarFile, rarfile.NotRarFile, zipfile.BadZipFile, FileNotFoundError):
            self.import_button.set_sensitive(False)
        else:
            self.import_button.set_sensitive(True)
            if not self.import_title.get_text():
                if Path(location_text).is_file():
                    name = Path(location_text).stem
                else:
                    name = Path(location_text).name
                self.import_title.set_text(name)

    @Gtk.Template.Callback()
    def on_picker_clicked(self, _) -> None:
        dialog = Gtk.FileDialog()
        if self.selected_type == 'Folder':
            dialog.select_folder(self.window, None, self.on_file_selected)
        else:
            dialog.open(self.window, None, self.on_file_selected)

    def on_file_selected(self, dialog: Gtk.FileDialog, result):
        try:
            if self.selected_type == 'Folder':
                file = dialog.select_folder_finish(result)
            else:
                file = dialog.open_finish(result)
            self.import_location.set_text(file.get_path())
        except GLib.GError:
            pass  # dialog was dismissed by user

    @Gtk.Template.Callback()
    def on_import_clicked(self, _) -> None:
        def import_thread():
            try:
                self.import_game()
            except ImportInvalidError:
                toast = Adw.Toast(title='The game supplied is invalid!', timeout=5)
                self.window.toast_overlay.add_toast(toast)
            except ImportCorruptArchiveError:
                toast = Adw.Toast(title='The archive supplied is corrupt!', timeout=5)
                self.window.toast_overlay.add_toast(toast)
            except TimeoutError:
                toast = Adw.Toast(title='Couldn\'t come up with a name', timeout=5)
                self.window.toast_overlay.add_toast(toast)
            except ImportCancelError:
                toast = Adw.Toast(title='Importing cancelled', timeout=5)
                self.window.toast_overlay.add_toast(toast)
            finally:
                GLib.idle_add(self.import_progress_bar.set_visible, False)

        # if not self.import_button.get_style_context().has_class('destructive-action'):
        self.close()
        self.thread = threading.Thread(target=import_thread)
        self.thread.start()
        # else:
        #     self.cancel_flag.set()
        #     self.thread.join()

    # def check_process(self):
    #     if self.thread.is_alive():
    #         self.import_button.get_style_context().add_class('destructive-action')
    #         self.import_button.set_title('Cancel')
    #     else:
    #         self.import_button.get_style_context().remove_class('destructive-action')
    #         self.import_button.set_title('Import')
    #     return True

    def import_game(self):
        name = self.import_title.get_text()
        location = self.import_location.get_text()
        location_stem = os.path.splitext(os.path.basename(location))[0]
        is_mod = self.import_mod_toggle.get_active()
        modded_game: GameItem = self.import_game_combo.get_selected_item()  # type: ignore
        archive: zipfile | rarfile = None  # type: ignore

        data_dir = RencherConfig().get_data_dir()
        game_dir = os.path.join(data_dir, 'games')
        self.import_progress_bar.set_visible(True)

        if not os.path.exists(location):
            return

        suffix = os.path.splitext(location)[1]
        if suffix in ['.zip', '.rar']:
            logging.debug(f'Archive detected ("{location})"')
            try:
                if suffix == '.zip':
                    archive = zipfile.ZipFile(location)
                else:
                    archive = rarfile.RarFile(location)
            except (rarfile.BadRarFile, rarfile.NotRarFile, zipfile.BadZipFile) as err:
                raise ImportCorruptArchiveError('The archive supplied is invalid!') from err
            else:
                files = archive.namelist()

        elif os.path.isdir(location):
            logging.debug(f'Folder detected ("{location}/")')
            files = glob.glob(f'{location}/**/*', recursive=True)
        else:
            return

        if not is_mod and not validate_game_files(files):
            raise ImportInvalidError()

        count = 2
        start = time.perf_counter()
        rpath = None
        config = RencherConfig()
        while rpath is None or not os.path.exists(rpath):
            if time.perf_counter() - start > 1:
                # this will never happen unless you're a freak
                raise TimeoutError()

            possible_paths = [
                os.path.join(game_dir, name),
                os.path.join(game_dir, location_stem),
                os.path.join(game_dir, f'{name} ({count})'),
                os.path.join(game_dir, f'{location_stem} ({count})'),
            ]
            for path in possible_paths:
                if config.get('settings', 'windowficate_filenames', fallback=None) == 'true':
                    new_path = windowficate_path(path)
                else:
                    new_path = path
                if not os.path.exists(new_path):
                    os.makedirs(new_path, exist_ok=True)
                    rpath = new_path
                    break

            count += 1

        if not self.cancel_flag.is_set():
            logging.info(f'Importing the game at "{rpath}/"')
        start = time.perf_counter()
        self.window.application.pause_monitor(rpath)
        task_date = time.time()

        if is_mod:
            game_files = glob.glob(f'{modded_game.rpath}/**', recursive=True)
            total_work = len(files) + len(game_files)
        else:
            total_work = len(files)

        self.window.tasks.new_task(task_date, rpath, Task.IMPORT, self.cancel_flag, total_work)

        for i, path in enumerate(files):
            if self.cancel_flag.is_set():
                break
            if archive:
                archive.extract(path, rpath)
            else:
                relative_path = os.path.relpath(path, location)
                target_path = os.path.join(rpath, relative_path)

                if os.path.isdir(path):
                    os.makedirs(target_path, exist_ok=True)
                else:
                    os.makedirs(os.path.dirname(target_path), exist_ok=True)
                    shutil.copy(path, target_path)

            GLib.idle_add(self.window.tasks.update_task, task_date, i + 1)
            
        if is_mod:
            rpa_path = get_rpa_path(rpath)
            if rpa_path == rpath:
                new_rpa_path = os.path.join(rpath, 'game')
                rpa_files = get_rpa_files(rpath)
                if not os.path.exists(new_rpa_path):
                    os.makedirs(new_rpa_path, exist_ok=True)
                for path in rpa_files:
                    if self.cancel_flag.is_set():
                        break
                    relative_path = os.path.relpath(path, rpa_path)
                    target_path = os.path.join(new_rpa_path, relative_path)
                    shutil.move(path, target_path)
    
                # get_absolute_path is based off of get_rpa_files so we need to clear the cache
                # otherwise it will dump the game files outside the folder
                get_rpa_files.cache_clear()
                    
            apath = get_absolute_path(rpath)
    
            for i, path in enumerate(glob.iglob(f'{modded_game.apath}/**', recursive=True)):
                if self.cancel_flag.is_set():
                    break
                
                relative_path = os.path.relpath(path, modded_game.apath)
                target_path = os.path.join(apath, relative_path)
                
                if os.path.exists(target_path):
                    continue
                if os.path.basename(target_path) == 'rencher.ini':
                    continue
                if os.path.basename(target_path) == 'persistent':
                    continue
                if os.path.splitext(target_path)[1] == '.save':
                    continue
                if os.path.isdir(path):
                    os.makedirs(target_path, exist_ok=True)
                else:
                    os.makedirs(os.path.dirname(target_path), exist_ok=True)
                    shutil.copy(path, target_path)
                    
                GLib.idle_add(self.window.tasks.update_task, task_date, i)
            
        if not self.cancel_flag.is_set():
            game = Game(rpath=rpath)
            game.config.set('info', 'nickname', name)
            game.config.set('info', 'added_on', str(time.time()))
            game_scripts = get_py_files(game.apath)
            if len(game_scripts) == 2 and is_mod:
                try:
                    # ugh
                    game_codenames = [os.path.splitext(os.path.basename(codename))[0] for codename in game_scripts]
                    game_codenames.remove(modded_game.codename)
                    game.config.set('info', 'codename', game_codenames[0])
                except ValueError:
                    logging.warn('Couldn\'t determine codename')
                    pass
            game.config.write()

            self.window.library.add_game(rpath)
            game_item = self.window.library.get_game(rpath)
            row = self.window.rows[game_item]
            self.window.library_list_box.select_row(row)

            logging.info(f'Importing done in {time.perf_counter() - start:.2f}s')
            if RencherConfig()['settings']['delete_on_import'] == 'true':
                try:
                    os.unlink(location)
                except PermissionError:
                    logging.error('Couldn\'t delete archive! File left untouched')
                except Exception as e:
                    logging.error(f'Couldn\'t delete archive! {e}')
                else:
                    logging.info(f'Archive "{location_stem}" deleted!')

            self.window.application.resume_monitor(rpath)
        else:
            GLib.idle_add(self.import_progress_bar.set_fraction, 1)
            shutil.rmtree(rpath)
            logging.info(f'Importing cancelled. Total thread runtime: {time.perf_counter() - start:.2f}s')
            self.window.application.resume_monitor(rpath)
            # raise ImportCancelError()
