import glob
import logging
import os.path

from gi.repository import Adw

from rencher import GameInvalidError
from rencher.gtk.codename_dialog import RencherCodename
from rencher.renpy.config import RencherConfig
from rencher.renpy.game import Game


def return_games(self) -> list[Game]:
    config = RencherConfig()
    data_dir = config.get_data_dir()
    games_path = os.path.join(data_dir, 'games')
    dialog = RencherCodename(self)

    games: list[Game] = []
    for path in glob.iglob(os.path.join(games_path, '*')):
        try:
            games.append(Game(rpath=path))
        except GameInvalidError:
            pass  # possibly add some warning dialog that your game isn't valid
        # except NoOptionError: 
        #     dialog.change_game(path)
        #     dialog.choose(self)
        # except AttributeError:
        #     pass
        # except Exception as e:  # comment when testing so you get the full traceback
        #     logging.debug(f'{repr(e)} - Oops!')

    return games

def update_library_sidebar(self) -> None:
    games = return_games(self)

    added_games = set(games) - set(self.games)
    removed_games = set(self.games) - set(games)
    # assuming that all the projects are changed is simpler and IS NOT O(n^2) !!!!!!!!!
    # will there be false positives? yeah. i need to alter watchdog to hand out the changed projects
    changed_games = set(games) - added_games

    log = ''
    for game in removed_games:
        log += f'-{game.name} '
    for game in changed_games:
        log += f'~{game.name} '
    for game in added_games:
        log += f'+{game.name} '

    if log != '':
        logging.debug(log)

    buttons = {}
    for i, _ in enumerate(self.games):
        button = self.library_list_box.get_row_at_index(i)
        buttons[i] = button

    for button in buttons.values():
        if (button is not None
                and button.game in removed_games
                and button.get_parent() is self.library_list_box):
            self.library_list_box.remove(button)

    for game in added_games:
        button = Adw.ButtonRow(title=game.name)  # type: ignore
        button.game = game
        self.library_list_box.append(button)
        continue

    if not games:  # ps5 view
        self.library_view_stack.set_visible_child_name('empty')
        self.split_view.set_show_sidebar(False)
    else:
        if not self.library_list_box.get_selected_row():
            self.library_view_stack.set_visible_child_name('game-select')
        self.split_view.set_show_sidebar(True)

    self.games = games


