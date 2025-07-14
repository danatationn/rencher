import logging
import secrets
import shutil
import zipfile
from pathlib import Path

import rarfile
from gi.repository import Adw, GLib

from rencher.gtk import windowficate_file
from rencher.renpy import Game
from rencher.renpy.config import RencherConfig
from rencher.renpy.paths import get_absolute_path, get_rpa_path

config = RencherConfig()
data_dir = RencherConfig().get_data_dir()

def get_dir_name(self, location: Path, is_mod: bool = False) -> Path:
    library_dir = data_dir / ('mods' if is_mod else 'games')
    while True:
        dir_name = None
        try:
            dir_name = windowficate_file(self.import_title.get_text())
        except ValueError:
            pass
        try:
            location_path = Path(self.import_location.get_text())
            dir_name = windowficate_file(location_path)
            if location_path.is_file():
                dir_name = dir_name.stem
            else:
                dir_name = dir_name.name
        except ValueError:
            pass
        if not dir_name or Path(library_dir / dir_name).is_dir():
            # if they both fail you just get a simple random string like 'vRDQzw'
            # we also do not want to paste the game over another game
            dir_name = secrets.token_urlsafe(4)

        rpath = library_dir / dir_name
        if not rpath.is_dir():
            rpath.mkdir(exist_ok=True, parents=True)
            return rpath

def import_game(self):
    game_name = self.import_title.get_text()
    location = Path(self.import_location.get_text())
    is_mod = self.import_game_combo.get_sensitive()
    target_game = self.import_game_combo.get_selected_item()

    rpath = get_dir_name(self, location, is_mod)

    if location.is_file():
        if location.suffix == '.zip':
            archive = zipfile.ZipFile(location, 'r')
        elif location.suffix == '.rar':
            archive = rarfile.RarFile(location, 'r')
        else:
            toast = Adw.Toast(
                title='Only zip and rar files are supported at the moment',
                timeout=5,
            )
            self.window.toast_overlay.add_toast(toast)
            return

        self.import_progress_bar.set_visible(True)
        total_mod_work = len(archive.namelist())
        total_game_work = sum(1 for file in target_game.game.rpath.rglob('*') if file.is_file()) if is_mod else 0
        total_work = total_mod_work + total_game_work

        for i, file in enumerate(archive.namelist(), 1):
            if not self.cancel_flag.is_set():
                archive.extract(file, rpath)
                GLib.idle_add(self.import_progress_bar.set_fraction, i / total_work)

        archive.close()

    elif location.is_dir():
        self.import_progress_bar.set_visible(True)
        total_mod_work = sum(1 for file in location.rglob('*') if file.is_file())
        total_game_work = sum(1 for file in target_game.game.rpath.rglob('*') if file.is_file()) if is_mod else 0
        total_work = total_mod_work + total_game_work

        for i, file in enumerate(location.rglob('*'), 1):
            relative_path = file.relative_to(location)
            target_path = rpath / relative_path
            if file.is_dir():
                target_path.mkdir(exist_ok=True)
            elif config['settings']['delete_on_import'] == 'true':
                file.replace(target_path)
            else:
                shutil.copy(file, target_path)
            GLib.idle_add(self.import_progress_bar.set_fraction, i / total_work)
            logging.debug(i/total_work)

    if is_mod and not self.cancel_flag.is_set():
        game = target_game.game

        # some ren'py 6 mods only supply rpa files
        # make sure the game/ folder exists
        rpa_dir = get_rpa_path(rpath)
        if rpa_dir.name != 'game':
            logging.debug(rpa_dir)
            new_rpa_dir = rpath / 'game'
            new_rpa_dir.mkdir(exist_ok=True, parents=True)
            for file in rpa_dir.glob('*'):
                relative_path = file.relative_to(rpa_dir)
                new_rpa_path = new_rpa_dir / relative_path
                file.replace(new_rpa_path)

        # we already did find_absolute_path, and it's possible that the directory has now changed completely
        # we need to clear the cache in order for it to not return the same thing
        get_rpa_path.cache_clear()
        apath = get_absolute_path(rpath)
        if apath is None:
            # mod is broken
            toast = Adw.Toast(
                title='The game is corrupt',  # ???
                timeout=5,
            )
            self.window.toast_overlay.add_toast(toast)
            shutil.rmtree(rpath)
            return

        for i, file in enumerate(game.apath.rglob('*'), 1):
            if not self.cancel_flag.is_set():
                relative_path = file.relative_to(game.apath)
                target_path = apath / relative_path

                if target_path.exists():
                    continue
                if target_path.name == 'rencher.ini':
                    continue

                target_path.parent.mkdir(exist_ok=True, parents=True)

                if file.is_dir():
                    target_path.mkdir(exist_ok=True, parents=True)
                else:
                    shutil.copy(file, target_path)

                GLib.idle_add(self.import_progress_bar.set_fraction, (total_mod_work + i) / total_work)

    if not self.cancel_flag.is_set():
        get_rpa_path.cache_clear()
        apath = get_absolute_path(rpath)
        if apath is None:
            toast = Adw.Toast(
                title='The mod is corrupt',  # ???
                timeout=5,
            )
            self.window.toast_overlay.add_toast(toast)
            shutil.rmtree(rpath)
            return

        py_names = [py_path.stem for py_path in sorted(apath.glob('*.py'))]
        # if not is_mod and len(py_names) > 1:
        # 	mod_rpath = get_dir_name(self, location, True)
        # 	rpath.replace(mod_rpath)
        # DOING THIS LATER

        game = Game(apath=apath)
        game.config['info']['nickname'] = game_name

        if is_mod:
            game_codename = target_game.game.codename

            if len(py_names) == 2:
                py_names.remove(game_codename)
                game.config['info']['codename'] = py_names[0]

        game.config.write()

        toast = Adw.Toast(
            title=f'{game.name} has been imported',
            timeout=5,
        )
        self.window.toast_overlay.add_toast(toast)

        if config['settings']['delete_on_import'] == 'true':
            location_path = Path(location)
            try:
                if location_path.is_file():
                    location_path.unlink(missing_ok=True)
                elif location_path.is_dir():
                    shutil.rmtree(location_path)
            except PermissionError:
                pass
    else:
        shutil.rmtree(rpath, ignore_errors=True)

        toast = Adw.Toast(
            title='Import has been cancelled',
            timeout=5,
        )
        self.window.toast_overlay.add_toast(toast)
		