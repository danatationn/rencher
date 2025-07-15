import glob
import logging
import os.path
from configparser import NoOptionError
from itertools import chain

from gi.repository import Adw, GLib

from rencher.gtk import format_gdatetime
from rencher.gtk.codename_dialog import RencherCodename
from rencher.renpy import Game, Mod
from rencher.renpy.config import RencherConfig


def return_projects(self) -> list[Game]:
    config = RencherConfig()
    data_dir = config.get_data_dir()
    games_path = os.path.join(data_dir, 'games')
    mods_path = os.path.join(data_dir, 'mods')
    dialog = RencherCodename(self)

    projects: list[Game] = []
    for path in chain(
        glob.iglob(os.path.join(games_path, '*')),
        glob.iglob(os.path.join(mods_path, '*')),
    ):
        try:
            if os.path.dirname(path) == games_path:
                projects.append(Game(rpath=path))
            else:
                projects.append(Mod(rpath=path))
        except NoOptionError:
            dialog.change_game(path)
            dialog.choose(self)
        except FileNotFoundError as e:
            logging.debug(f'{path} -> {repr(e)}')
        except AttributeError:
            pass
        # except Exception as e:  # uncomment when testing
        #     logging.debug(f'RANDOM NEW ERROR: {e}. YEY !!!')

    return projects

def update_library_sidebar(self) -> None:
    projects = return_projects(self)

    added_projects = set(projects) - set(self.projects)
    removed_projects = set(self.projects) - set(projects)
    # assuming that all the projects are changed is simpler and IS NOT O(n^2) !!!!!!!!!
    # will there be false positives? yeah. i need to alter watchdog to hand out the changed projects
    changed_projects = set(projects) - added_projects

    log = ''
    for project in removed_projects:
        log += f'-{project.name} '
    for project in changed_projects:
        log += f'~{project.name} '
    for project in added_projects:
        log += f'+{project.name} '

    if log != '':
        logging.debug(log)

    buttons = {}
    for i, _ in enumerate(self.projects):
        button = self.library_list_box.get_row_at_index(i)
        buttons[i] = button

    for button in buttons.values():
        if (button is not None
                and button.game in removed_projects
                and button.get_parent() is self.library_list_box):
            self.library_list_box.remove(button)

    for project in added_projects:
        button = Adw.ButtonRow(title=project.name)  # type: ignore
        button.game = project
        self.library_list_box.append(button)
        continue

    if not projects:  # ps5 view
        self.library_view_stack.set_visible_child_name('empty')
        self.split_view.set_show_sidebar(False)
    else:
        if not self.library_list_box.get_selected_row():
            self.library_view_stack.set_visible_child_name('game-select')
        self.split_view.set_show_sidebar(True)

    self.projects = projects

def update_library_view(self, project: Game) -> None:
    self.selected_status_page.set_title(project.name)
    project.config.read()

    try:
        last_played = int(float(project.config['info']['last_played']))
        datetime = GLib.DateTime.new_from_unix_utc(last_played)
        formatted_last_played = format_gdatetime(datetime, 'neat')
        self.last_played_row.set_subtitle(formatted_last_played)
    except KeyError:
        self.last_played_row.set_subtitle('N/A')
    except ValueError:
        self.last_played_row.set_subtitle('Never')

    try:
        playtime = int(float(project.config['info']['playtime']))
        datetime = GLib.DateTime.new_from_unix_utc(playtime)
        formatted_playtime = format_gdatetime(datetime, 'runtime')

        self.playtime_row.set_subtitle(formatted_playtime)
    except KeyError:
        self.playtime_row.set_subtitle('N/A')
    except ValueError:
        self.playtime_row.set_subtitle('N/A')

    try:
        added_on = int(project.config['info']['added_on'])
        datetime = GLib.DateTime.new_from_unix_utc(added_on)
        formatted_datetime = format_gdatetime(datetime, 'neat')
        self.added_on_row.set_subtitle(formatted_datetime)
    except KeyError:
        self.added_on_row.set_subtitle('N/A')

    self.version_row.set_subtitle(project.version if project.version else 'N/A')
    self.rpath_row.set_subtitle(str(project.rpath))
    self.codename_row.set_subtitle(project.codename)
    