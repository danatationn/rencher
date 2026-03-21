from gi.repository import GLib, GObject

from rencher.renpy.game import Game


class GameItemDateError(Exception):
    pass

def format_date(time: float) -> str:
    date = GLib.DateTime.new_from_unix_local(int(time))
    now = GLib.DateTime.new_now_local()
    today = GLib.DateTime.new_local(
        now.get_year(), now.get_month(), now.get_day_of_month(), 0, 0, 0,
    )
    yesterday = today.add_days(-1)
    tomorrow = today.add_days(1)

    if date.to_unix() == 0:
        raise GameItemDateError()
    elif date.compare(tomorrow) >= 0:
        return date.format('In the future')
    elif date.compare(today) >= 0:
        return date.format('Today, %I:%M %p')
    elif date.compare(yesterday) >= 0:
        return date.format('Yesterday, %I:%M %p')
    else:
        return date.format('%d %b %Y, %I:%M %p')

def format_playtime(time: float) -> str:
    hours = int(time / 3600)
    minutes = int((time % 3600) / 60)
    seconds = int((time % 3600) % 60)

    formatted_playtime = f'{hours:02}:{minutes:02}:{seconds:02}'
    if formatted_playtime != '00:00:00':
        return formatted_playtime
    else:
        raise GameItemDateError()

class GameItem(GObject.Object):
    """
        used mostly for binding labels and shi

        uhh
    """
    __gtype_name__: str = 'GameItem'
    _game: Game
    name: GObject.Property = GObject.Property(type=str)
    rpath: GObject.Property = GObject.Property(type=str)
    apath: GObject.Property = GObject.Property(type=str)
    last_played: GObject.Property = GObject.Property(type=str)
    playtime: GObject.Property = GObject.Property(type=str)
    added_on: GObject.Property = GObject.Property(type=str)
    version: GObject.Property = GObject.Property(type=str)
    codename: GObject.Property = GObject.Property(type=str)

    def __init__(self, rpath: str | None = None, game: Game | None = None):
        super().__init__()

        if not rpath and not game:
            return
        if game and not rpath:
            rpath = game.rpath
        if rpath and not game:
            game = Game(rpath=rpath)

        self.game = game
        self.refresh(self.game)

    """def __getstate__(self) -> dict:
        return {
            'game': self._game,
        }

    def __setstate__(self, state: dict) -> None:
        self.__init__()
        game = state.get('_game', None)
        if not game:
            return
        if not isinstance(game, Game):
            return
        if not game.is_valid:
            return
        self.game = game"""

    def refresh(self, game: Game | None):
        if not game:
            return
        game.config.read()

        property_map: dict[str, tuple[object, list[str]]] = {
            'name': (game.get_name, []),
            'rpath': (lambda: game.rpath, []),
            'apath': (lambda: game.apath, []),
            'last_played': (game.config.get_value, ['last_played']),
            'added_on': (game.config.get_value, ['added_on']),
            'playtime': (game.config.get_value, ['playtime']),
            'version': (game.get_renpy_version, []),
            'codename': (game.get_codename, []),
        }

        for prop, (func, args) in property_map.items():
            try:
                value = func(*args)
                if prop in ['last_played', 'added_on']:
                    setattr(self, prop, format_date(value))
                elif prop == 'playtime':
                    setattr(self, prop, format_playtime(value))
                elif value:
                    setattr(self, prop, value)
                else:
                    setattr(self, prop, 'N/A')
            except Exception:
                setattr(self, prop, 'N/A')

    @property
    def game(self) -> Game:
        return self._game
    @game.setter
    def game(self, value: Game):
        self._game = value
        self.refresh(value)
