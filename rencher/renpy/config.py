import os
import sys
from collections.abc import Mapping
from configparser import ConfigParser
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path
from types import UnionType
from typing import TYPE_CHECKING, cast, get_type_hints

if TYPE_CHECKING:
    from _typeshed import DataclassInstance

from rencher.renpy.paths import config_path, local_path

type IniValue = str | float | int | bool | None

def _parse(raw: str, type: type | UnionType, default: IniValue) -> IniValue:
    """converts the ini's string to the correct type expected by the config"""
    raw = raw.strip()
    try:
        if type is bool:
            return ConfigParser.BOOLEAN_STATES[raw.lower()]
        if type == bool | None:
            return None if raw == '' else ConfigParser.BOOLEAN_STATES[raw.lower()]
        if type is float:
            return float(raw)
        if type is int:
            return int(raw)
        return raw
    except (KeyError, ValueError):
        return default

def _format(value: IniValue) -> str:
    """converts the value to a string"""
    if value is None:
        return ''
    if isinstance(value, bool):
        return 'true' if value else 'false'
    return str(value)

def _fill_section(parser: ConfigParser, section: str, object: 'DataclassInstance') -> None:
    if not parser.has_section(section):
        return

    hints: dict[str, type | UnionType] = get_type_hints(type(object))

    for f in fields(object):
        raw = parser[section].get(f.name)
        if raw is not None:
            current = cast(IniValue, getattr(object, f.name))
            setattr(object, f.name, _parse(raw, hints[f.name], current))

def _read_ini(config_path: Path) -> ConfigParser:
    parser = ConfigParser(interpolation=None)
    parser.read(config_path, encoding='utf-8')
    return parser

def _write_ini(config_path: Path, sections: Mapping[str, 'DataclassInstance']) -> None:
    """this can raise OSError"""
    parser = ConfigParser(interpolation=None)
    for name, object in sections.items():
        values: dict[str, IniValue] = asdict(object)
        parser[name] = {key: _format(value) for key, value in values.items()}

    config_path.parent.mkdir(parents=True, exist_ok=True)

    tmp_path = config_path.with_name(config_path.name + '.tmp')
    with open(tmp_path, 'w', encoding='utf-8') as f:
        parser.write(f)
    os.replace(tmp_path, config_path)

@dataclass
class RencherConfig:
    data_dir: str = ''
    suppress_updates: bool = False
    delete_on_import: bool = False
    skip_splash_scr: bool = False
    skip_main_menu: bool = False
    forced_save_dir: bool = False
    discord_rpc: bool = False
    windowficate_filenames: bool = True
    reduce_motion: bool = sys.platform == 'win32'
    disable_hidpi: bool = False

    def __post_init__(self) -> None:
        self.refresh()

    @property
    def data_path(self) -> Path:
        return Path(self.data_dir) if self.data_dir else local_path

    def refresh(self) -> None:
        _fill_section(_read_ini(config_path), 'settings', self)

    def save(self) -> None:
        _write_ini(config_path, {'settings': self})

_settings: RencherConfig | None = None
def get_rencher_settings() -> RencherConfig:
    """call this instead of making new instances for stupid stuff"""
    global _settings
    if _settings is None:
        _settings = RencherConfig()
    return _settings

@dataclass
class GameInfo:
    nickname: str = ''
    last_played: float = 0.0
    playtime: float = 0.0
    added_on: float = 0.0
    codename: str = ''
    # TODO is_mod: bool = False,

@dataclass
class GameOptions:
    skip_splash_scr: bool | None = None
    skip_main_menu: bool | None = None
    forced_save_dir: bool | None = None
    discord_rpc: bool | None = None
    # save_slot: int = 1

@dataclass
class GameConfig:
    path: Path
    info: GameInfo = field(init=False, default_factory=GameInfo)
    options: GameOptions = field(init=False, default_factory=GameOptions)

    def __post_init__(self) -> None:
        self.refresh()

    def save(self) -> None:
        _write_ini(self.path, {'info': self.info, 'options': self.options})

    def refresh(self) -> None:
        parser = _read_ini(self.path)
        _fill_section(parser, 'info', self.info)
        _fill_section(parser, 'options', self.options)

    def effective(self) -> GameOptions:
        """meant to be read-only! do not assign this to self.options"""
        settings = get_rencher_settings()
        options = GameOptions()
        for f in fields(GameOptions):
            override = cast(IniValue, getattr(self.options, f.name))
            default = cast(IniValue, getattr(settings, f.name))
            setattr(options, f.name, default if override is None else override)
        return options
